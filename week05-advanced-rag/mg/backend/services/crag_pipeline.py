"""Corrective RAG (CRAG) Pipeline.

Evaluates retrieved document quality and takes corrective action:
- CORRECT: use retrieved docs as-is
- AMBIGUOUS: refine query and re-search
- INCORRECT: rewrite query from different angle and re-search
"""

import json

from services.embedding_service import embed_single
from services import vector_store
from services.llm_service import ask_with_context, ask_json, ask_short
from services.rag_utils import SYSTEM_PROMPT, format_context, chunks_from_results

EVALUATE_DOCS_SYSTEM = """질문과 검색된 문서들의 관련성을 평가하세요.

평가 기준:
- CORRECT: 검색된 문서가 질문에 답하기에 충분함
- AMBIGUOUS: 부분적으로 관련 있지만 불충분함
- INCORRECT: 검색된 문서가 질문과 거의 관련 없음

반드시 다음 JSON 형식으로만 응답하세요:
{"verdict": "CORRECT", "confidence": 0.85, "reason": "판단 이유"}"""

REFINE_QUERY_SYSTEM = (
    "원래 질문으로 검색한 결과가 불충분합니다. "
    "더 나은 검색을 위해 질문을 다른 관점에서 재작성하세요. "
    "재작성된 질문만 출력하세요."
)




async def run_crag(
    question: str,
    collection_name: str,
    top_k: int = 5,
    model: str = "gpt-4o-mini",
) -> dict:
    """CRAG: search → evaluate docs → correct if needed → generate."""
    steps = []
    total_cost = 0.0

    # Step 1: Embed + Search
    query_emb, embed_ms = await embed_single(question)
    steps.append({"name": "embed", "label": "질문 임베딩", "time_ms": embed_ms})

    results, search_ms = vector_store.search(collection_name, query_emb, top_k)
    chunks = chunks_from_results(results)
    steps.append({
        "name": "search", "label": "벡터 검색",
        "time_ms": search_ms, "detail": f"{len(chunks)}개 청크",
    })

    # Step 2: Evaluate retrieved documents
    context = format_context(chunks)
    eval_prompt = f"질문: {question}\n\n검색된 문서:\n{context}"
    eval_content, eval_ms, eval_cost = await ask_json(
        system_prompt=EVALUATE_DOCS_SYSTEM,
        user_prompt=eval_prompt,
        model=model,
    )
    total_cost += eval_cost

    try:
        eval_data = json.loads(eval_content)
        verdict = eval_data.get("verdict", "CORRECT")
        confidence = eval_data.get("confidence", 0.5)
        eval_reason = eval_data.get("reason", "")
    except (json.JSONDecodeError, AttributeError):
        verdict = "CORRECT"
        confidence = 0.5
        eval_reason = "평가 파싱 실패"

    steps.append({
        "name": "evaluate", "label": "문서 품질 평가",
        "time_ms": eval_ms,
        "detail": f"{verdict} (신뢰도: {confidence:.0%})",
    })

    corrective_action = None
    refine_ms = 0
    re_search_ms = 0
    re_embed_ms = 0

    # Step 3: Corrective action if needed
    if verdict in ("AMBIGUOUS", "INCORRECT"):
        corrective_action = verdict

        # Refine query
        refine_prompt = f"원래 질문: {question}\n검색 결과 평가: {verdict} - {eval_reason}"
        refined_query, refine_ms, refine_cost = await ask_short(
            system_prompt=REFINE_QUERY_SYSTEM,
            user_prompt=refine_prompt,
            model=model,
            temperature=0.5,
            max_tokens=150,
        )
        total_cost += refine_cost
        steps.append({
            "name": "refine", "label": "쿼리 수정",
            "time_ms": refine_ms, "detail": f"수정: {refined_query[:60]}...",
        })

        # Re-search with refined query
        re_emb, re_embed_ms = await embed_single(refined_query)
        re_results, re_search_ms = vector_store.search(collection_name, re_emb, top_k)
        new_chunks = chunks_from_results(re_results)
        steps.append({
            "name": "re_search", "label": "재검색",
            "time_ms": re_embed_ms + re_search_ms,
            "detail": f"수정된 쿼리로 {len(new_chunks)}개 검색",
        })

        # Merge: deduplicate, prefer higher scores
        chunk_map = {c["index"]: c for c in chunks}
        for nc in new_chunks:
            if nc["index"] not in chunk_map or nc["score"] > chunk_map[nc["index"]]["score"]:
                chunk_map[nc["index"]] = nc
        chunks = sorted(chunk_map.values(), key=lambda c: c["score"], reverse=True)[:top_k]
        context = format_context(chunks)

    # Step 4: Generate
    llm_result = await ask_with_context(
        question, context, model, system_prompt=SYSTEM_PROMPT
    )
    total_cost += llm_result.cost_usd
    steps.append({"name": "generate", "label": "LLM 생성", "time_ms": llm_result.time_ms})

    total_ms = (
        embed_ms + search_ms + eval_ms + refine_ms +
        re_embed_ms + re_search_ms + llm_result.time_ms
    )

    return {
        "answer": llm_result.answer,
        "sources": chunks,
        "steps": steps,
        "timing": {
            "embed_ms": embed_ms, "search_ms": search_ms, "eval_ms": eval_ms,
            "refine_ms": refine_ms, "re_search_ms": re_embed_ms + re_search_ms,
            "llm_ms": llm_result.time_ms, "total_ms": total_ms,
        },
        "cost_usd": round(total_cost, 6),
        "total_tokens": llm_result.total_tokens,
        "mode": "crag",
        "corrective_action": corrective_action,
        "eval_verdict": verdict,
    }
