"""Retriever Agent — the heart of Agentic RAG.

Unlike a simple "search → return" pipeline, this agent:
1. Reformulates the query (search-friendly form, removes pronouns)
2. Searches the document store
3. Self-evaluates the retrieved chunks (relevance 1~5)
4. If irrelevant, rewrites query and retries (up to 2 times)
5. Returns chunks with citations

This is the Self-RAG pattern (Asai et al., 2023) wrapped in our
Plan-and-Execute graph as the `documents` domain.
"""

import json
from openai import AsyncOpenAI

from config import DOMAIN_MODEL
from services.document_store import search as vector_search, Chunk

_client = AsyncOpenAI()

MAX_RETRIEVAL_ROUNDS = 2
RELEVANCE_THRESHOLD = 3   # 5점 만점, 3 이상이면 충분


_QUERY_REWRITE_SYSTEM = """당신은 검색 쿼리 변환 전문가입니다.
원본 질문을 벡터 검색에 적합한 짧고 명확한 쿼리로 변환하세요.

원칙:
- 대명사 제거 ("이것", "그", "거기" 등을 구체화)
- 짧고 핵심 키워드 위주 (최대 30자)
- 같은 의미라도 문서에 자주 쓰일 표현으로

반드시 JSON 으로만 응답:
{"query": "변환된 쿼리"}
"""


_RELEVANCE_SYSTEM = """당신은 검색 결과 평가자입니다.
사용자 질문과 검색된 chunk 들을 보고, 답변에 충분한지 1~5점으로 평가하세요.

평가 기준:
- 5: 질문에 직접 답할 정보가 있음
- 4: 거의 충분, 약간의 추론 필요
- 3: 부분적으로 관련 있음, 추가 검색 권장
- 2: 거의 관련 없음
- 1: 무관

반드시 JSON 으로만 응답:
{
  "score": 5,
  "reasoning": "한 문장 근거",
  "alternative_query": "점수가 3 미만일 때만 다른 검색어 제안"
}
"""


async def _rewrite_query(question: str, history_hint: str = "",
                         model: str | None = None) -> str:
    """Convert user question into a search-friendly query."""
    model = model or DOMAIN_MODEL
    user = f"질문: {question}"
    if history_hint:
        user += f"\n\n이전 대화 맥락: {history_hint[:300]}"

    resp = await _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _QUERY_REWRITE_SYSTEM},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    try:
        parsed = json.loads(resp.choices[0].message.content or "{}")
        return (parsed.get("query") or question)[:120]
    except json.JSONDecodeError:
        return question


async def _evaluate_relevance(question: str, chunks: list[Chunk],
                              model: str | None = None) -> dict:
    """LLM scores whether the retrieved chunks are sufficient (1~5)."""
    model = model or DOMAIN_MODEL
    if not chunks:
        return {"score": 1, "reasoning": "검색 결과 없음", "alternative_query": ""}

    chunk_text = "\n\n".join(
        f"[{i + 1}] ({c.doc_name} score={(c.score or 0):.2f})\n{c.text[:400]}"
        for i, c in enumerate(chunks[:5])
    )

    user = f"질문: {question}\n\n검색된 chunks:\n{chunk_text}"

    resp = await _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _RELEVANCE_SYSTEM},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    try:
        parsed = json.loads(resp.choices[0].message.content or "{}")
        score = int(parsed.get("score", 3))
        return {
            "score": max(1, min(5, score)),
            "reasoning": parsed.get("reasoning", "")[:200],
            "alternative_query": (parsed.get("alternative_query") or "")[:120],
        }
    except (json.JSONDecodeError, ValueError):
        return {"score": 3, "reasoning": "평가 실패", "alternative_query": ""}


async def run_retriever(
    question: str,
    history: list[dict] | None = None,
    model: str | None = None,
    on_event=None,
    top_k: int = 5,
) -> dict:
    """Run the agentic retrieval loop.

    Returns:
        {
            "chunks": [Chunk, ...],
            "rounds": [{query, score, reasoning}, ...],
            "final_score": int,
        }

    on_event callback events:
        - "retrieval_round": {round, query, top_k}
        - "retrieval_result": {round, chunks: [{doc_name, score, text_snippet}]}
        - "retrieval_eval":   {round, score, reasoning, alternative_query}
    """
    history = history or []
    history_hint = " ".join(
        (h.get("content") or "")[:200] for h in history[-4:]
        if h.get("role") in ("user", "assistant")
    )

    rounds_log: list[dict] = []
    best_chunks: list[Chunk] = []
    best_score = 0
    current_query = await _rewrite_query(question, history_hint, model)

    for round_num in range(1, MAX_RETRIEVAL_ROUNDS + 1):
        if on_event:
            await on_event("retrieval_round", {
                "round": round_num, "query": current_query, "top_k": top_k,
            })

        chunks = await vector_search(current_query, top_k=top_k)

        if on_event:
            await on_event("retrieval_result", {
                "round": round_num,
                "chunks": [{
                    "doc_name": c.doc_name,
                    "page": c.page,
                    "score": round(c.score or 0, 3),
                    "text_snippet": c.text[:200],
                } for c in chunks],
            })

        evaluation = await _evaluate_relevance(question, chunks, model)
        score = evaluation["score"]

        if on_event:
            await on_event("retrieval_eval", {
                "round": round_num,
                "score": score,
                "reasoning": evaluation["reasoning"],
                "alternative_query": evaluation["alternative_query"],
            })

        rounds_log.append({
            "round": round_num,
            "query": current_query,
            "score": score,
            "reasoning": evaluation["reasoning"],
            "chunks_count": len(chunks),
        })

        if score > best_score:
            best_score = score
            best_chunks = chunks

        if score >= RELEVANCE_THRESHOLD:
            break

        # Try alternative query
        alt = evaluation.get("alternative_query") or ""
        if not alt or alt == current_query:
            break
        current_query = alt

    return {
        "chunks": best_chunks,
        "rounds": rounds_log,
        "final_score": best_score,
    }


def format_chunks_for_writer(chunks: list[Chunk]) -> str:
    """Format retrieved chunks as a citation-friendly block for the Writer."""
    if not chunks:
        return "(검색 결과 없음)"
    parts = []
    for i, c in enumerate(chunks, start=1):
        loc = f"{c.doc_name}"
        if c.page is not None:
            loc += f", p.{c.page}"
        parts.append(f"[{i}] {loc}\n{c.text}")
    return "\n\n".join(parts)
