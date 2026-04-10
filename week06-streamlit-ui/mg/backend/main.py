from dotenv import load_dotenv

load_dotenv()

import hashlib
import json

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import tiktoken

from models.schemas import (
    SamplesResponse, SampleInfo, SampleDetailResponse,
    EmbedRequest, EmbedResponse,
    CollectionsResponse, CollectionItem,
    ChatRequest, ChatResponse, SourceChunk,
)
from services.chunking_service import chunk_text
from services.embedding_service import embed_texts
from services.llm_service import PRICING
from services import vector_store
from services.agentic_rag import agentic_rag_stream
from services.message_router import is_trivial
from services.llm_service import stream_with_context as stream_direct
from data.samples import SAMPLES

app = FastAPI(title="RAG Chatbot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_COLLECTION = "startup-guide-500-50"


@app.on_event("startup")
async def startup_init():
    """서버 시작 시 스타트업 문서 자동 임베딩."""
    if vector_store.collection_exists(DEFAULT_COLLECTION):
        return
    for s in SAMPLES:
        if s["id"] == "startup-guide":
            chunks = chunk_text(s["content"], 500, 50)
            texts = [c.text for c in chunks]
            embeddings, _ = await embed_texts(texts)
            metadatas = [{"index": c.index} for c in chunks]
            vector_store.add_chunks(DEFAULT_COLLECTION, texts, embeddings, metadatas)
            break

_enc = tiktoken.encoding_for_model("gpt-4o-mini")


def count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def make_collection_name(document: str, chunk_size: int, overlap: int) -> str:
    for s in SAMPLES:
        if s["content"] == document:
            return f"{s['id']}-{chunk_size}-{overlap}"
    h = hashlib.md5(document.encode()).hexdigest()[:8]
    return f"custom-{h}-{chunk_size}-{overlap}"


# ─── Default ───


@app.get("/api/default")
async def get_default():
    """기본 스타트업 문서 컬렉션 정보."""
    if vector_store.collection_exists(DEFAULT_COLLECTION):
        col = vector_store.create_collection(DEFAULT_COLLECTION)
        return {"collection_name": DEFAULT_COLLECTION, "chunk_count": col.count(), "title": "스타트업 창업 가이드"}
    return {"collection_name": None, "chunk_count": 0, "title": None}


# ─── Samples ───


@app.get("/api/samples", response_model=SamplesResponse)
async def get_samples():
    return SamplesResponse(
        samples=[
            SampleInfo(id=s["id"], title=s["title"], length=len(s["content"]))
            for s in SAMPLES
        ]
    )


@app.get("/api/samples/{sample_id}", response_model=SampleDetailResponse)
async def get_sample(sample_id: str):
    for s in SAMPLES:
        if s["id"] == sample_id:
            return SampleDetailResponse(id=s["id"], title=s["title"], content=s["content"])
    raise HTTPException(404, f"Sample '{sample_id}' not found")


# ─── Embed ───


@app.post("/api/embed", response_model=EmbedResponse)
async def embed_document(req: EmbedRequest):
    col_name = make_collection_name(req.document, req.chunk_size, req.chunk_overlap)

    if vector_store.collection_exists(col_name):
        col = vector_store.create_collection(col_name)
        return EmbedResponse(collection_name=col_name, chunk_count=col.count())

    chunks = chunk_text(req.document, req.chunk_size, req.chunk_overlap)
    texts = [c.text for c in chunks]
    embeddings, _ = await embed_texts(texts)
    metadatas = [{"index": c.index} for c in chunks]
    vector_store.add_chunks(col_name, texts, embeddings, metadatas)

    return EmbedResponse(collection_name=col_name, chunk_count=len(texts))


# ─── File Upload ───


@app.post("/api/upload", response_model=EmbedResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a file (.txt, .md, .pdf) and embed it."""
    if not file.filename:
        raise HTTPException(400, "파일 이름이 없습니다")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("txt", "md", "pdf", "csv"):
        raise HTTPException(400, f"지원하지 않는 파일 형식: .{ext} (txt, md, pdf, csv만 가능)")

    raw = await file.read()

    # Extract text based on file type
    if ext == "pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=raw, filetype="pdf")
            text = "\n\n".join(page.get_text() for page in doc)
            doc.close()
        except ImportError:
            # Fallback: try to decode as text
            text = raw.decode("utf-8", errors="ignore")
    else:
        text = raw.decode("utf-8", errors="ignore")

    if len(text.strip()) < 50:
        raise HTTPException(400, "파일 내용이 너무 짧습니다 (최소 50자)")

    # Create collection name from filename
    name_part = file.filename.rsplit(".", 1)[0][:20]
    h = hashlib.md5(text.encode()).hexdigest()[:6]
    col_name = f"file-{name_part}-{h}"

    if vector_store.collection_exists(col_name):
        col = vector_store.create_collection(col_name)
        return EmbedResponse(collection_name=col_name, chunk_count=col.count())

    chunks = chunk_text(text, 500, 50)
    texts = [c.text for c in chunks]
    embeddings, _ = await embed_texts(texts)
    metadatas = [{"index": c.index, "source": file.filename} for c in chunks]
    vector_store.add_chunks(col_name, texts, embeddings, metadatas)

    return EmbedResponse(collection_name=col_name, chunk_count=len(texts))


# ─── Collections ───


@app.get("/api/collections", response_model=CollectionsResponse)
async def get_collections():
    cols = vector_store.list_collections()
    return CollectionsResponse(
        collections=[CollectionItem(name=c["name"], count=c["count"]) for c in cols]
    )


@app.delete("/api/collections/{name}")
async def delete_collection(name: str):
    try:
        vector_store.delete_collection(name)
        return {"deleted": name}
    except Exception:
        raise HTTPException(404, f"Collection '{name}' not found")


# ─── Chat (SSE Streaming) ───


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE streaming chat.

    Routing:
    - Tier 1: obvious greetings → direct LLM (no search at all)
    - Tier 2: everything else → embed + probe similarity → decide RAG or direct
    """
    async def event_generator():
        if is_trivial(req.question):
            # Tier 1: obvious greeting → skip search entirely
            history = req.history[-10:] if req.history else []
            async for token in stream_direct(
                req.question, "", req.model,
                system_prompt="친절하고 자연스럽게 대화하세요. 궁금한 점이 있으면 언제든 물어보세요.",
                history=history,
            ):
                yield f"data: {json.dumps({'type': 'token', 'data': token}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        else:
            # Tier 2: Agentic RAG (ReAct loop)
            async for event_type, data in agentic_rag_stream(
                req.question, req.collection_names, req.top_k, req.model, req.history
            ):
                if event_type == "thinking":
                    yield f"data: {json.dumps({'type': 'thinking', 'data': data}, ensure_ascii=False)}\n\n"
                elif event_type == "sources":
                    sources_trimmed = [
                        {
                            "index": c["index"],
                            "text": c["text"][:200],
                            "score": c.get("rerank_score", c.get("rrf_score", c.get("score", 0))),
                        }
                        for c in data
                    ]
                    yield f"data: {json.dumps({'type': 'sources', 'data': sources_trimmed}, ensure_ascii=False)}\n\n"
                elif event_type == "token":
                    yield f"data: {json.dumps({'type': 'token', 'data': data}, ensure_ascii=False)}\n\n"
                elif event_type == "done":
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


