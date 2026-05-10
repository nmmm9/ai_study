"""
specialist.py
─────────────
전문 에이전트 4종

각 에이전트는 자기 도메인에 특화된 정책만 검색·분석합니다.
오케스트레이터가 선택하지 않은 에이전트는 즉시 종료합니다.
"""

from openai import OpenAI
from state import MultiAgentState
from tools.policy_loader import search_policies, get_all_policy_titles

_client = OpenAI()

_BASE_SYSTEM = """\
당신은 청년정책 {domain} 전문 AI입니다.
사용자 조건에 맞는 {domain} 관련 정책만 분석하여 마크다운으로 답변하세요.

## 응답 형식
### {domain} 맞춤 정책
- **정책명**: 신청 자격 / 혜택 요약 (1-2줄)

### 핵심 추천
가장 우선 신청할 정책과 이유

### 유의사항
나이·지역 제한, 신청 기간 등

원칙: 문서에 없는 내용 추측 금지. 조건 불명확하면 "확인 필요" 표시.
"""

_DOMAIN_CONFIG = {
    "scholarship": {
        "domain":    "장학금·교육비",
        "category":  "장학금",
        "keywords":  ["장학금", "학자금", "등록금", "교육비", "대학생"],
    },
    "employment": {
        "domain":    "취업·일자리",
        "category":  "취업",
        "keywords":  ["취업", "일자리", "고용", "인턴", "채용", "구직"],
    },
    "housing": {
        "domain":    "주거·월세",
        "category":  "주거",
        "keywords":  ["주거", "월세", "전세", "청약", "주택", "임대"],
    },
    "finance": {
        "domain":    "금융·적금",
        "category":  "금융",
        "keywords":  ["적금", "계좌", "금융", "저축", "도약", "대출"],
    },
}


def _run_specialist(state: MultiAgentState, agent_key: str, result_key: str) -> dict:
    """공통 전문 에이전트 로직."""
    selected = state.get("selected_agents", [])
    trace    = list(state.get("execution_trace", []))

    # 선택되지 않은 에이전트는 건너뜀
    if agent_key not in selected:
        trace.append({"node": f"{agent_key}_node", "summary": "선택 안 됨 — 건너뜀"})
        return {"execution_trace": trace}

    cfg     = _DOMAIN_CONFIG[agent_key]
    profile = state.get("user_profile", {})
    age     = profile.get("age", 0)
    region  = profile.get("region", "")

    # 키워드에 나이·지역 추가
    keywords = list(cfg["keywords"])
    if region:
        keywords.append(region)

    # 정책 검색
    results = search_policies(keywords=keywords, category=cfg["category"], top_k=5)
    if not results:
        results = search_policies(keywords=keywords, category="", top_k=5)

    # 컨텍스트 구성
    context = f"사용자: 나이={age}세, 지역={region}\n\n"
    if results:
        context += f"검색된 {cfg['domain']} 정책 ({len(results)}개):\n"
        for doc in results:
            context += f"\n### {doc['title']}\n{doc['content'][:1500]}\n"
    else:
        titles   = get_all_policy_titles()
        context += "검색 결과 없음. 보유 정책:\n" + "\n".join(f"- {t}" for t in titles)

    system = _BASE_SYSTEM.format(domain=cfg["domain"])

    resp = _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": context},
        ],
        max_tokens=1000,
    )

    result = resp.choices[0].message.content or ""
    summary = f"{len(results)}개 정책 분석 완료"
    print(f"[{agent_key}_node] {summary}")

    trace.append({"node": f"{agent_key}_node", "summary": summary})
    return {result_key: result, "execution_trace": trace}


# ── 4개 전문 노드 ────────────────────────────────────────────────

def scholarship_node(state: MultiAgentState) -> dict:
    return _run_specialist(state, "scholarship", "scholarship_result")


def employment_node(state: MultiAgentState) -> dict:
    return _run_specialist(state, "employment", "employment_result")


def housing_node(state: MultiAgentState) -> dict:
    return _run_specialist(state, "housing", "housing_result")


def finance_node(state: MultiAgentState) -> dict:
    return _run_specialist(state, "finance", "finance_result")
