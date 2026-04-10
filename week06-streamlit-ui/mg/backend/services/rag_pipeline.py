"""Production RAG Pipeline — Hybrid Search + Reranking + Relevance Gate.

Flow:
1. Embed question (1 API call)
2. Quick probe: top-1 cosine score across collections
3. If score < 0.55 → skip RAG, direct LLM
4. If score >= 0.55 → full pipeline (BM25 + RRF + Rerank + stream)
"""

import time

from services.embedding_service import embed_single
from services import vector_store
from services.hybrid_search import _bm25_search, _reciprocal_rank_fusion
from services.reranker_service import rerank
from services.llm_service import stream_with_context
from services.rag_utils import SYSTEM_PROMPT, format_context
from services.message_router import RELEVANCE_THRESHOLD


async def _probe_relevance(
    query_emb: list[float],
    collection_names: list[str],
) -> float:
    """Quick check: what's the best cosine similarity across all collections?"""
    best = 0.0
    for col_name in collection_names:
        try:
            results, _ = vector_store.search(col_name, query_emb, top_k=1)
            if results and results[0].score > best:
                best = results[0].score
        except Exception:
            continue
    return best


async def _full_search_with_rerank(
    question: str,
    query_emb: list[float],
    collection_names: list[str],
    top_k: int = 5,
    model: str = "gpt-4o-mini",
) -> list[dict]:
    """Full Hybrid Search + Rerank across multiple collections. Reuses pre-computed embedding."""
    search_k = top_k * 2
    all_chunks: list[dict] = []

    for col_name in collection_names:
        try:
            # Vector search (reuse embedding)
            vec_results, _ = vector_store.search(col_name, query_emb, search_k)
            vec_chunks = [
                {"index": r.index, "text": r.text, "score": round(r.score, 4), "source": col_name}
                for r in vec_results
            ]

            # BM25
            bm25_chunks, _ = _bm25_search(col_name, question, search_k)
            for c in bm25_chunks:
                c["source"] = col_name

            # RRF merge
            merged = _reciprocal_rank_fusion(vec_chunks, bm25_chunks)
            all_chunks.extend(merged)
        except Exception:
            continue

    if not all_chunks:
        return []

    # Deduplicate
    seen: set[str] = set()
    unique: list[dict] = []
    for c in all_chunks:
        key = c["text"][:100]
        if key not in seen:
            seen.add(key)
            unique.append(c)

    unique.sort(key=lambda c: c.get("rrf_score", c.get("score", 0)), reverse=True)
    candidates = unique[:top_k * 3]

    if candidates:
        reranked, _, _ = await rerank(question, candidates, top_n=top_k, model=model)
        return reranked

    return candidates[:top_k]


async def rag_stream(
    question: str,
    collection_names: list[str],
    top_k: int = 5,
    model: str = "gpt-4o-mini",
    history: list[dict] | None = None,
):
    """RAG stream with post-search relevance gating.

    1. Embed question (reused for both probe and full search)
    2. Probe top-1 score
    3. If relevant → full pipeline with sources
    4. If not → direct LLM, no sources
    """
    # Step 1: Embed (done once, reused)
    query_emb, _ = await embed_single(question)

    # Step 2: Relevance probe
    best_score = await _probe_relevance(query_emb, collection_names)

    if best_score >= RELEVANCE_THRESHOLD:
        # Step 3a: Full RAG pipeline
        chunks = await _full_search_with_rerank(
            question, query_emb, collection_names, top_k, model
        )
        context = format_context(chunks)

        yield "sources", chunks

        async for token in stream_with_context(
            question, context, model,
            system_prompt=SYSTEM_PROMPT,
            history=history,
        ):
            yield "token", token
    else:
        # Step 3b: Direct LLM (no retrieval context)
        yield "sources", []

        async for token in stream_with_context(
            question, "", model,
            system_prompt="친절하고 자연스럽게 대화하세요. 궁금한 점이 있으면 언제든 물어보세요.",
            history=history,
        ):
            yield "token", token

    yield "done", None
