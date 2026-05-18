"""
grade_node.py
─────────────
검색된 문서가 질문과 관련 있는지 평가합니다.

관련 없으면 → rewrite_node로 이동 (쿼리 재작성 후 재검색)
관련 있으면 → generate_node로 이동 (최종 답변 생성)
"""

from openai import OpenAI
from state import AgenticRAGState

_client = OpenAI()

_SYSTEM = """\
당신은 문서 관련성 평가자입니다.
사용자 질문과 검색된 문서를 보고, 문서가 질문에 답하기에 충분히 관련 있는지 판단하세요.

반드시 아래 중 하나만 응답하세요:
- relevant    (문서가 질문과 관련 있고 답변에 충분히 활용 가능)
- not_relevant (문서가 질문과 관련 없거나 정보가 부족)
"""


def grade_docs_node(state: AgenticRAGState) -> dict:
    """검색 결과의 관련성을 평가합니다."""
    question  = state.get("rewritten_question") or state.get("question", "")
    documents = state.get("documents", [])

    if not documents:
        grade = "not_relevant"
        print("[grade_docs_node] 문서 없음 → not_relevant")
    else:
        doc_preview = "\n\n".join(
            f"[{d['title']}]\n{d['content'][:400]}" for d in documents[:4]
        )
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user",   "content": f"질문: {question}\n\n검색된 문서:\n{doc_preview}"},
            ],
            max_tokens=10,
            temperature=0,
        )
        raw   = (resp.choices[0].message.content or "").strip().lower()
        grade = "relevant" if "relevant" in raw and "not" not in raw else "not_relevant"
        print(f"[grade_docs_node] 평가 결과: {grade}")

    trace = list(state.get("execution_trace", []))
    trace.append({
        "node":    "grade_docs_node",
        "summary": f"관련성 평가: {grade} (문서 {len(documents)}개)",
    })

    return {
        "grade":           grade,
        "execution_trace": trace,
    }


def route_grade(state: AgenticRAGState) -> str:
    """관련성 및 재시도 횟수에 따라 분기."""
    grade       = state.get("grade", "not_relevant")
    retry_count = state.get("retry_count", 0)

    if grade == "relevant":
        return "generate"
    if retry_count >= 2:
        print("[grade_docs_node] 최대 재시도 도달 → 현재 문서로 생성")
        return "generate"
    return "rewrite"
