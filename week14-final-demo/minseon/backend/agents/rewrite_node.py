"""
rewrite_node.py — 검색 실패 시 쿼리 재작성 (BACKEND 계층 / week10 Self-Correction)
"""

from openai import OpenAI
from backend.logging_config import get_logger
from backend.prompts.rewrite import SYSTEM as _SYSTEM
from backend.state import FinalRAGState

logger = get_logger(__name__)

_client = OpenAI()


def rewrite_node(state: FinalRAGState) -> dict:
    original = state.get("question", "")
    previous = state.get("rewritten_question", original)
    retry    = state.get("retry_count", 0)

    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"원본 질문: {original}\n이전 검색 쿼리: {previous}\n\n개선된 검색 쿼리:"},
        ],
        max_tokens=80,
        temperature=0.3,
    )
    rewritten = (resp.choices[0].message.content or previous).strip()
    logger.info(f"[rewrite_node] '{previous}' → '{rewritten}'")

    trace = list(state.get("execution_trace", []))
    trace.append({
        "node":    "rewrite_node",
        "summary": f"쿼리 재작성 (시도 {retry + 1}): {rewritten[:40]}",
    })
    return {
        "rewritten_question": rewritten,
        "retry_count":        retry + 1,
        "documents":          [],
        "tool_calls":         [],
        "tool_name":          "",
        "grade":              "",   # 이전 판정이 다음 라우팅을 오염시키지 않도록 초기화
        "grade_score":        0,
        "execution_trace":    trace,
    }
