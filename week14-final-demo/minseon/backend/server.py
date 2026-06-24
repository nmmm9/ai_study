"""
server.py — FastAPI 서버 (BACKEND 계층)

실행: uvicorn backend.server:app --reload --port 8000
"""

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.graph import graph, run_retrieval
from backend.agents.generate_node import stream_answer
from backend.scheduler import init_scheduler, notify_matching_users
from frontend.session_manager import (
    sign_in, sign_up, sign_out,
    new_session, get_all, save_session, rename_session, delete_session,
    _get_client,
)

# ── Lifespan (스케줄러) ───────────────────────────────────────────

@asynccontextmanager
async def lifespan(_: FastAPI):
    sch = init_scheduler()
    sch.start()
    print("[server] 스케줄러 시작 (매일 오전 9시 알림)")
    yield
    sch.shutdown()


app = FastAPI(title="청년정책 AI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Models ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str = ""

class AuthRequest(BaseModel):
    email: str
    password: str

class SessionSaveRequest(BaseModel):
    messages: list
    traces: list = []

class SessionRenameRequest(BaseModel):
    name: str

class ProfileRequest(BaseModel):
    email: str
    age: int = 0
    region: str = ""
    employment_status: str = ""
    annual_income: int = 0
    notify: bool = True


# ── Health ────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ── Chat ──────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """논스트리밍 채팅 — 전체 답변을 한 번에 반환."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: graph.invoke({
        "question":        request.message,
        "retry_count":     0,
        "execution_trace": [],
    }))
    return {
        "answer":    result.get("answer", ""),
        "tool_name": result.get("tool_name", ""),
    }


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE 스트리밍 채팅 — 청크 단위로 실시간 전송.

    클라이언트 수신 형식:
      data: {"type": "meta",  "tool": "search_policies"}
      data: {"type": "chunk", "content": "안녕하세요"}
      data: {"type": "done"}
    """
    async def generate():
        # 1. 검색·도구 선택 단계 실행 (동기 → 스레드풀)
        loop = asyncio.get_event_loop()
        state = await loop.run_in_executor(None, lambda: run_retrieval(request.message))

        # 2. 도구 메타데이터 먼저 전송
        yield f"data: {json.dumps({'type': 'meta', 'tool': state.get('tool_name', '')}, ensure_ascii=False)}\n\n"

        # 3. GPT 답변 스트리밍
        async for chunk in stream_answer(state):
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Auth ──────────────────────────────────────────────────────────

@app.post("/api/auth/signup")
async def auth_signup(request: AuthRequest):
    try:
        result = sign_up(request.email, request.password)
        return {"success": True, "message": "회원가입 완료. 이메일 인증 후 로그인하세요."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login")
async def auth_login(request: AuthRequest):
    try:
        result  = sign_in(request.email, request.password)
        session = result.get("session")
        user    = result.get("user")
        return {
            "success":      True,
            "access_token": session.access_token if session else "",
            "email":        user.email if user else "",
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/auth/logout")
async def auth_logout():
    sign_out()
    return {"success": True}


# ── Sessions ──────────────────────────────────────────────────────

@app.get("/api/sessions")
async def get_sessions():
    return get_all()


@app.post("/api/sessions")
async def create_session():
    sid = new_session()
    return {"session_id": sid}


@app.put("/api/sessions/{session_id}")
async def update_session(session_id: str, request: SessionSaveRequest):
    save_session(session_id, request.messages, request.traces)
    return {"success": True}


@app.patch("/api/sessions/{session_id}/rename")
async def rename_session_endpoint(session_id: str, request: SessionRenameRequest):
    rename_session(session_id, request.name)
    return {"success": True}


@app.delete("/api/sessions/{session_id}")
async def delete_session_endpoint(session_id: str):
    delete_session(session_id)
    return {"success": True}


# ── Profile ───────────────────────────────────────────────────────

@app.post("/api/profiles")
async def save_profile(request: ProfileRequest):
    """로그인한 사용자의 프로필(나이/지역)을 Supabase에 저장."""
    try:
        _get_client().table("user_profiles").upsert({
            "email":             request.email,
            "age":               request.age or None,
            "region":            request.region or None,
            "employment_status": request.employment_status or None,
            "annual_income":     request.annual_income or None,
            "notify":            request.notify,
        }).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/profiles/{email}")
async def get_profile(email: str):
    """이메일로 프로필 조회."""
    try:
        res = _get_client().table("user_profiles").select("*").eq("email", email).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Notify ────────────────────────────────────────────────────────

@app.post("/api/notify/test")
async def notify_test():
    """수동으로 알림 발송 테스트 (스케줄 기다리지 않고 즉시 실행)."""
    await notify_matching_users()
    return {"success": True, "message": "알림 발송 완료"}
