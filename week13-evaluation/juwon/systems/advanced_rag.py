"""
advanced_rag.py - System B: Advanced RAG

5주차 방식 적용:
  질문 → Multi-Query 확장 (3개) → 각 쿼리로 검색 → RRF 결합 → 리랭킹 → LLM 답변

특징: 검색 커버리지 향상, 중복 제거, 점수 기반 정렬
"""
from systems.base import vector_search, expand_queries, build_context, llm_answer, embed


def _rrf_merge(results_list: list[list[dict]], k: int = 60) -> list[dict]:
    """Reciprocal Rank Fusion으로 여러 검색 결과 합산"""
    scores: dict[str, float] = {}
    docs:   dict[str, dict]  = {}

    for results in results_list:
        for rank, r in enumerate(results):
            doc_id = r.get("id", str(rank))
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
            docs[doc_id]   = r

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [docs[doc_id] for doc_id, _ in ranked[:5]]


def _simple_rerank(question: str, results: list[dict], top_k: int = 3) -> list[dict]:
    """임베딩 코사인 유사도로 간단한 리랭킹"""
    import numpy as np

    q_vec = embed(question)

    scored = []
    for r in results:
        sim = r.get("similarity", 0.5)
        scored.append((sim, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:top_k]]


def run(question: str) -> dict:
    """
    반환: {
        "answer": str,
        "contexts": list[str],
        "system": "advanced_rag"
    }
    """
    queries      = expand_queries(question, n=2)
    results_list = [vector_search(q, limit=5) for q in queries]
    merged       = _rrf_merge(results_list)
    reranked     = _simple_rerank(question, merged, top_k=3)
    context      = build_context(reranked)
    answer       = llm_answer(context, question)

    contexts = [
        f"{r.get('judge_decision', '')} (레포: {', '.join(rp['name'] for rp in r.get('repos', [])[:3])})"
        for r in reranked
    ]

    return {
        "answer":   answer,
        "contexts": contexts if contexts else ["관련 데이터 없음"],
        "system":   "advanced_rag",
    }
