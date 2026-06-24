"""
generate_node.py — 최종 답변 생성 (BACKEND 계층)

도구별 출력 형식:
  search_policy     → 정책 상세 정보
  compare_policies  → 두 정책 비교표
  list_by_category  → 정책 목록 요약
"""

from openai import OpenAI
from backend.state import FinalRAGState

_client = OpenAI()

_SYSTEM_SEARCH = """\
당신은 청년정책 전문 AI 가이드입니다.
제공된 정책 문서가 있으면 문서를 우선 활용하고,
문서가 없으면 보유한 일반 지식으로 성실하게 답변하세요.

## 답변 스타일
- 친절하고 명확하게, 청년이 읽기 쉽게 작성
- 번호(1. 2. 3.)와 소항목(① ② ③)으로 구조화
- 숫자·조건·금액은 구체적으로 명시 (예: 만 19세~34세, 월 최대 50만 원)
- 중요한 주의사항은 "⚠️ 주의:" 로 강조
- 표(table)를 적극 활용해 조건·혜택 비교
- 내용이 없는 항목은 생략 (빈 항목 출력 금지)
- 일반 지식으로 답변할 때는 마지막에 "※ 정확한 최신 정보는 온통청년(www.youthcenter.go.kr)에서 확인하세요." 추가

## 답변 구성 (해당 내용 있을 때만 포함)
### 1. 개요
(정책 목적과 핵심 특징 2~3문장)

### 2. 가입 대상 및 조건
(나이·소득·기타 조건을 ① ② ③ 소항목으로 구체적으로)

### 3. 지원 혜택
(금액·기간·금리 등을 표 또는 목록으로 상세히)

### 4. 신청 방법
(기간·방법·절차를 단계별로)

### 5. 신청 링크
가장 최신·가까운 신청 기간과 공식 신청 링크를 반드시 안내하세요.
- 해당 정책의 공식 신청 사이트 URL 포함
- 신청 기간이 알려져 있으면 날짜 명시
- 신청 기간이 불분명하면 아래 주요 포털 링크 제공:
  - 온통청년: https://www.youthcenter.go.kr
  - 복지로: https://www.bokjiro.go.kr
  - 정부24: https://www.gov.kr
"""

_SYSTEM_COMPARE = """\
당신은 청년정책 비교 전문 AI입니다.
두 정책의 핵심 차이점을 비교표로 명확하게 정리해주세요.

## 형식
### 비교 요약
(어떤 경우에 어떤 정책이 유리한지 2~3문장)

### 비교표
| 항목 | [정책A 이름] | [정책B 이름] |
|------|-------------|-------------|
| 대상 나이 | | |
| 소득 조건 | | |
| 지원 금액 | | |
| 기간 | | |
| 중복 수혜 | | |

### 결론
(케이스별 추천)
"""

_SYSTEM_LIST = """\
당신은 청년정책 안내 AI입니다.
제공된 정책 목록을 정리하고 각 정책의 핵심을 한 줄로 요약해주세요.

## 형식
### [카테고리명] 정책 목록 (N개)

| 정책명 | 핵심 내용 | 대상 |
|--------|----------|------|

### 대표 추천 정책
(2~3개 강조)
"""


_SYSTEM_ELIGIBILITY = """\
당신은 청년정책 자격 검증 전문 AI입니다.
제공된 정책 문서와 사용자 정보를 비교하여 신청 가능 여부를 판단하세요.

## 답변 형식
### 검증 결과
**[신청 가능 / 신청 불가 / 조건부 가능]**

### 판단 근거
(정책 조건과 사용자 정보를 항목별로 대조)

| 조건 항목 | 정책 요건 | 사용자 정보 | 충족 여부 |
|----------|---------|-----------|---------|

### 주의 사항
(추가 확인이 필요한 조건 안내)

### 신청 방법
(신청 가능하다면 다음 단계 안내)
"""

_SYSTEM_RECOMMEND = """\
당신은 청년정책 맞춤 추천 전문 AI입니다.
사용자 프로필을 분석하여 가장 혜택이 큰 정책을 우선순위로 추천하세요.

## 답변 형식
### 맞춤 추천 정책 (상위 N개)

| 순위 | 정책명 | 핵심 혜택 | 추천 이유 |
|-----|--------|---------|---------|

### 상세 추천 이유
(각 정책이 사용자에게 유리한 이유를 구체적으로)

### 신청 우선순위
(마감이 임박하거나 혜택이 큰 순서로 안내)
"""

_SYSTEM_APPLICATION = """\
당신은 청년정책 신청 절차 안내 전문 AI입니다.
신청 방법, 필요 서류, 신청 링크를 단계별로 명확하게 안내하세요.

## 답변 형식
### 신청 방법

**신청 기간:** (알 수 있는 경우 명시)
**신청 방법:** 온라인 / 방문 / 우편

### 필요 서류
① (서류명) — (용도)
② ...

### 신청 단계
1단계 → 2단계 → 3단계 ...

### 신청 링크
- 공식 신청 사이트: (URL)
- 문의처: (기관명, 전화번호)
"""

_SYSTEM_DEADLINES = """\
당신은 청년정책 마감 임박 알림 전문 AI입니다.
마감이 임박한 정책들을 D-Day 순서로 정리하고 긴급도를 강조하세요.

## 답변 형식
### 마감 임박 정책 목록

| 정책명 | 마감일 | D-Day | 지원 내용 |
|--------|--------|-------|---------|

### 긴급 추천
(가장 빨리 신청해야 할 정책 1~2개 강조)

※ 정확한 마감일은 각 정책 공식 사이트에서 반드시 확인하세요.
"""


def generate_node(state: FinalRAGState) -> dict:
    question  = state.get("question", "")
    documents = state.get("documents", [])
    tool_name = state.get("tool_name", "search_policies")
    tool_args = state.get("tool_args", {})
    retry     = state.get("retry_count", 0)

    if tool_name == "compare_policies":
        system = _SYSTEM_COMPARE
    elif tool_name == "list_by_category":
        system = _SYSTEM_LIST
    elif tool_name == "check_eligibility":
        system = _SYSTEM_ELIGIBILITY
    elif tool_name == "recommend_policies":
        system = _SYSTEM_RECOMMEND
    elif tool_name == "get_application_method":
        system = _SYSTEM_APPLICATION
    elif tool_name == "get_upcoming_deadlines":
        system = _SYSTEM_DEADLINES
    else:
        system = _SYSTEM_SEARCH

    context = f"## 질문\n{question}\n\n"

    if tool_args:
        relevant = {k: v for k, v in tool_args.items() if v and k not in ("top_k", "keywords", "query")}
        if relevant:
            context += f"## 사용자 입력 조건\n{relevant}\n\n"

    if documents:
        context += f"## 검색된 정책 문서 ({len(documents)}개)\n"
        for doc in documents:
            context += f"\n### {doc['title']}\n{doc['content'][:1500]}\n"
    else:
        context += "## 참고\n검색된 문서가 없습니다. 일반 지식으로 답변합니다.\n"

    resp = _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": context},
        ],
        max_tokens=1500,
    )
    answer = resp.choices[0].message.content or ""
    print(f"[generate_node] {len(answer)}자 | 도구={tool_name} | 재시도={retry}회")

    trace = list(state.get("execution_trace", []))
    trace.append({
        "node":    "generate_node",
        "summary": f"답변 생성 완료 (문서 {len(documents)}개 활용, 재검색 {retry}회)",
    })
    return {"answer": answer, "execution_trace": trace}
