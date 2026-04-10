"""Hybrid Search — Vector + BM25 keyword search with Reciprocal Rank Fusion.

Combines semantic (vector) search with lexical (BM25) search
to catch both meaning-similar and keyword-matching chunks.
"""

import time
from rank_bm25 import BM25Okapi

from services.embedding_service import embed_single
from services import vector_store
from services.llm_service import ask_with_context
from services.rag_utils import SYSTEM_PROMPT, format_context


def _bm25_search(
    collection_name: str, query: str, top_k: int
) -> tuple[list[dict], int]:
    """BM25 keyword search over all documents in the collection."""
    start = time.perf_counter()

    col = vector_store.create_collection(collection_name)
    all_docs = col.get(include=["documents", "metadatas"])

    if not all_docs["documents"]:
        return [], 0

    docs = all_docs["documents"]
    metadatas = all_docs["metadatas"]

    # Tokenize (simple whitespace split for Korean/English)
    tokenized = [doc.split() for doc in docs]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(query.split())

    # Build scored results
    scored = []
    for i, score in enumerate(scores):
        idx = metadatas[i].get("index", i) if metadatas else i
        scored.append({
            "index": idx,
            "text": docs[i],
            "bm25_score": float(score),
        })

    scored.sort(key=lambda x: x["bm25_score"], reverse=True)
    elapsed = int((time.perf_counter() - start) * 1000)
    return scored[:top_k], elapsed


def _reciprocal_rank_fusion(
    vector_results: list[dict],
    bm25_results: list[dict],
    k: int = 60,
) -> list[dict]:
    """Merge two ranked lists using Reciprocal Rank Fusion (RRF)."""
    scores: dict[int, float] = {}
    text_map: dict[int, str] = {}
    vec_score_map: dict[int, float] = {}

    for rank, r in enumerate(vector_results):
        idx = r["index"]
        scores[idx] = scores.get(idx, 0) + 1.0 / (k + rank + 1)
        text_map[idx] = r["text"]
        vec_score_map[idx] = r.get("score", 0)

    for rank, r in enumerate(bm25_results):
        idx = r["index"]
        scores[idx] = scores.get(idx, 0) + 1.0 / (k + rank + 1)
        text_map[idx] = r["text"]

    merged = []
    for idx, rrf_score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        merged.append({
            "index": idx,
            "text": text_map[idx],
            "score": round(vec_score_map.get(idx, 0), 4),
            "rrf_score": round(rrf_score, 4),
        })

    return merged


async def run_hybrid_rag(
    question: str,
    collection_name: str,
    top_k: int = 5,
    model: str = "gpt-4o-mini",
) -> dict:
    """Hybrid RAG: vector search + BM25 → RRF merge → generate."""
    steps = []
    search_k = top_k * 3

    # Step 1: Embed + Vector search
    query_emb, embed_ms = await embed_single(question)
    steps.append({"name": "embed", "label": "질문 임베딩", "time_ms": embed_ms})

    vec_results, vec_ms = vector_store.search(collection_name, query_emb, search_k)
    vec_chunks = [
        {"index": r.index, "text": r.text, "score": round(r.score, 4)}
        for r in vec_results
    ]
    steps.append({
        "name": "search", "label": "벡터 검색",
        "time_ms": vec_ms, "detail": f"{len(vec_chunks)}개 검색",
    })

    # Step 2: BM25 search
    bm25_chunks, bm25_ms = _bm25_search(collection_name, question, search_k)
    steps.append({
        "name": "bm25", "label": "BM25 키워드 검색",
        "time_ms": bm25_ms, "detail": f"{len(bm25_chunks)}개 검색",
    })

    # Step 3: RRF merge
    start = time.perf_counter()
    merged = _reciprocal_rank_fusion(vec_chunks, bm25_chunks)
    final = merged[:top_k]
    rrf_ms = int((time.perf_counter() - start) * 1000)
    steps.append({
        "name": "rrf", "label": "RRF 병합",
        "time_ms": rrf_ms, "detail": f"→ {len(final)}개 선택",
    })

    # Step 4: Generate
    context = format_context(final)
    llm_result = await ask_with_context(
        question, context, model, system_prompt=SYSTEM_PROMPT
    )
    steps.append({"name": "generate", "label": "LLM 생성", "time_ms": llm_result.time_ms})

    total_ms = embed_ms + vec_ms + bm25_ms + rrf_ms + llm_result.time_ms

    return {
        "answer": llm_result.answer,
        "sources": final,
        "steps": steps,
        "timing": {
            "embed_ms": embed_ms, "vector_ms": vec_ms, "bm25_ms": bm25_ms,
            "rrf_ms": rrf_ms, "llm_ms": llm_result.time_ms, "total_ms": total_ms,
        },
        "cost_usd": llm_result.cost_usd,
        "total_tokens": llm_result.total_tokens,
        "mode": "hybrid",
    }
