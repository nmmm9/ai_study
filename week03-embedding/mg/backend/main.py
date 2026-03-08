from dotenv import load_dotenv

load_dotenv()

import hashlib
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tiktoken

from models.schemas import (
    SamplesResponse,
    SampleInfo,
    SampleDetailResponse,
    EmbedRequest,
    EmbedResponse,
    VectorDBSearchRequest,
    MemorySearchRequest,
    SearchResponse,
    ScoredChunkSchema,
    TimingBreakdown,
    VizResponse,
    VizChunkPoint,
    Point2D,
    CollectionsResponse,
    CollectionItem,
)
from services.chunking_service import chunk_text
from services.embedding_service import embed_texts, embed_single
from services.llm_service import ask_with_context, PRICING
from services.memory_search import search_in_memory
from services import vector_store
from services.viz_service import reduce_to_2d
from data.samples import SAMPLES

app = FastAPI(title="Embedding & Vector DB Demo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
    items = [
        SampleInfo(id=s["id"], title=s["title"], length=len(s["content"]))
        for s in SAMPLES
    ]
    return SamplesResponse(samples=items)


@app.get("/api/samples/{sample_id}", response_model=SampleDetailResponse)
async def get_sample(sample_id: str):
    for s in SAMPLES:
        if s["id"] == sample_id:
            return SampleDetailResponse(
                id=s["id"],
                title=s["title"],
                content=s["content"],
                length=len(s["content"]),
            )
    raise HTTPException(status_code=404, detail="Sample not found")


# ─── Embed ───


@app.post("/api/embed", response_model=EmbedResponse)
async def embed_document(req: EmbedRequest):
    if not req.document.strip():
        raise HTTPException(400, "Document cannot be empty")

    collection_name = req.collection_name or make_collection_name(
        req.document, req.chunk_size, req.chunk_overlap
    )

    # Check if already embedded
    if vector_store.collection_exists(collection_name):
        cols = vector_store.list_collections()
        count = next((c["count"] for c in cols if c["name"] == collection_name), 0)
        return EmbedResponse(
            collection_name=collection_name,
            chunk_count=count,
            dimension=1536,
            embed_time_ms=0,
            store_time_ms=0,
            total_time_ms=0,
            embed_cost=0,
        )

    total_start = time.perf_counter()

    # Chunk
    chunks = chunk_text(req.document, req.chunk_size, req.chunk_overlap)
    chunk_texts = [c.text for c in chunks]

    # Embed via OpenAI
    embeddings, embed_time_ms = await embed_texts(chunk_texts)

    # Store in ChromaDB
    metadatas = [
        {"index": c.index, "start": c.start, "end": c.end} for c in chunks
    ]
    store_time_ms = vector_store.add_chunks(
        collection_name, chunk_texts, embeddings, metadatas
    )

    total_ms = int((time.perf_counter() - total_start) * 1000)

    # Calculate embedding cost
    token_count = sum(count_tokens(t) for t in chunk_texts)
    embed_cost = round(token_count * PRICING["embedding"], 6)

    return EmbedResponse(
        collection_name=collection_name,
        chunk_count=len(chunks),
        dimension=len(embeddings[0]),
        embed_time_ms=embed_time_ms,
        store_time_ms=store_time_ms,
        total_time_ms=total_ms,
        embed_cost=embed_cost,
    )


# ─── Search ───


@app.post("/api/search/vectordb", response_model=SearchResponse)
async def search_vectordb(req: VectorDBSearchRequest):
    try:
        # 1. Embed query only
        query_emb, embed_ms = await embed_single(req.question)

        # 2. Search ChromaDB
        results, search_ms = vector_store.search(
            req.collection_name, query_emb, req.top_k
        )

        # 3. LLM answer
        context = "\n\n".join([r.text for r in results])
        llm_result = await ask_with_context(req.question, context, req.model)

        # Cost: embed query + LLM
        query_tokens = count_tokens(req.question)
        embed_cost = query_tokens * PRICING["embedding"]
        total_cost = round(llm_result.cost_usd + embed_cost, 6)

        return SearchResponse(
            answer=llm_result.answer,
            timing=TimingBreakdown(
                embed_ms=embed_ms,
                search_ms=search_ms,
                llm_ms=llm_result.time_ms,
                total_ms=embed_ms + search_ms + llm_result.time_ms,
            ),
            cost_usd=total_cost,
            prompt_tokens=llm_result.prompt_tokens,
            completion_tokens=llm_result.completion_tokens,
            total_tokens=llm_result.total_tokens,
            used_chunks=[
                ScoredChunkSchema(
                    index=r.index, text=r.text, score=round(r.score, 4)
                )
                for r in results
            ],
            chunk_count=len(results),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/memory", response_model=SearchResponse)
async def search_memory(req: MemorySearchRequest):
    try:
        chunks = chunk_text(req.document, req.chunk_size, req.chunk_overlap)

        # In-memory: embed ALL chunks + query every time
        scored, embed_ms, search_ms = await search_in_memory(
            req.question, chunks, req.top_k
        )

        context = "\n\n".join([sc.text for sc in scored])
        llm_result = await ask_with_context(req.question, context, req.model)

        # Cost: embed all chunks + query + LLM
        all_tokens = sum(count_tokens(c.text) for c in chunks) + count_tokens(
            req.question
        )
        embed_cost = all_tokens * PRICING["embedding"]
        total_cost = round(llm_result.cost_usd + embed_cost, 6)

        return SearchResponse(
            answer=llm_result.answer,
            timing=TimingBreakdown(
                embed_ms=embed_ms,
                search_ms=search_ms,
                llm_ms=llm_result.time_ms,
                total_ms=embed_ms + search_ms + llm_result.time_ms,
            ),
            cost_usd=total_cost,
            prompt_tokens=llm_result.prompt_tokens,
            completion_tokens=llm_result.completion_tokens,
            total_tokens=llm_result.total_tokens,
            used_chunks=[
                ScoredChunkSchema(
                    index=sc.index, text=sc.text, score=round(sc.score, 4)
                )
                for sc in scored
            ],
            chunk_count=len(chunks),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Visualization ───


@app.get("/api/visualize/{collection_name}", response_model=VizResponse)
async def visualize(collection_name: str, query: str | None = None):
    try:
        embeddings, texts, indices = vector_store.get_all_embeddings(collection_name)
    except Exception:
        raise HTTPException(404, f"Collection '{collection_name}' not found")

    query_emb = None
    if query:
        query_emb, _ = await embed_single(query)

    chunk_points_raw, query_point_raw = reduce_to_2d(embeddings, query_emb)

    points = [
        VizChunkPoint(
            x=chunk_points_raw[i]["x"],
            y=chunk_points_raw[i]["y"],
            index=indices[i],
            text_preview=texts[i][:50],
        )
        for i in range(len(embeddings))
    ]

    query_point = None
    if query_point_raw:
        query_point = Point2D(x=query_point_raw["x"], y=query_point_raw["y"])

    return VizResponse(points=points, query_point=query_point)


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
