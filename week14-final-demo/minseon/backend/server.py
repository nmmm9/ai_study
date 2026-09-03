"""
server.py — FastAPI 서버 (BACKEND 계층)

실행: uvicorn backend.server:app --reload --port 8000
"""

import asyncio
import json

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.config import settings  # noqa: F401  (.env를 여기서 한 번 로드)
from backend.logging_config import get_logger
from backend.auth import get_current_user, get_current_user_email, require_self
from backend.graph import graph, run_retrieval
from backend.agents.generate_node import stream_answer
from backend.scheduler import init_scheduler, notify_matching_users
from frontend.session_manager import (
    sign_in, sign_up, sign_out,
    new_session, get_all, save_session, rename_session, delete_session,
    _get_client,
)

logger = get_logger(__name__)

# 업로드 허용 파일 (OCR)
_OCR_MAX_BYTES     = 10 * 1024 * 1024  # 10MB
_OCR_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}

# ── Lifespan (스케줄러) ───────────────────────────────────────────

@asynccontextmanager
async def lifespan(_: FastAPI):
    sch = init_scheduler()
    sch.start()
    logger.info("[server] 스케줄러 시작 (매일 오전 9시 알림)")
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

class HistoryTurn(BaseModel):
    role:    str  # "user" | "bot"
    content: str

class ChatRequest(BaseModel):
    message:           str
    session_id:        str = ""
    email:             str = ""
    age:               int = 0
    region:            str = ""
    employment_status: str = ""
    annual_income:     int = 0
    history:            list[HistoryTurn] = []

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

def _build_user_profile(request: ChatRequest) -> dict:
    """요청에서 사용자 프로필 딕셔너리 생성 (빈 값 제외)."""
    profile = {}
    if request.email:             profile["email"]             = request.email
    if request.age:               profile["age"]               = request.age
    if request.region:            profile["region"]            = request.region
    if request.employment_status: profile["employment_status"] = request.employment_status
    if request.annual_income:     profile["annual_income"]     = request.annual_income
    return profile


def _build_conversation_history(history: list[HistoryTurn]) -> list[dict]:
    """프론트에서 보낸 대화 이력을 OpenAI 메시지 형식으로 변환 (최근 10턴만 사용)."""
    role_map = {"user": "user", "bot": "assistant"}
    turns = [
        {"role": role_map.get(h.role, "user"), "content": h.content}
        for h in history if h.content.strip()
    ]
    return turns[-10:]


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """논스트리밍 채팅 — 전체 답변을 한 번에 반환."""
    user_profile = _build_user_profile(request)
    conversation_history = _build_conversation_history(request.history)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: graph.invoke({
        "question":            request.message,
        "retry_count":         0,
        "execution_trace":     [],
        "user_profile":        user_profile,
        "conversation_history": conversation_history,
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
    user_profile = _build_user_profile(request)
    conversation_history = _build_conversation_history(request.history)

    async def generate():
        # 1. 검색·도구 선택 단계 실행 (동기 → 스레드풀)
        loop = asyncio.get_event_loop()
        state = await loop.run_in_executor(None, lambda: run_retrieval(
            request.message, user_profile=user_profile, conversation_history=conversation_history
        ))

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


# ── Sessions (로그인 필요 — 세션은 본인 계정에만 저장/조회) ────────

@app.get("/api/sessions")
async def get_sessions(current=Depends(get_current_user)):
    return get_all(current.token)


@app.post("/api/sessions")
async def create_session(current=Depends(get_current_user)):
    sid = new_session(current.user_id, current.token)
    return {"session_id": sid}


@app.put("/api/sessions/{session_id}")
async def update_session(session_id: str, request: SessionSaveRequest, current=Depends(get_current_user)):
    save_session(current.token, session_id, request.messages, request.traces)
    return {"success": True}


@app.patch("/api/sessions/{session_id}/rename")
async def rename_session_endpoint(session_id: str, request: SessionRenameRequest, current=Depends(get_current_user)):
    rename_session(current.token, session_id, request.name)
    return {"success": True}


@app.delete("/api/sessions/{session_id}")
async def delete_session_endpoint(session_id: str, current=Depends(get_current_user)):
    delete_session(current.token, session_id)
    return {"success": True}


# ── Profile ───────────────────────────────────────────────────────

@app.post("/api/profiles")
async def save_profile(request: ProfileRequest, current_email: str = Depends(get_current_user_email)):
    """로그인한 사용자의 프로필(나이/지역)을 Supabase에 저장."""
    require_self(current_email, request.email)
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
async def get_profile(email: str, current_email: str = Depends(get_current_user_email)):
    """이메일로 프로필 조회."""
    require_self(current_email, email)
    try:
        res = _get_client().table("user_profiles").select("*").eq("email", email).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Notify ────────────────────────────────────────────────────────

@app.post("/api/notify/test")
async def notify_test():
    await notify_matching_users()
    return {"success": True, "message": "알림 발송 완료"}


# ── OCR (Feature 6) ───────────────────────────────────────────────

@app.post("/api/ocr")
async def ocr_analyze(file: UploadFile = File(...)):
    """이미지/PDF 업로드 → GPT-4o Vision으로 정책 정보 추출."""
    if file.content_type not in _OCR_ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="이미지(JPEG/PNG/WEBP) 또는 PDF 파일만 업로드할 수 있습니다.")

    contents = await file.read()
    if len(contents) > _OCR_MAX_BYTES:
        raise HTTPException(status_code=400, detail="파일 크기는 10MB를 초과할 수 없습니다.")

    try:
        from backend.tools.ocr_tool import analyze_file
        result = analyze_file(contents, file.filename or "upload.jpg")
        return {"success": True, "result": result, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 키워드 구독 (Feature 1) ───────────────────────────────────────

class SubscriptionRequest(BaseModel):
    email:   str
    keyword: str

@app.get("/api/subscriptions/{email}")
async def get_subscriptions(email: str, current_email: str = Depends(get_current_user_email)):
    require_self(current_email, email)
    from backend.db.subscription_db import get_subscriptions
    return {"keywords": get_subscriptions(email)}

@app.post("/api/subscriptions")
async def add_subscription(req: SubscriptionRequest, current_email: str = Depends(get_current_user_email)):
    require_self(current_email, req.email)
    from backend.db.subscription_db import add_subscription
    ok = add_subscription(req.email, req.keyword)
    return {"success": ok}

@app.delete("/api/subscriptions")
async def remove_subscription(req: SubscriptionRequest, current_email: str = Depends(get_current_user_email)):
    require_self(current_email, req.email)
    from backend.db.subscription_db import remove_subscription
    ok = remove_subscription(req.email, req.keyword)
    return {"success": ok}


# ── 지원 현황 트래킹 (Feature 3) ─────────────────────────────────

class ApplicationRequest(BaseModel):
    email:       str
    policy_name: str
    policy_id:   str = ""
    deadline:    str = ""

class ApplicationStatusRequest(BaseModel):
    app_id: int
    status: str
    memo:   str = ""

@app.get("/api/applications/{email}")
async def get_applications(email: str, current_email: str = Depends(get_current_user_email)):
    require_self(current_email, email)
    from backend.db.subscription_db import get_applications
    return {"applications": get_applications(email)}

@app.post("/api/applications")
async def add_application(req: ApplicationRequest, current_email: str = Depends(get_current_user_email)):
    require_self(current_email, req.email)
    from backend.db.subscription_db import add_application
    app_id = add_application(req.email, req.policy_name, req.policy_id, req.deadline)
    return {"success": True, "app_id": app_id}

@app.patch("/api/applications/status")
async def update_application_status(req: ApplicationStatusRequest, current_email: str = Depends(get_current_user_email)):
    from backend.db.subscription_db import get_application_owner, update_status
    owner = get_application_owner(req.app_id)
    if owner is None:
        raise HTTPException(status_code=404, detail="지원 현황을 찾을 수 없습니다.")
    require_self(current_email, owner)
    ok = update_status(req.app_id, req.status, req.memo)
    return {"success": ok}


# ── 협업 필터링 추천 (Feature 7) ──────────────────────────────────

@app.get("/api/recommendations/{session_id}")
async def get_recommendations(session_id: str, category: str = ""):
    from backend.db.behavior_db import get_collab_recommendations, get_popular_by_category
    names = get_collab_recommendations(session_id, top_k=5)
    if not names:
        names = get_popular_by_category(category=category, top_k=5)
    return {"recommendations": names}
