"""
rewrite_node.py — 검색 실패 시 쿼리 재작성 (BACKEND 계층 / week10 Self-Correction)
"""

from openai import OpenAI
from backend.state import FinalRAGState

_client = OpenAI()

_SYSTEM = """\
당신은 검색 쿼리 최적화 전문가입니다.
기존 질문으로 검색했지만 관련 문서를 찾지 못했습니다.
같은 의도를 더 잘 검색할 수 있도록 쿼리를 재작성하세요.

원칙:
- 더 구체적인 정책명이나 키워드 사용
- 동의어·유사어 추가 (예: "월세" → "주거비 지원", "임대료")
- 핵심 단어만 남기고 짧게
- 재작성된 쿼리만 출력 (설명 없이)
"""


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
    print(f"[rewrite_node] '{previous}' → '{rewritten}'")

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
        "execution_trace":    trace,
    }
