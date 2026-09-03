"""
diagnosis_node.py — 대화형 지원 자격 모의 진단 (Feature 5)

사용자와 스무고개 방식으로 대화하며
- 중위소득 계산
- 무주택 기간, 가점 항목 확인
- 최종 지원 가능 여부 및 합격 확률(%) 예측
"""

from openai import OpenAI
from backend.prompts.diagnosis import SYSTEM as _SYSTEM
from backend.state import FinalRAGState

_client = OpenAI()


def diagnosis_node(state: FinalRAGState) -> dict:
    question  = state.get("rewritten_question") or state.get("question", "")
    documents = state.get("documents", [])

    # 수집된 정책 문서가 있으면 컨텍스트로 활용
    doc_ctx = ""
    if documents:
        doc_ctx = "\n\n".join(
            f"[{d['title']}]\n{d['content'][:800]}" for d in documents[:3]
        )

    user_content = question
    if doc_ctx:
        user_content += f"\n\n참고 정책 문서:\n{doc_ctx}"

    resp = _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": user_content},
        ],
        max_tokens=1200,
    )
    answer = resp.choices[0].message.content or ""

    trace = list(state.get("execution_trace", []))
    trace.append({"node": "diagnosis_node", "summary": "자가진단 실행"})

    return {"answer": answer, "execution_trace": trace}
