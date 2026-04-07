"""
7주차: FastAPI 백엔드 - Function Calling 기반 AI Agent

[6주차 대비 변경 사항]
  - RAG 파이프라인 직접 호출 → AI Agent (Function Calling) 으로 대체
  - LLM이 직접 도구 선택 → 지능형 라우팅
  - 자가 보정 검색 (search_and_validate) 지원
  - SSE로 도구 실행 과정 실시간 전송
"""
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

_BACKEND = os.path.dirname(__file__)
sys.path.insert(0, _BACKEND)

from agent import PolicyAgent

# ── 앱 초기화 ─────────────────────────────────────────────────
app = FastAPI(title="청년도우미 AI Agent API v3")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 간단한 로컬 세션 저장소 ───────────────────────────────────
SESSIONS_FILE = os.path.join(_BACKEND, "sessions.json")


def _load_sessions() -> dict:
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_sessions(data: dict):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _new_session(name: str = "새 대화") -> dict:
    return {
        "id":           uuid.uuid4().hex[:8],
        "name":         name,
        "messages":     [],
        "conversation": [],
        "created_at":   datetime.now().isoformat(),
    }


# ── 에이전트 인스턴스 풀 (세션별 격리) ───────────────────────
_agents: dict[str, PolicyAgent] = {}


def get_agent(session_id: str) -> PolicyAgent:
    if session_id not in _agents:
        _agents[session_id] = PolicyAgent()
        sessions = _load_sessions()
        s = sessions.get(session_id)
        if s and s.get("conversation"):
            _agents[session_id].conversation = list(s["conversation"])
    return _agents[session_id]


# ── 요청 모델 ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str
    message:    str


class RenameRequest(BaseModel):
    name: str


# ════════════════════════════════════════════════════════════════
# 세션 API
# ════════════════════════════════════════════════════════════════

@app.get("/sessions")
def list_sessions():
    sessions = _load_sessions()
    return sorted(sessions.values(), key=lambda s: s["created_at"], reverse=True)


@app.post("/sessions")
def create_session():
    sessions = _load_sessions()
    s = _new_session()
    sessions[s["id"]] = s
    _save_sessions(sessions)
    return s


@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    s = _load_sessions().get(session_id)
    if not s:
        raise HTTPException(404, "세션 없음")
    return s


@app.patch("/sessions/{session_id}")
def rename_session(session_id: str, body: RenameRequest):
    sessions = _load_sessions()
    if session_id not in sessions:
        raise HTTPException(404, "세션 없음")
    sessions[session_id]["name"] = body.name
    _save_sessions(sessions)
    return sessions[session_id]


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    sessions = _load_sessions()
    sessions.pop(session_id, None)
    _save_sessions(sessions)
    _agents.pop(session_id, None)
    return {"ok": True}


# ════════════════════════════════════════════════════════════════
# 챗봇 API (SSE 스트리밍)
# ════════════════════════════════════════════════════════════════

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    sessions = _load_sessions()
    session  = sessions.get(req.session_id)
    if not session:
        raise HTTPException(404, "세션 없음")

    agent = get_agent(req.session_id)

    async def generate():
        full_response = ""
        hits          = []
        tool_calls    = []

        for event in agent.chat_stream(req.message):
            etype = event["type"]

            if etype == "text":
                full_response += event["content"]
            elif etype == "hits":
                hits = event["hits"]
            elif etype == "tool_calls":
                tool_calls = event["calls"]

            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0)

        # ── 세션 저장 ─────────────────────────────────────────
        sessions2 = _load_sessions()
        s2 = sessions2.get(req.session_id)
        if not s2:
            return

        # 첫 질문으로 세션 이름 자동 설정
        if not any(m["role"] == "user" for m in s2["messages"]):
            words = req.message.replace("?", "").strip()
            s2["name"] = words[:20] + ("…" if len(words) > 20 else "")

        s2["messages"] = s2["messages"] + [
            {"role": "user",      "content": req.message,    "hits": [],  "tool_calls": []},
            {"role": "assistant", "content": full_response,  "hits": hits, "tool_calls": tool_calls},
        ]
        s2["conversation"] = agent.conversation
        sessions2[req.session_id] = s2
        _save_sessions(sessions2)

    return StreamingResponse(generate(), media_type="text/event-stream")


# ════════════════════════════════════════════════════════════════
# 문서·통계 API
# ════════════════════════════════════════════════════════════════

@app.get("/sources")
def get_sources():
    from tools import get_store
    try:
        return get_store().get_sources()
    except Exception:
        return []


@app.get("/health")
def health():
    return {"status": "ok"}
