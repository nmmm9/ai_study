"""
qa_agent.py
───────────
경로 B: 직접 Q&A 모드

특정 정책에 대한 팩트 질문을 받아
RAG 검색 → 즉시 답변 생성 (프로필 수집 없음)
"""

from openai import OpenAI
from state import MultiAgentState
from tools.policy_loader import search_policies, search_all_policies, get_all_policy_titles

_client = OpenAI()

_SYSTEM = """\
당신은 청년정책 전문 AI입니다.
사용자의 질문에 검색된 정책 문서를 바탕으로 정확하고 간결하게 답변하세요.

## 응답 원칙
- 문서에 있는 내용만 사용 (추측·창작 금지)
- 수치(금액, 나이, 기간)는 정확하게 인용
- 중복 수혜 가능 여부는 근거 문서 기준으로 답변
- 정보가 없으면 "문서에서 확인되지 않습니다"라고 명시
- 마크다운으로 깔끔하게 작성

## 답변 형식
### 답변
(핵심 답변 1-3줄)

### 근거
- 정책명: 관련 조항 인용

### 참고 사항
(추가 확인이 필요한 사항, 공식 사이트 안내)
"""


def _extract_keywords(query: str) -> list[str]:
    """질문에서 검색 키워드를 추출합니다."""
    # 자주 쓰이는 정책명 키워드 우선
    policy_keywords = [
        "청년도약계좌", "청년희망적금", "청년내일채움공제", "국가장학금",
        "근로장학금", "청년월세", "청년주택드림", "국민취업지원",
        "미래내일", "청년성장", "주거급여",
    ]
    found = [kw for kw in policy_keywords if kw in query]

    # 일반 키워드 추가
    general = []
    for word in ["장학금", "취업", "주거", "월세", "적금", "계좌", "청약",
                 "지원금", "대출", "인턴", "일자리"]:
        if word in query:
            general.append(word)

    keywords = found + general
    return keywords if keywords else [query[:20]]


def qa_search_node(state: MultiAgentState) -> dict:
    """질문 키워드로 관련 정책을 검색합니다."""
    query    = state.get("user_query", "")
    keywords = _extract_keywords(query)

    results = search_policies(keywords=keywords, category="", top_k=6)
    if not results:
        results = search_all_policies(keywords=keywords, top_k=6)

    summary = f"{len(results)}개 정책 검색됨"
    print(f"[qa_search_node] {summary} | 키워드: {keywords[:3]}")

    trace = list(state.get("execution_trace", []))
    trace.append({"node": "qa_search_node", "summary": summary})

    return {
        "qa_search_results": results,
        "execution_trace":   trace,
    }


def qa_answer_node(state: MultiAgentState) -> dict:
    """검색 결과를 바탕으로 즉시 답변을 생성합니다."""
    query   = state.get("user_query", "")
    results = state.get("qa_search_results", [])

    # 컨텍스트 구성
    context = f"## 사용자 질문\n{query}\n\n"
    if results:
        context += f"## 검색된 정책 문서 ({len(results)}개)\n"
        for doc in results:
            context += f"\n### {doc['title']}\n{doc['content'][:2000]}\n"
    else:
        titles   = get_all_policy_titles()
        context += "## 보유 정책 목록\n" + "\n".join(f"- {t}" for t in titles)
        context += "\n\n(검색 결과 없음 — 위 목록 참고하여 답변)"

    resp = _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": context},
        ],
        max_tokens=1200,
    )

    answer = resp.choices[0].message.content or ""
    print(f"[qa_answer_node] 답변 생성 완료 ({len(answer)}자)")

    trace = list(state.get("execution_trace", []))
    trace.append({"node": "qa_answer_node", "summary": "직접 답변 생성 완료"})

    return {
        "qa_answer":       answer,
        "final_answer":    answer,   # app.py가 final_answer를 읽으므로 동기화
        "execution_trace": trace,
    }
