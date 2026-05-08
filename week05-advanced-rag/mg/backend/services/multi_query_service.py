"""Multi-Query RAG — Generate multiple query variations for broader retrieval.

Creates 3 variations of the original question,
searches each independently, then deduplicates and merges results.
"""

import asyncio
import json

from services.embedding_service import embed_single
from services import vector_store
from services.llm_service import ask_json, ask_with_context
from services.rag_utils import SYSTEM_PROMPT, format_context

MULTI_QUERY_SYSTEM = """사용자의 질문을 3가지 다른 관점에서 재작성하세요.
각 변형은 원래 질문과 같은 정보를 찾지만 다른 표현/관점을 사용합니다.

반드시 다음 JSON 형식으로만 응답하세요:
{"queries": ["변형1", "변형2", "변형3"]}"""




async def _generate_queries(
    question: str, model: str
) -> tuple[list[str], int, float]:
    """Generate 3 query variations. Returns (queries, time_ms, cost)."""
    content, elapsed_ms, cost = await ask_json(
        system_prompt=MULTI_QUERY_SYSTEM,
        user_prompt=question,
        model=model,
        temperature=0.7,
    )
    try:
        data = json.loads(content)
        queries = data.get("queries", [question])
    except (json.JSONDecodeError, AttributeError):
        queries = [question]

    return queries, elapsed_ms, cost


async def run_multi_query_rag(
    question: str,
    collection_name: str,
    top_k: int = 5,
    model: str = "gpt-4o-mini",
) -> dict:
    """Multi-Query RAG: generate variations → search each → merge → generate."""
    steps = []
    total_cost = 0.0

    # Step 1: Generate query variations
    queries, gen_ms, gen_cost = await _generate_queries(question, model)
    total_cost += gen_cost
    all_queries = [question] + queries  # original + 3 variations
    steps.append({
        "name": "multi_query", "label": "질문 변형 생성",
        "time_ms": gen_ms, "detail": f"{len(queries)}개 변형 생성",
    })

    # Step 2: Embed all queries in parallel
    import time as _time
    embed_start = _time.perf_counter()
    embed_results = await asyncio.gather(
        *(embed_single(q) for q in all_queries)
    )
    total_embed_ms = int((_time.perf_counter() - embed_start) * 1000)

    steps.append({
        "name": "embed", "label": "질문들 임베딩 (병렬)",
        "time_ms": total_embed_ms, "detail": f"{len(all_queries)}개 질문",
    })

    # Step 3: Search each embedding
    all_chunks: dict[int, dict] = {}
    total_search_ms = 0

    for query_emb, _ in embed_results:
        results, search_ms = vector_store.search(collection_name, query_emb, top_k)
        total_search_ms += search_ms

        for r in results:
            if r.index not in all_chunks or r.score > all_chunks[r.index]["score"]:
                all_chunks[r.index] = {
                    "index": r.index,
                    "text": r.text,
                    "score": round(r.score, 4),
                }

    steps.append({
        "name": "search", "label": "다중 검색",
        "time_ms": total_search_ms,
        "detail": f"{len(all_queries)}회 검색 → {len(all_chunks)}개 고유 청크",
    })

    # Step 3: Sort by score, take top_k
    merged = sorted(all_chunks.values(), key=lambda c: c["score"], reverse=True)
    final = merged[:top_k]

    # Step 4: Generate
    context = format_context(final)
    llm_result = await ask_with_context(
        question, context, model, system_prompt=SYSTEM_PROMPT
    )
    total_cost += llm_result.cost_usd
    steps.append({
        "name": "generate", "label": "LLM 생성",
        "time_ms": llm_result.time_ms,
    })

    total_ms = gen_ms + total_embed_ms + total_search_ms + llm_result.time_ms

    return {
        "answer": llm_result.answer,
        "sources": final,
        "steps": steps,
        "timing": {
            "query_gen_ms": gen_ms, "embed_ms": total_embed_ms,
            "search_ms": total_search_ms, "llm_ms": llm_result.time_ms,
            "total_ms": total_ms,
        },
        "cost_usd": round(total_cost, 6),
        "total_tokens": llm_result.total_tokens,
        "mode": "multi_query",
        "generated_queries": queries,
    }
