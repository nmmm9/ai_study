"""Self-RAG Pipeline — Self-reflective retrieval-augmented generation.

The LLM decides:
1. Whether retrieval is needed
2. Generates an answer with retrieved context
3. Self-evaluates the answer quality
4. If quality is low, regenerates with stricter instructions
"""

import json

from services.embedding_service import embed_single
from services import vector_store
from services.llm_service import ask_with_context, ask_json
from services.rag_utils import SYSTEM_PROMPT, format_context, chunks_from_results

NEED_RETRIEVAL_SYSTEM = """사용자의 질문이 외부 문서 검색이 필요한지 판단하세요.

판단 기준:
- 특정 사실, 데이터, 정의를 묻는 질문 → 검색 필요
- 일반적인 인사, 의견 요청 → 검색 불필요

반드시 다음 JSON 형식으로만 응답하세요:
{"need_retrieval": true, "reason": "판단 이유"}"""

EVALUATE_SYSTEM = """생성된 답변의 품질을 평가하세요.

평가 기준:
- 문서 컨텍스트에 근거한 답변인가?
- 질문에 정확히 답하고 있는가?
- 할루시네이션(문서에 없는 내용 날조)이 있는가?

반드시 다음 JSON 형식으로만 응답하세요:
{"score": 8, "is_grounded": true, "feedback": "평가 내용"}"""




async def run_self_rag(
    question: str,
    collection_name: str,
    top_k: int = 5,
    model: str = "gpt-4o-mini",
) -> dict:
    """Self-RAG: judge retrieval → retrieve → generate → self-evaluate → (re-generate)."""
    steps = []
    total_cost = 0.0

    # Step 1: Judge if retrieval is needed
    judge_content, judge_ms, judge_cost = await ask_json(
        system_prompt=NEED_RETRIEVAL_SYSTEM,
        user_prompt=question,
        model=model,
    )
    total_cost += judge_cost

    try:
        judge_data = json.loads(judge_content)
        need_retrieval = judge_data.get("need_retrieval", True)
        judge_reason = judge_data.get("reason", "")
    except (json.JSONDecodeError, AttributeError):
        need_retrieval = True
        judge_reason = "판단 실패, 기본값: 검색 수행"

    steps.append({
        "name": "judge", "label": "검색 필요성 판단",
        "time_ms": judge_ms,
        "detail": f"{'검색 필요' if need_retrieval else '검색 불필요'}: {judge_reason}",
    })

    chunks = []
    embed_ms = 0
    search_ms = 0

    if need_retrieval:
        # Step 2: Embed + Search
        query_emb, embed_ms = await embed_single(question)
        steps.append({"name": "embed", "label": "질문 임베딩", "time_ms": embed_ms})

        results, search_ms = vector_store.search(collection_name, query_emb, top_k)
        chunks = chunks_from_results(results)
        steps.append({
            "name": "search", "label": "벡터 검색",
            "time_ms": search_ms, "detail": f"{len(chunks)}개 청크",
        })

    # Step 3: Generate answer
    context = format_context(chunks) if chunks else "검색된 문서가 없습니다."
    llm_result = await ask_with_context(
        question, context, model, system_prompt=SYSTEM_PROMPT
    )
    total_cost += llm_result.cost_usd
    steps.append({"name": "generate", "label": "답변 생성", "time_ms": llm_result.time_ms})

    answer = llm_result.answer
    gen_ms = llm_result.time_ms

    # Step 4: Self-evaluate
    eval_prompt = (
        f"질문: {question}\n\n"
        f"컨텍스트:\n{context}\n\n"
        f"생성된 답변:\n{answer}"
    )
    eval_content, eval_ms, eval_cost = await ask_json(
        system_prompt=EVALUATE_SYSTEM,
        user_prompt=eval_prompt,
        model=model,
    )
    total_cost += eval_cost

    try:
        eval_data = json.loads(eval_content)
        eval_score = eval_data.get("score", 7)
        is_grounded = eval_data.get("is_grounded", True)
        feedback = eval_data.get("feedback", "")
    except (json.JSONDecodeError, AttributeError):
        eval_score = 7
        is_grounded = True
        feedback = "평가 파싱 실패"

    steps.append({
        "name": "evaluate", "label": "자체 평가",
        "time_ms": eval_ms,
        "detail": f"점수: {eval_score}/10, 근거 기반: {'Yes' if is_grounded else 'No'}",
    })

    # Step 5: Re-generate if score is low
    regen_ms = 0
    if eval_score < 6 or not is_grounded:
        strict_prompt = (
            "이전 답변이 품질 기준에 미달했습니다. "
            f"피드백: {feedback}\n\n"
            "다음 문서만 근거로 하여 더 정확한 답변을 작성하세요. "
            "문서에 없는 내용은 절대 포함하지 마세요."
        )
        regen_result = await ask_with_context(
            question, context, model, system_prompt=strict_prompt
        )
        total_cost += regen_result.cost_usd
        answer = regen_result.answer
        regen_ms = regen_result.time_ms
        steps.append({
            "name": "regenerate", "label": "재생성",
            "time_ms": regen_ms, "detail": f"피드백 반영 재생성",
        })

    total_ms = judge_ms + embed_ms + search_ms + gen_ms + eval_ms + regen_ms

    return {
        "answer": answer,
        "sources": chunks,
        "steps": steps,
        "timing": {
            "judge_ms": judge_ms, "embed_ms": embed_ms, "search_ms": search_ms,
            "generate_ms": gen_ms, "evaluate_ms": eval_ms, "regenerate_ms": regen_ms,
            "total_ms": total_ms,
        },
        "cost_usd": round(total_cost, 6),
        "total_tokens": llm_result.total_tokens,
        "mode": "self_rag",
        "self_eval": {"score": eval_score, "grounded": is_grounded, "feedback": feedback},
    }
