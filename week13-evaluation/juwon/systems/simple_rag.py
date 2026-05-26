"""
simple_rag.py - System A: 기본 RAG

4주차 방식과 동일한 단순 파이프라인:
  질문 → 벡터 검색 1회 → 컨텍스트 조립 → LLM 답변

특징: 가장 단순, 검색 1회, 추가 판단 없음
"""
from systems.base import vector_search, build_context, llm_answer


def run(question: str) -> dict:
    """
    반환: {
        "answer": str,
        "contexts": list[str],  # RAGAS 평가용
        "system": "simple_rag"
    }
    """
    results  = vector_search(question, limit=3)
    context  = build_context(results)
    answer   = llm_answer(context, question)

    contexts = [
        f"{r.get('judge_decision', '')} (레포: {', '.join(rp['name'] for rp in r.get('repos', [])[:3])})"
        for r in results
    ]

    return {
        "answer":   answer,
        "contexts": contexts if contexts else ["관련 데이터 없음"],
        "system":   "simple_rag",
    }
