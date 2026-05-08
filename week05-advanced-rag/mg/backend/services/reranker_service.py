"""LLM-based Reranker.

Takes initial search results and re-scores them using LLM
for more accurate relevance ranking.
"""

import json

from services.llm_service import ask_json

RERANK_SYSTEM = """다음 질문과 각 텍스트 청크의 관련성을 0~10점으로 평가하세요.

평가 기준:
- 10: 질문에 직접적으로 답변하는 내용
- 7-9: 매우 관련 있는 내용
- 4-6: 부분적으로 관련 있는 내용
- 1-3: 약간 관련 있는 내용
- 0: 전혀 관련 없음

반드시 다음 JSON 형식으로만 응답하세요:
{"results": [{"index": 0, "score": 8}, {"index": 1, "score": 3}]}"""


async def rerank(
    question: str,
    chunks: list[dict],
    top_n: int = 5,
    model: str = "gpt-4o-mini",
) -> tuple[list[dict], int, float]:
    """Rerank chunks by LLM-scored relevance.

    Returns: (reranked_chunks, time_ms, cost_usd)
    """
    if not chunks:
        return [], 0, 0.0

    chunk_texts = "\n\n".join(
        f"[청크 {i}] {c['text'][:300]}" for i, c in enumerate(chunks)
    )
    user_msg = f"질문: {question}\n\n{chunk_texts}"

    content, elapsed_ms, cost = await ask_json(
        system_prompt=RERANK_SYSTEM,
        user_prompt=user_msg,
        model=model,
        temperature=0,
    )

    # Parse LLM scores
    score_map: dict[int, float] = {}
    try:
        data = json.loads(content)
        results_list = data.get("results", [])
        for item in results_list:
            idx = item.get("index", -1)
            score = item.get("score", 0)
            score_map[idx] = score
    except (json.JSONDecodeError, AttributeError):
        # Fallback: keep original order
        for i in range(len(chunks)):
            score_map[i] = len(chunks) - i

    # Build scored copies (avoid mutating caller's list)
    scored = [
        {**chunk, "rerank_score": round(score_map.get(i, 0) / 10.0, 4)}
        for i, chunk in enumerate(chunks)
    ]

    # Sort by rerank score descending
    ranked = sorted(scored, key=lambda c: c.get("rerank_score", 0), reverse=True)
    return ranked[:top_n], elapsed_ms, cost
