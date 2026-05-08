from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tiktoken

from models.schemas import (
    SamplesResponse,
    SampleInfo,
    SampleDetailResponse,
    AskRawRequest,
    RawResponse,
    Stats,
    AskChunkedRequest,
    ChunkedResponse,
    ChunksInfo,
    ScoredChunkSchema,
)
from services.llm_service import ask_with_context, PRICING
from services.chunking_service import chunk_text
from services.embedding_service import search_similar
from data.samples import SAMPLES

app = FastAPI(title="Chunking Demo API")
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


@app.post("/api/ask-raw", response_model=RawResponse)
async def ask_raw(request: AskRawRequest):
    doc_tokens = count_tokens(request.document)

    try:
        result = await ask_with_context(
            request.question, request.document, request.model
        )
        return RawResponse(
            answer=result.answer,
            stats=Stats(
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                total_tokens=result.total_tokens,
                time_ms=result.time_ms,
                cost_usd=result.cost_usd,
                document_tokens=doc_tokens,
            ),
        )
    except Exception as e:
        error_str = str(e)
        if "maximum context length" in error_str or "too many tokens" in error_str.lower():
            model_limits = {"gpt-4o": 128000, "gpt-4o-mini": 128000}
            return RawResponse(
                answer=None,
                error="token_limit_exceeded",
                message=f"문서가 너무 깁니다 (약 {doc_tokens:,} 토큰). 모델 한도를 초과했습니다. 이것이 청킹이 필요한 이유입니다.",
                stats=Stats(
                    document_tokens=doc_tokens,
                    model_limit=model_limits.get(request.model, 128000),
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    time_ms=0,
                    cost_usd=0,
                ),
            )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask-chunked", response_model=ChunkedResponse)
async def ask_chunked(request: AskChunkedRequest):
    chunks = chunk_text(request.document, request.chunk_size, request.chunk_overlap)

    results = await search_similar(request.question, chunks, request.top_k)

    context = "\n\n".join([sc.text for sc in results])
    doc_tokens = count_tokens(context)

    llm_result = await ask_with_context(request.question, context, request.model)

    embed_token_count = sum(count_tokens(c.text) for c in chunks) + count_tokens(request.question)
    embed_cost = embed_token_count * PRICING["embedding"]
    total_cost = round(llm_result.cost_usd + embed_cost, 6)

    used_chunks = [
        ScoredChunkSchema(
            index=sc.index,
            text=sc.text,
            score=round(sc.score, 4),
            start=sc.start,
            end=sc.end,
        )
        for sc in results
    ]

    return ChunkedResponse(
        answer=llm_result.answer,
        stats=Stats(
            prompt_tokens=llm_result.prompt_tokens,
            completion_tokens=llm_result.completion_tokens,
            total_tokens=llm_result.total_tokens,
            time_ms=llm_result.time_ms,
            cost_usd=total_cost,
            document_tokens=doc_tokens,
        ),
        chunks=ChunksInfo(total_count=len(chunks), used=used_chunks),
    )
