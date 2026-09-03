"""
grade_docs_node.py — 검색 결과 관련성 평가 (BACKEND 계층)

변경 사항:
  - 이진(relevant/not_relevant) → 0~100 점수 기반 평가
  - 50점 이상: generate (부분 관련도 살려서 활용)
  - 50점 미만 + retry < 2: rewrite
  - 50점 미만 + retry >= 2: web_search fallback
  - 문서 미리보기 400자 → 2000자로 확장 (문서 전체 맥락 검토)
"""

from openai import OpenAI
from backend.logging_config import get_logger
from backend.prompts.grade import SYSTEM as _SYSTEM
from backend.state import FinalRAGState

logger = get_logger(__name__)

_client = OpenAI()

_THRESHOLD = 50  # 이 점수 이상이면 generate로 라우팅


def _parse_score(raw: str) -> int:
    """GPT 응답에서 점수 파싱. 실패 시 0 반환."""
    for line in raw.splitlines():
        if line.strip().upper().startswith("SCORE"):
            parts = line.split(":")
            if len(parts) >= 2:
                try:
                    return max(0, min(100, int(parts[1].strip())))
                except ValueError:
                    pass
    # 숫자만 있는 응답 fallback
    import re
    nums = re.findall(r"\b(\d{1,3})\b", raw)
    if nums:
        return max(0, min(100, int(nums[0])))
    return 0


def grade_docs_node(state: FinalRAGState) -> dict:
    question  = state.get("rewritten_question") or state.get("question", "")
    documents = state.get("documents", [])
    retry     = state.get("retry_count", 0)

    if not documents:
        score  = 0
        reason = "검색 결과 없음"
    else:
        # 문서 미리보기: 400자 → 2000자로 확장
        doc_preview = "\n\n".join(
            f"[문서 {i+1}: {d['title']}]\n{d['content'][:2000]}"
            for i, d in enumerate(documents[:5])
        )
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user",   "content": f"질문: {question}\n\n검색된 문서:\n{doc_preview}"},
            ],
            max_tokens=60,
            temperature=0,
        )
        raw    = (resp.choices[0].message.content or "").strip()
        score  = _parse_score(raw)
        reason = next(
            (l.split(":", 1)[1].strip() for l in raw.splitlines() if "REASON" in l.upper()),
            raw[:80],
        )

    grade = "relevant" if score >= _THRESHOLD else "not_relevant"
    logger.info(f"[grade_docs_node] score={score}/100 → {grade} | {reason[:60]}")

    # 마지막 tool_history 항목에 grade 결과 기록
    tool_history = list(state.get("tool_history", []))
    if tool_history:
        tool_history[-1]["grade"] = f"{score}점 → {grade}"

    trace = list(state.get("execution_trace", []))
    trace.append({
        "node":    "grade_docs_node",
        "summary": f"관련성 {score}점 → {grade} (문서 {len(documents)}개) | {reason[:40]}",
    })
    return {
        "grade":           grade,
        "grade_score":     score,
        "tool_history":    tool_history,
        "execution_trace": trace,
    }


def route_grade(state: FinalRAGState) -> str:
    grade = state.get("grade", "not_relevant")
    retry = state.get("retry_count", 0)

    if grade == "relevant":
        return "generate"
    if retry >= 2:
        return "web_search"   # 2회 실패 → Tavily fallback
    return "rewrite"
