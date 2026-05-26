from dotenv import load_dotenv

load_dotenv()

import json
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Trigger tool registration
import tools  # noqa: F401

from tools.registry import list_tool_names
from tools import TOOL_DOMAINS, DOMAINS
from services.graph import agent_stream, graph_metadata
from services.memory import (
    list_threads, get_history, delete_thread, get_thread_summary,
)
from services.document_store import collection_stats, delete_document
from services.ingestion import ingest_file, ingest_text
from config import SUPERVISOR_MODEL, DOMAIN_MODEL, WRITER_MODEL

SUPPORTED_EXTS = {".pdf", ".txt", ".md", ".markdown"}
MAX_FILE_BYTES = 20 * 1024 * 1024   # 20 MB

app = FastAPI(title="K-Agent LangGraph Multi-Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str
    model: str = "auto"  # "auto" → tiered routing per stage; otherwise overrides all stages
    history: list[dict] = []
    thread_id: str | None = None  # When set, conversation memory is loaded/saved server-side


@app.get("/api/tools")
async def get_tools():
    names = list_tool_names()
    by_domain = {d: [n for n in names if TOOL_DOMAINS.get(n) == d] for d in DOMAINS}
    return {
        "tools": names,
        "count": len(names),
        "domains": by_domain,
    }


@app.get("/api/models")
async def get_models():
    """Expose the per-stage model routing config."""
    return {
        "supervisor": SUPERVISOR_MODEL,
        "domain": DOMAIN_MODEL,
        "writer": WRITER_MODEL,
    }


@app.get("/api/graph")
async def get_graph():
    """Static graph metadata for frontend visualization."""
    return graph_metadata()


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE — multi-agent graph execution with node/edge/token events.

    When thread_id is provided, conversation history is loaded/saved
    server-side via the LangGraph checkpointer (services/memory.py).
    """
    async def event_generator():
        async for event_type, data in agent_stream(
            req.question, req.model, req.history, req.thread_id,
        ):
            yield f"data: {json.dumps({'type': event_type, 'data': data}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/sessions")
async def list_sessions():
    """List all conversation threads (newest first)."""
    return {"sessions": list_threads()}


@app.get("/api/sessions/{thread_id}")
async def get_session(thread_id: str):
    """Retrieve full conversation history for a thread."""
    summary = get_thread_summary(thread_id)
    if not summary:
        return {"thread_id": thread_id, "messages": [], "exists": False}
    return {
        "thread_id": thread_id,
        "title": summary["title"],
        "messages": get_history(thread_id, limit=200),
        "exists": True,
    }


@app.delete("/api/sessions/{thread_id}")
async def delete_session(thread_id: str):
    removed = delete_thread(thread_id)
    return {"removed": removed}


# ── Agentic RAG endpoints (week 12) ─────────────────────────────

class TextIngestRequest(BaseModel):
    text: str
    doc_name: str


@app.get("/api/documents")
async def list_docs():
    """List all uploaded documents and their chunk counts."""
    return collection_stats()


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF / TXT / MD file. Chunks + embeds + indexes."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in SUPPORTED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"지원 형식: {', '.join(SUPPORTED_EXTS)} (받은: {ext})",
        )

    body = await file.read()
    if len(body) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"파일이 너무 큽니다 ({len(body) // 1024} KB > {MAX_FILE_BYTES // 1024} KB)",
        )

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(body)
        tmp_path = tmp.name

    try:
        result = await ingest_file(tmp_path, doc_name=file.filename)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return result


@app.post("/api/documents/text")
async def upload_text(req: TextIngestRequest):
    """Ingest raw text — useful for quick testing without a file."""
    return await ingest_text(req.text, req.doc_name)


@app.delete("/api/documents/{doc_id}")
async def remove_document(doc_id: str):
    """Delete all chunks for a document."""
    n = delete_document(doc_id)
    return {"removed_chunks": n}
