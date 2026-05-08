"""Adaptive RAG — Routes queries to different pipelines based on complexity.

Classifies question complexity:
- SIMPLE: basic RAG (fast, cheap)
- MODERATE: HyDE or Rerank
- COMPLEX: Advanced RAG (HyDE + Rerank)
"""

import json

from services.llm_service import ask_json
from services.basic_pipeline import run_basic_rag
from services.advanced_pipeline import run_hyde_rag, run_rerank_rag, run_advanced_rag

CLASSIFY_SYSTEM = """질문의 복잡도를 분류하세요.

분류 기준:
- SIMPLE: 단순 사실/정의 질문 (예: "X란 무엇인가?", "X의 정의는?")
- MODERATE: 비교, 설명, 원리 질문 (예: "X와 Y의 차이는?", "X가 왜 중요한가?")
- COMPLEX: 다단계 추론, 종합 분석 질문 (예: "X를 적용할 때 고려사항과 해결방법은?")

반드시 다음 JSON 형식으로만 응답하세요:
{"complexity": "SIMPLE", "reason": "분류 이유", "recommended_pipeline": "basic"}"""

# Mapping: complexity → pipeline function
_PIPELINE_MAP = {
    "SIMPLE": ("basic", run_basic_rag),
    "MODERATE": ("rerank", run_rerank_rag),
    "COMPLEX": ("advanced", run_advanced_rag),
}


async def run_adaptive_rag(
    question: str,
    collection_name: str,
    top_k: int = 5,
    model: str = "gpt-4o-mini",
) -> dict:
    """Adaptive RAG: classify complexity → route to appropriate pipeline."""

    # Step 1: Classify question complexity
    classify_content, classify_ms, classify_cost = await ask_json(
        system_prompt=CLASSIFY_SYSTEM,
        user_prompt=question,
        model=model,
    )

    try:
        data = json.loads(classify_content)
        complexity = data.get("complexity", "MODERATE")
        classify_reason = data.get("reason", "")
    except (json.JSONDecodeError, AttributeError):
        complexity = "MODERATE"
        classify_reason = "분류 실패, 기본값 사용"

    if complexity not in _PIPELINE_MAP:
        complexity = "MODERATE"

    pipeline_name, pipeline_fn = _PIPELINE_MAP[complexity]

    # Step 2: Run selected pipeline
    result = await pipeline_fn(question, collection_name, top_k, model)

    # Prepend classification step
    classify_step = {
        "name": "classify",
        "label": "복잡도 분류",
        "time_ms": classify_ms,
        "detail": f"{complexity} → {pipeline_name} 파이프라인 선택",
    }
    result["steps"] = [classify_step] + result["steps"]
    result["timing"]["classify_ms"] = classify_ms
    result["timing"]["total_ms"] += classify_ms
    result["cost_usd"] = round(result["cost_usd"] + classify_cost, 6)
    result["mode"] = "adaptive"
    result["selected_pipeline"] = pipeline_name
    result["complexity"] = complexity
    result["classify_reason"] = classify_reason

    return result
