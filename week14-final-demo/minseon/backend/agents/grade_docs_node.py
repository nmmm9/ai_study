"""
grade_docs_node.py — 검색 결과 관련성 평가 (BACKEND 계층)
"""

from openai import OpenAI
from backend.state import FinalRAGState

_client = OpenAI()

_SYSTEM = """\
당신은 문서 관련성 평가자입니다.
사용자 질문과 검색된 문서를 보고, 문서가 질문에 답하기에 충분히 관련 있는지 판단하세요.

반드시 아래 중 하나만 응답하세요:
- relevant    (문서가 질문과 관련 있고 답변에 활용 가능)
- not_relevant (문서가 질문과 관련 없거나 정보가 부족)
"""


def grade_docs_node(state: FinalRAGState) -> dict:
    question  = state.get("rewritten_question") or state.get("question", "")
    documents = state.get("documents", [])

    if not documents:
        grade = "not_relevant"
    else:
        doc_preview = "\n\n".join(
            f"[{d['title']}]\n{d['content'][:400]}" for d in documents[:4]
        )
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": f"질문: {question}\n\n검색된 문서:\n{doc_preview}"},
            ],
            max_tokens=10,
            temperature=0,
        )
        raw   = (resp.choices[0].message.content or "").strip().lower()
        grade = "relevant" if "relevant" in raw and "not" not in raw else "not_relevant"

    print(f"[grade_docs_node] {grade}")
    trace = list(state.get("execution_trace", []))
    trace.append({
        "node":    "grade_docs_node",
        "summary": f"관련성 평가: {grade} (문서 {len(documents)}개)",
    })
    return {"grade": grade, "execution_trace": trace}


def route_grade(state: FinalRAGState) -> str:
    grade = state.get("grade", "not_relevant")
    retry = state.get("retry_count", 0)
    if grade == "relevant":
        return "generate"
    if retry >= 2:
        return "generate"
    return "rewrite"
