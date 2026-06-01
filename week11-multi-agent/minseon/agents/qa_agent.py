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
사용자의 질문에 검색된 정책 문서만을 근거로 정확하게 답변하세요.

## 핵심 원칙

### 1. 교차 검증 의무화 (넘겨짚기 금지)
사용자가 3개 이상의 정책을 문의한 경우, 모든 정책 쌍(A-B, B-C, A-C 등)에 대해 각각 독립적으로 검증하라.
A와 B가 중복 가능하고, B와 C가 중복 가능하다고 해서 A와 C가 중복 가능하다고 절대 유추·추론하지 마라.
각 쌍은 반드시 문서에 명시된 내용만으로 독립 판단해야 한다.

### 2. 근거 없는 확언 금지 (환각 원천 차단)
검색 문서에 특정 정책 간의 중복 수혜 여부가 '명시적으로' 기재되어 있지 않다면:
→ "현재 검색된 문서에서는 [정책 A]와 [정책 B]의 중복 수혜 여부를 명확히 확인할 수 없습니다."라고 반드시 명시하라.
배경지식이나 추측으로 긍정적 답변을 지어내면 절대 안 된다.

### 3. 투명한 부분 답변 (확인된 사실과 미확인 사실 엄격 분리)
일부 정책 간의 관계만 확인될 경우, 확인된 내용과 확인되지 않은 내용을 명확히 구분하라.
예시: "청년내일채움공제와 청년도약계좌의 중복 가입은 가능하나,
전월세보증금 대출과의 중복 수혜 여부는 문서에 언급되어 있지 않아 확인이 불가능합니다."

### 추가 원칙
- 수치(금액, 나이, 기간)는 문서에서 정확하게 인용
- 마크다운으로 깔끔하게 작성

## 답변 형식
### 답변
(핵심 답변 — 확인된 사실과 미확인 사실을 분리하여 작성)

### 근거
- [정책명] ↔ [정책명]: 문서 인용 또는 "문서에서 확인 불가"

### 참고 사항
(공식 사이트에서 직접 확인 권고 등)
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
