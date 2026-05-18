"""
generate_node.py
────────────────
검색된 문서를 기반으로 최종 답변을 생성합니다.
"""

from openai import OpenAI
from state import AgenticRAGState

_client = OpenAI()

_SYSTEM = """\
당신은 청년정책 전문 AI입니다.
제공된 정책 문서를 바탕으로 정확하고 유용한 답변을 작성하세요.

## 핵심 원칙
- 문서에 있는 내용만 사용 (추측·창작 금지)
- 문서에 없는 내용은 "문서에서 확인되지 않습니다"라고 명시
- "당신은" 같은 어색한 표현 금지 — 자연스러운 한국어로 작성
- 마크다운으로 깔끔하게 작성

## 반드시 포함할 정보 (문서에 있을 경우)
- 자격 조건: 나이 범위, 소득 분위, 학점, 재직 여부 등
- 지원 금액: 월 지원액, 총 지원액, 한도 등 구체적 수치
- 신청 기간 및 방법: 접수 일정, 신청처
- 중복 수혜: 다른 정책과 동시 수혜 가능 여부 (문서 근거 명시)

## 답변 형식
### 답변
(핵심 내용을 2~4문장으로 명확하게)

### 자격 조건
- 나이: / 소득: / 기타 조건:

### 지원 내용
- 금액: / 기간: / 방식:

### 관련 정책
- 정책명: 핵심 내용 한 줄 요약

### 참고
(공식 사이트 또는 추가 확인 권고)
"""


def generate_node(state: AgenticRAGState) -> dict:
    """최종 답변을 생성합니다."""
    question  = state.get("question", "")
    documents = state.get("documents", [])
    retry     = state.get("retry_count", 0)

    context = f"## 질문\n{question}\n\n"
    if documents:
        context += f"## 검색된 정책 문서 ({len(documents)}개)\n"
        for doc in documents:
            context += f"\n### {doc['title']}\n{doc['content'][:1500]}\n"
    else:
        context += "## 참고\n검색된 문서가 없습니다. 일반 지식으로 답변합니다.\n"

    resp = _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": context},
        ],
        max_tokens=1200,
    )
    answer = resp.choices[0].message.content or ""
    print(f"[generate_node] 답변 생성 완료 ({len(answer)}자) | 재시도={retry}회")

    trace = list(state.get("execution_trace", []))
    trace.append({
        "node":    "generate_node",
        "summary": f"답변 생성 완료 (문서 {len(documents)}개 활용, 재검색 {retry}회)",
    })

    return {
        "answer":          answer,
        "execution_trace": trace,
    }
