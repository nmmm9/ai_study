"""Advanced RAG Pipelines.

- HyDE: Hypothetical Document Embeddings
- Rerank: LLM-based reranking
- Advanced: HyDE + Rerank combined
"""

from services.embedding_service import embed_single
from services import vector_store
from services.llm_service import ask_with_context
from services.hyde_service import generate_hypothetical
from services.reranker_service import rerank

SYSTEM_PROMPT = (
    "다음 문서를 참고하여 질문에 답변하세요. "
    "문서에 없는 내용은 '문서에 해당 정보가 없습니다'라고 답하세요."
)


def _format_context(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{i + 1}] {c['text']}" for i, c in enumerate(chunks)
    )


async def run_hyde_rag(
    question: str,
    collection_name: str,
    top_k: int = 5,
    model: str = "gpt-4o-mini",
) -> dict:
    """HyDE RAG: question → hypothetical doc → embed → search → generate."""
    steps = []
    total_cost = 0.0

    # Step 1: Generate hypothetical document
    hyde_text, hyde_ms, hyde_cost = await generate_hypothetical(question, model)
    total_cost += hyde_cost
    steps.append({
        "name": "hyde",
        "label": "HyDE 생성",
        "time_ms": hyde_ms,
        "detail": f"가상 답변 {len(hyde_text)}자",
    })

    # Step 2: Embed hypothetical document (NOT the original question)
    query_emb, embed_ms = await embed_single(hyde_text)
    steps.append({
        "name": "embed",
        "label": "가상 문서 임베딩",
        "time_ms": embed_ms,
    })

    # Step 3: Vector search
    results, search_ms = vector_store.search(collection_name, query_emb, top_k)
    chunks = [
        {"index": r.index, "text": r.text, "score": round(r.score, 4)}
        for r in results
    ]
    steps.append({
        "name": "search",
        "label": "벡터 검색",
        "time_ms": search_ms,
        "detail": f"{len(chunks)}개 청크 검색됨",
    })

    # Step 4: Generate answer
    context = _format_context(chunks)
    llm_result = await ask_with_context(
        question, context, model, system_prompt=SYSTEM_PROMPT
    )
    total_cost += llm_result.cost_usd
    steps.append({
        "name": "generate",
        "label": "LLM 생성",
        "time_ms": llm_result.time_ms,
    })

    total_ms = hyde_ms + embed_ms + search_ms + llm_result.time_ms

    return {
        "answer": llm_result.answer,
        "sources": chunks,
        "steps": steps,
        "timing": {
            "hyde_ms": hyde_ms,
            "embed_ms": embed_ms,
            "search_ms": search_ms,
            "llm_ms": llm_result.time_ms,
            "total_ms": total_ms,
        },
        "cost_usd": round(total_cost, 6),
        "total_tokens": llm_result.total_tokens,
        "mode": "hyde",
        "hyde_query": hyde_text,
    }


async def run_rerank_rag(
    question: str,
    collection_name: str,
    top_k: int = 5,
    model: str = "gpt-4o-mini",
) -> dict:
    """Rerank RAG: question → embed → wide search → rerank → generate."""
    steps = []
    total_cost = 0.0
    initial_k = top_k * 4

    # Step 1: Embed question
    query_emb, embed_ms = await embed_single(question)
    steps.append({
        "name": "embed",
        "label": "질문 임베딩",
        "time_ms": embed_ms,
    })

    # Step 2: Wide vector search
    results, search_ms = vector_store.search(collection_name, query_emb, initial_k)
    initial_chunks = [
        {"index": r.index, "text": r.text, "score": round(r.score, 4)}
        for r in results
    ]
    steps.append({
        "name": "search",
        "label": "벡터 검색 (확장)",
        "time_ms": search_ms,
        "detail": f"{len(initial_chunks)}개 후보 검색",
    })

    # Step 3: LLM Reranking
    reranked, rerank_ms, rerank_cost = await rerank(
        question, initial_chunks, top_n=top_k, model=model
    )
    total_cost += rerank_cost
    steps.append({
        "name": "rerank",
        "label": "리랭킹",
        "time_ms": rerank_ms,
        "detail": f"{len(initial_chunks)}개 → {len(reranked)}개",
    })

    # Step 4: Generate
    context = _format_context(reranked)
    llm_result = await ask_with_context(
        question, context, model, system_prompt=SYSTEM_PROMPT
    )
    total_cost += llm_result.cost_usd
    steps.append({
        "name": "generate",
        "label": "LLM 생성",
        "time_ms": llm_result.time_ms,
    })

    total_ms = embed_ms + search_ms + rerank_ms + llm_result.time_ms

    return {
        "answer": llm_result.answer,
        "sources": reranked,
        "steps": steps,
        "timing": {
            "embed_ms": embed_ms,
            "search_ms": search_ms,
            "rerank_ms": rerank_ms,
            "llm_ms": llm_result.time_ms,
            "total_ms": total_ms,
        },
        "cost_usd": round(total_cost, 6),
        "total_tokens": llm_result.total_tokens,
        "mode": "rerank",
    }


async def run_advanced_rag(
    question: str,
    collection_name: str,
    top_k: int = 5,
    model: str = "gpt-4o-mini",
) -> dict:
    """Advanced RAG: HyDE + Rerank combined."""
    steps = []
    total_cost = 0.0
    initial_k = top_k * 4

    # Step 1: HyDE
    hyde_text, hyde_ms, hyde_cost = await generate_hypothetical(question, model)
    total_cost += hyde_cost
    steps.append({
        "name": "hyde",
        "label": "HyDE 생성",
        "time_ms": hyde_ms,
        "detail": f"가상 답변 {len(hyde_text)}자",
    })

    # Step 2: Embed hypothetical
    query_emb, embed_ms = await embed_single(hyde_text)
    steps.append({
        "name": "embed",
        "label": "가상 문서 임베딩",
        "time_ms": embed_ms,
    })

    # Step 3: Wide vector search
    results, search_ms = vector_store.search(collection_name, query_emb, initial_k)
    initial_chunks = [
        {"index": r.index, "text": r.text, "score": round(r.score, 4)}
        for r in results
    ]
    steps.append({
        "name": "search",
        "label": "벡터 검색 (확장)",
        "time_ms": search_ms,
        "detail": f"{len(initial_chunks)}개 후보 검색",
    })

    # Step 4: Rerank
    reranked, rerank_ms, rerank_cost = await rerank(
        question, initial_chunks, top_n=top_k, model=model
    )
    total_cost += rerank_cost
    steps.append({
        "name": "rerank",
        "label": "리랭킹",
        "time_ms": rerank_ms,
        "detail": f"{len(initial_chunks)}개 → {len(reranked)}개",
    })

    # Step 5: Generate
    context = _format_context(reranked)
    llm_result = await ask_with_context(
        question, context, model, system_prompt=SYSTEM_PROMPT
    )
    total_cost += llm_result.cost_usd
    steps.append({
        "name": "generate",
        "label": "LLM 생성",
        "time_ms": llm_result.time_ms,
    })

    total_ms = hyde_ms + embed_ms + search_ms + rerank_ms + llm_result.time_ms

    return {
        "answer": llm_result.answer,
        "sources": reranked,
        "steps": steps,
        "timing": {
            "hyde_ms": hyde_ms,
            "embed_ms": embed_ms,
            "search_ms": search_ms,
            "rerank_ms": rerank_ms,
            "llm_ms": llm_result.time_ms,
            "total_ms": total_ms,
        },
        "cost_usd": round(total_cost, 6),
        "total_tokens": llm_result.total_tokens,
        "mode": "advanced",
        "hyde_query": hyde_text,
    }
