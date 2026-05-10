"""
orchestrator.py
───────────────
오케스트레이터 에이전트

사용자 프로필을 보고 어떤 전문 에이전트를 실행할지 결정합니다.
"""

import json
from openai import OpenAI
from state import MultiAgentState

_client = OpenAI()

_SYSTEM = """\
당신은 청년정책 멀티에이전트 시스템의 오케스트레이터입니다.
사용자 프로필을 분석하여 실행할 전문 에이전트를 선택하세요.

전문 에이전트 목록:
- scholarship : 장학금·교육비 지원 정책 전문
- employment  : 취업·일자리·인턴 지원 정책 전문
- housing     : 주거·월세·청약 지원 정책 전문
- finance     : 적금·계좌·금융 지원 정책 전문

규칙:
- 사용자 관심분야에 해당하는 에이전트는 반드시 포함
- 나이·상황을 고려해 추가 에이전트도 포함 가능
- 최소 1개, 최대 4개 선택

아래 JSON 형식으로만 응답:
{
  "selected": ["scholarship", "employment"],
  "reasons": {
    "scholarship": "대학생이므로 장학금 검색 필요",
    "employment": "구직 중이므로 취업 지원 검색 필요"
  }
}
"""


def orchestrator_node(state: MultiAgentState) -> dict:
    """프로필 기반으로 실행할 전문 에이전트를 결정합니다."""
    profile = state.get("user_profile", {})

    prompt = f"""
사용자 프로필:
- 나이: {profile.get('age')}세
- 지역: {profile.get('region')}
- 상황: {profile.get('employment')}
- 관심분야: {profile.get('interests', [])}

어떤 전문 에이전트를 실행해야 할까요?
"""

    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=300,
    )

    raw = resp.choices[0].message.content or "{}"
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.split("```")[0]

    try:
        data     = json.loads(raw.strip())
        selected = data.get("selected", ["employment"])
        reasons  = data.get("reasons", {})
    except Exception:
        interests = profile.get("interests", [])
        selected  = _fallback_selection(interests)
        reasons   = {}

    print(f"[orchestrator] 선택된 에이전트: {selected}")

    trace = list(state.get("execution_trace", []))
    trace.append({
        "node":    "orchestrator_node",
        "summary": f"에이전트 선택: {', '.join(selected)}",
    })

    return {
        "selected_agents": selected,
        "agent_reasons":   reasons,
        "execution_trace": trace,
    }


def _fallback_selection(interests: list) -> list:
    mapping = {
        "장학금": "scholarship",
        "취업":   "employment",
        "주거":   "housing",
        "금융":   "finance",
    }
    selected = [mapping[i] for i in interests if i in mapping]
    return selected or ["employment"]
