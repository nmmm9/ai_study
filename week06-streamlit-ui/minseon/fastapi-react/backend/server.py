"""
6주차: FastAPI 백엔드 (실서비스용)

[5주차 대비 추가된 기능]
  1. 세션 관리 API: 생성·조회·삭제·이름변경
  2. 세션별 대화 격리: session_id로 RAG 인스턴스 분리
  3. 세션 영속: SessionManager로 sessions.json 저장
  4. 비용 조회 API: 세션별·전체 누적 비용
"""

import os
import sys
import json
import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ── 경로 설정 ──────────────────────────────────────────────────
_BACKEND = os.path.dirname(__file__)
_ROOT    = os.path.join(_BACKEND, "..", "..")
sys.path.insert(0, _ROOT)

from rag_pipeline import AdvancedRagPipeline
from session_manager import SessionManager

# ── 초기화 ────────────────────────────────────────────────────
app = FastAPI(title="청년도우미 Advanced RAG API v2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS_PATH = os.path.join(_ROOT, "data", "sessions.json")
sm  = SessionManager(SESSIONS_PATH)

# 세션별 RAG 인스턴스 (session_id → AdvancedRagPipeline)
_rag_instances: dict[str, AdvancedRagPipeline] = {}

# 공유 RAG (인덱싱·검색용 - 벡터DB는 공유)
_shared_rag = AdvancedRagPipeline()

# 자동 인덱싱
_shared_rag.auto_index_data_dir()


def get_rag(session_id: str) -> AdvancedRagPipeline:
    """세션별 독립 RAG 인스턴스 반환 (벡터DB는 공유)"""
    if session_id not in _rag_instances:
        _rag_instances[session_id] = AdvancedRagPipeline()
        # 기존 세션 대화 복원
        session = sm.get(session_id)
        if session:
            _rag_instances[session_id].conversation = list(session["conversation"])
    return _rag_instances[session_id]


# ════════════════════════════════════════════════════════════════
# 요청/응답 모델
# ════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    session_id:      str
    message:         str
    top_k:           int   = 5
    threshold:       float = 0.2
    max_per_source:  int   = 2
    use_compression: bool  = True


class SessionRenameRequest(BaseModel):
    name: str


class IndexRequest(BaseModel):
    file_path:   str
    source_name: Optional[str] = None


# ════════════════════════════════════════════════════════════════
# 세션 API
# ════════════════════════════════════════════════════════════════

@app.get("/sessions")
def list_sessions():
    return sm.list()


@app.post("/sessions")
def create_session():
    sid = sm.create()
    return sm.get(sid)


@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    session = sm.get(session_id)
    if not session:
        raise HTTPException(404, "세션 없음")
    return session


@app.patch("/sessions/{session_id}")
def rename_session(session_id: str, body: SessionRenameRequest):
    sm.rename(session_id, body.name)
    return sm.get(session_id)


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    sm.delete(session_id)
    if session_id in _rag_instances:
        del _rag_instances[session_id]
    return {"ok": True}


@app.get("/sessions/{session_id}/cost")
def session_cost(session_id: str):
    session = sm.get(session_id)
    if not session:
        raise HTTPException(404, "세션 없음")
    return {
        "total_cost_usd": session["total_cost_usd"],
        "total_cost_krw": session["total_cost_usd"] * 1380,
        "total_tokens":   session["total_tokens"],
    }


@app.get("/cost/total")
def total_cost():
    sessions  = sm.list()
    total_usd = sum(s["total_cost_usd"] for s in sessions)
    total_in  = sum(s["total_tokens"]["input"] for s in sessions)
    total_out = sum(s["total_tokens"]["output"] for s in sessions)
    return {
        "total_cost_usd": total_usd,
        "total_cost_krw": total_usd * 1380,
        "total_input_tokens":  total_in,
        "total_output_tokens": total_out,
        "session_count": len(sessions),
    }


# ════════════════════════════════════════════════════════════════
# 챗봇 API
# ════════════════════════════════════════════════════════════════

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    session = sm.get(req.session_id)
    if not session:
        raise HTTPException(404, "세션 없음")

    rag = get_rag(req.session_id)

    async def stream_generator():
        # ── Pre-retrieval ──────────────────────────────────────
        from services.cost_tracker import CostTracker
        tracker = CostTracker()

        tracker.start_stage("pre")
        queries = rag._generate_queries(req.message, tracker)
        tracker.end_stage("pre")
        rag._last_queries = queries

        yield f"data: {json.dumps({'type':'pipeline','stage':'pre','queries':queries,'query_type':rag._last_query_type})}\n\n"
        await asyncio.sleep(0)

        # ── Retrieval ──────────────────────────────────────────
        tracker.start_stage("retrieval")
        candidates = rag._hybrid_search_all(
            queries, req.top_k, req.threshold, req.max_per_source, tracker
        )
        tracker.end_stage("retrieval")
        rag._last_candidates = candidates

        yield f"data: {json.dumps({'type':'pipeline','stage':'retrieval','count':len(candidates),'queries_used':len(queries)})}\n\n"
        await asyncio.sleep(0)

        # ── Post-retrieval ─────────────────────────────────────
        tracker.start_stage("post")
        final_hits = rag._post_process(
            req.message, candidates, req.top_k, req.use_compression, tracker
        )
        tracker.end_stage("post")

        yield f"data: {json.dumps({'type':'pipeline','stage':'post','reranked':len(rag._last_hits),'compressed':len([h for h in final_hits if h.get('compressed')])})}\n\n"
        await asyncio.sleep(0)

        # ── Generation ─────────────────────────────────────────
        tracker.start_stage("generation")
        system_content = rag._build_system_prompt(final_hits)

        from services.llm_service import stream_response
        for chunk in stream_response(system_content, rag.conversation, req.message, tracker=tracker):
            yield f"data: {json.dumps({'type':'text','content':chunk})}\n\n"
            await asyncio.sleep(0)
        tracker.end_stage("generation")

        # ── 결과 전송 ──────────────────────────────────────────
        usage = getattr(stream_response, "_last_usage", {"input": 0, "output": 0})
        rag._last_usage = usage
        cost_summary = tracker.get_summary()
        rag._last_cost_summary = cost_summary

        # 세션 업데이트
        if len([m for m in session["messages"] if m["role"] == "user"]) == 0:
            words = req.message.replace("?", "").strip()
            sm.rename(req.session_id, words[:20] + ("…" if len(words) > 20 else ""))

        hits_data = [
            {
                "source":     h["metadata"]["source"],
                "content":    h["content"],
                "similarity": h["similarity"],
                "compressed": h.get("compressed", False),
            }
            for h in final_hits
        ]

        sm.add_cost(req.session_id, cost_summary.get("total_cost_usd", 0), usage)
        sm.save_messages(
            req.session_id,
            session["messages"] + [
                {"role": "user",      "content": req.message},
                {"role": "assistant", "content": ""},
            ],
            rag.conversation,
        )

        yield f"data: {json.dumps({'type':'hits','hits':hits_data})}\n\n"
        yield f"data: {json.dumps({'type':'cost',**cost_summary})}\n\n"
        yield f"data: {json.dumps({'type':'usage','input':usage['input'],'output':usage['output']})}\n\n"
        yield f"data: {json.dumps({'type':'done'})}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


# ════════════════════════════════════════════════════════════════
# 문서 관리 API
# ════════════════════════════════════════════════════════════════

@app.get("/sources")
def get_sources():
    return _shared_rag.get_indexed_sources()


@app.delete("/sources/{source_name}")
def delete_source(source_name: str):
    ok = _shared_rag.delete_source(source_name)
    return {"ok": ok}


@app.get("/stats")
def get_stats():
    return _shared_rag.get_stats()


@app.get("/health")
def health():
    return {"status": "ok"}
