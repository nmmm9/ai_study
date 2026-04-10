"""Agentic RAG — ReAct-style loop with tool use.

Unlike pipeline RAG (fixed flow), the agent:
1. Plans what to do based on the question
2. Chooses tools (doc search, web-like search, direct answer)
3. Evaluates results after each step
4. Retries with rewritten queries if needed
5. Generates final answer only when satisfied

Max 3 iterations to keep latency reasonable.
"""

import json
from services.embedding_service import embed_single
from services import vector_store
from services.hybrid_search import _bm25_search, _reciprocal_rank_fusion
from services.reranker_service import rerank
from services.llm_service import ask_json, stream_with_context
from services.rag_utils import format_context
from services.message_router import RELEVANCE_THRESHOLD

MAX_ITERATIONS = 3

PLANNER_PROMPT = """당신은 RAG 검색 에이전트입니다. 사용자의 질문을 분석하고 최적의 행동을 결정하세요.

사용 가능한 도구:
- "search": 문서에서 정보를 검색합니다. 검색 쿼리를 지정하세요.
- "answer": 충분한 정보가 모였으면 최종 답변을 생성합니다.

현재까지 검색된 정보:
{context}

규칙:
- 질문에 답하기에 정보가 부족하면 "search"를 선택하고, 더 나은 검색 쿼리를 작성하세요.
- 이전 검색 쿼리와 다른 관점/표현으로 쿼리를 작성하세요.
- 충분한 정보가 있으면 "answer"를 선택하세요.
- 일반 대화(인사, 감사 등)에는 바로 "answer"를 선택하세요.

반드시 다음 JSON 형식으로만 응답하세요:
{{"action": "search", "query": "검색할 내용", "reason": "이유"}}
또는
{{"action": "answer", "reason": "충분한 이유"}}"""

GRADER_PROMPT = """검색된 문서들이 질문에 답하기에 충분한지 평가하세요.

질문: {question}

검색된 문서:
{context}

평가 기준:
- "sufficient": 질문에 답하기에 충분한 정보가 있음
- "partial": 부분적으로 관련 있지만 보충이 필요함
- "insufficient": 관련 정보가 거의 없음

반드시 다음 JSON 형식으로만 응답하세요:
{{"grade": "sufficient", "reason": "판단 이유", "missing": "부족한 정보 (있다면)"}}"""


async def _search_collections(
    query: str,
    query_emb: list[float],
    collection_names: list[str],
    top_k: int = 5,
    model: str = "gpt-4o-mini",
) -> list[dict]:
    """Hybrid Search + Rerank across collections."""
    search_k = top_k * 2
    all_chunks: list[dict] = []

    for col_name in collection_names:
        try:
            vec_results, _ = vector_store.search(col_name, query_emb, search_k)
            vec_chunks = [
                {"index": r.index, "text": r.text, "score": round(r.score, 4), "source": col_name}
                for r in vec_results
            ]
            bm25_chunks, _ = _bm25_search(col_name, query, search_k)
            for c in bm25_chunks:
                c["source"] = col_name
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
        reranked, _, _ = await rerank(query, candidates, top_n=top_k, model=model)
        return reranked
    return candidates[:top_k]


async def agentic_rag_stream(
    question: str,
    collection_names: list[str],
    top_k: int = 5,
    model: str = "gpt-4o-mini",
    history: list[dict] | None = None,
):
    """Agentic RAG with ReAct loop. Yields (event_type, data) tuples."""

    all_chunks: list[dict] = []
    search_queries: list[str] = []
    iterations = 0

    # Step 1: Initial relevance probe
    query_emb, _ = await embed_single(question)
    best_score = 0.0
    for col_name in collection_names:
        try:
            results, _ = vector_store.search(col_name, query_emb, top_k=1)
            if results and results[0].score > best_score:
                best_score = results[0].score
        except Exception:
            continue

    # If not relevant to any document, skip agent loop
    if best_score < RELEVANCE_THRESHOLD:
        yield "thinking", {"step": "판단", "detail": "문서와 관련 없는 질문 → 직접 답변"}
        yield "sources", []
        async for token in stream_with_context(
            question, "", model,
            system_prompt="친절하고 자연스럽게 대화하세요.",
            history=history,
        ):
            yield "token", token
        yield "done", None
        return

    # Step 2: Agent loop (ReAct)
    while iterations < MAX_ITERATIONS:
        iterations += 1
        context_so_far = format_context(all_chunks) if all_chunks else "(아직 검색된 정보 없음)"

        # Plan: decide action
        yield "thinking", {
            "step": f"계획 (반복 {iterations}/{MAX_ITERATIONS})",
            "detail": f"검색된 청크 {len(all_chunks)}개, 행동 결정 중..."
        }

        plan_prompt = PLANNER_PROMPT.format(context=context_so_far[:2000])
        plan_content, _, _ = await ask_json(
            system_prompt=plan_prompt,
            user_prompt=question,
            model=model,
        )

        try:
            plan = json.loads(plan_content)
            action = plan.get("action", "answer")
            search_query = plan.get("query", question)
            reason = plan.get("reason", "")
        except (json.JSONDecodeError, AttributeError):
            action = "search" if not all_chunks else "answer"
            search_query = question
            reason = "파싱 실패"

        if action == "answer":
            yield "thinking", {"step": "결정", "detail": f"정보 충분 → 답변 생성 ({reason})"}
            break

        # Search with the planned query
        if search_query in search_queries:
            # Avoid duplicate queries
            search_query = f"{search_query} 상세 정보"

        search_queries.append(search_query)

        yield "thinking", {
            "step": f"검색 {len(search_queries)}",
            "detail": f'"{search_query}" 검색 중...'
        }

        search_emb, _ = await embed_single(search_query)
        new_chunks = await _search_collections(
            search_query, search_emb, collection_names, top_k, model
        )

        # Merge new chunks (deduplicate)
        existing_texts = {c["text"][:100] for c in all_chunks}
        added = 0
        for chunk in new_chunks:
            if chunk["text"][:100] not in existing_texts:
                all_chunks.append(chunk)
                existing_texts.add(chunk["text"][:100])
                added += 1

        yield "thinking", {
            "step": f"검색 결과",
            "detail": f"새로운 청크 {added}개 추가 (총 {len(all_chunks)}개)"
        }

        # Grade: evaluate if we have enough
        if all_chunks:
            grade_content, _, _ = await ask_json(
                system_prompt=GRADER_PROMPT.format(
                    question=question,
                    context=format_context(all_chunks[:8])[:3000]
                ),
                user_prompt="위 문서들을 평가하세요.",
                model=model,
            )
            try:
                grade = json.loads(grade_content)
                grade_result = grade.get("grade", "partial")
                missing = grade.get("missing", "")
            except (json.JSONDecodeError, AttributeError):
                grade_result = "partial"
                missing = ""

            yield "thinking", {
                "step": "평가",
                "detail": f"{grade_result}" + (f" (부족: {missing})" if missing else "")
            }

            if grade_result == "sufficient":
                break

    # Step 3: Final rerank across ALL collected chunks (single unified scoring)
    if len(all_chunks) > 0:
        # Strip old rerank_scores before final rerank so all get fresh scores
        cleaned = [{k: v for k, v in c.items() if k != "rerank_score"} for c in all_chunks]
        final_chunks, _, _ = await rerank(question, cleaned, top_n=len(cleaned), model=model)
    else:
        final_chunks = all_chunks

    # Ensure every chunk has a score for display
    for c in final_chunks:
        if "rerank_score" not in c:
            c["rerank_score"] = c.get("rrf_score", c.get("score", 0))

    # Filter out 0% chunks — not relevant enough to show
    relevant_chunks = [c for c in final_chunks if c.get("rerank_score", 0) > 0]

    # Use top chunks for context, show relevant ones as sources
    context_chunks = relevant_chunks[:top_k]
    context = format_context(context_chunks)

    yield "sources", relevant_chunks

    system = (
        "다음 문서를 참고하여 질문에 답변하세요. "
        "문서 내용을 기반으로 자세하고 친절하게 답변하세요. "
        "문서에 직접적인 답이 없더라도 관련 내용이 있다면 참고하여 답변하세요."
    )

    async for token in stream_with_context(
        question, context, model,
        system_prompt=system,
        history=history,
    ):
        yield "token", token

    yield "done", None
