from dotenv import load_dotenv

load_dotenv()

import hashlib

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tiktoken

from models.schemas import (
    SamplesResponse,
    SampleInfo,
    SampleDetailResponse,
    EmbedRequest,
    EmbedResponse,
    CollectionsResponse,
    CollectionItem,
    RagRequest,
    RagResponse,
    ChatRequest,
    ChatMessage,
    PipelineStep,
    SourceChunk,
)
from services.chunking_service import chunk_text
from services.embedding_service import embed_texts
from services.llm_service import PRICING
from services import vector_store
from services.rag_pipeline import run_rag, run_chat_rag
from data.samples import SAMPLES

app = FastAPI(title="RAG Pipeline Demo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_enc = tiktoken.encoding_for_model("gpt-4o-mini")


def count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def make_collection_name(document: str, chunk_size: int, overlap: int) -> str:
    for s in SAMPLES:
        if s["content"] == document:
            return f"{s['id']}-{chunk_size}-{overlap}"
    h = hashlib.md5(document.encode()).hexdigest()[:8]
    return f"custom-{h}-{chunk_size}-{overlap}"


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
            return SampleDetailResponse(
                id=s["id"], title=s["title"], content=s["content"]
            )
    raise HTTPException(404, f"Sample '{sample_id}' not found")


# ─── Embed ───


@app.post("/api/embed", response_model=EmbedResponse)
async def embed_document(req: EmbedRequest):
    col_name = make_collection_name(req.document, req.chunk_size, req.chunk_overlap)

    if vector_store.collection_exists(col_name):
        col = vector_store.create_collection(col_name)
        return EmbedResponse(
            collection_name=col_name,
            chunk_count=col.count(),
            dimension=1536,
            embed_time_ms=0,
            store_time_ms=0,
            total_time_ms=0,
            embed_cost=0,
        )

    chunks = chunk_text(req.document, req.chunk_size, req.chunk_overlap)
    texts = [c.text for c in chunks]

    embeddings, embed_ms = await embed_texts(texts)

    metadatas = [{"index": c.index} for c in chunks]
    store_ms = vector_store.add_chunks(col_name, texts, embeddings, metadatas)

    token_count = sum(count_tokens(t) for t in texts)
    embed_cost = round(token_count * PRICING["embedding"], 6)
    total_ms = embed_ms + store_ms

    return EmbedResponse(
        collection_name=col_name,
        chunk_count=len(texts),
        dimension=len(embeddings[0]),
        embed_time_ms=embed_ms,
        store_time_ms=store_ms,
        total_time_ms=total_ms,
        embed_cost=embed_cost,
    )


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


# ─── RAG ───


@app.post("/api/rag", response_model=RagResponse)
async def rag(req: RagRequest):
    try:
        result = await run_rag(
            question=req.question,
            collection_name=req.collection_name,
            top_k=req.top_k,
            model=req.model,
        )
        return RagResponse(
            answer=result["answer"],
            sources=[SourceChunk(**s) for s in result["sources"]],
            steps=[PipelineStep(**s) for s in result["steps"]],
            timing=result["timing"],
            cost_usd=result["cost_usd"],
            total_tokens=result["total_tokens"],
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── Chat (RAG + conversation history) ───


@app.post("/api/chat", response_model=RagResponse)
async def chat(req: ChatRequest):
    try:
        history = [{"role": m.role, "content": m.content} for m in req.history]
        result = await run_chat_rag(
            question=req.question,
            collection_name=req.collection_name,
            history=history,
            top_k=req.top_k,
            model=req.model,
        )
        return RagResponse(
            answer=result["answer"],
            sources=[SourceChunk(**s) for s in result["sources"]],
            steps=[PipelineStep(**s) for s in result["steps"]],
            timing=result["timing"],
            cost_usd=result["cost_usd"],
            total_tokens=result["total_tokens"],
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))
