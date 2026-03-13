from dotenv import load_dotenv

load_dotenv()

import asyncio
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
    CompareRequest,
    CompareResponse,
    PipelineStep,
    SourceChunk,
)
from services.chunking_service import chunk_text
from services.embedding_service import embed_texts
from services.llm_service import PRICING
from services import vector_store
from services.basic_pipeline import run_basic_rag
from services.advanced_pipeline import (
    run_hyde_rag,
    run_rerank_rag,
    run_advanced_rag,
)
from data.samples import SAMPLES

app = FastAPI(title="Advanced RAG Demo")
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


# ─── RAG (mode: basic | hyde | rerank | advanced) ───


_RUNNERS = {
    "basic": run_basic_rag,
    "hyde": run_hyde_rag,
    "rerank": run_rerank_rag,
    "advanced": run_advanced_rag,
}


def _to_response(result: dict) -> RagResponse:
    return RagResponse(
        answer=result["answer"],
        sources=[SourceChunk(**s) for s in result["sources"]],
        steps=[PipelineStep(**s) for s in result["steps"]],
        timing=result["timing"],
        cost_usd=result["cost_usd"],
        total_tokens=result["total_tokens"],
        mode=result.get("mode", "basic"),
        hyde_query=result.get("hyde_query"),
    )


@app.post("/api/rag", response_model=RagResponse)
async def rag(req: RagRequest):
    runner = _RUNNERS.get(req.mode, run_basic_rag)
    try:
        result = await runner(
            question=req.question,
            collection_name=req.collection_name,
            top_k=req.top_k,
            model=req.model,
        )
        return _to_response(result)
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ─── Compare (basic vs advanced, run simultaneously) ───


@app.post("/api/compare", response_model=CompareResponse)
async def compare(req: CompareRequest):
    try:
        basic_result, advanced_result = await asyncio.gather(
            run_basic_rag(
                req.question, req.collection_name, req.top_k, req.model
            ),
            run_advanced_rag(
                req.question, req.collection_name, req.top_k, req.model
            ),
        )
        return CompareResponse(
            basic=_to_response(basic_result),
            advanced=_to_response(advanced_result),
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))
