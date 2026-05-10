"""
synthesizer.py
──────────────
종합 에이전트

모든 전문 에이전트의 결과를 받아 하나의 통합 답변을 생성합니다.
"""

from openai import OpenAI
from state import MultiAgentState

_client = OpenAI()

_SYSTEM = """\
당신은 청년정책 AI 종합 상담사입니다.
여러 전문 에이전트가 분석한 결과를 하나의 명확한 답변으로 통합하세요.

## 응답 형식 (마크다운)

### 📊 분석 요약
(몇 개 분야에서 몇 개 정책을 찾았는지 한 줄 요약)

### 🏆 최우선 추천 정책 (TOP 3)
1. **정책명** — 이유 (한 줄)
2. **정책명** — 이유 (한 줄)
3. **정책명** — 이유 (한 줄)

### 📋 분야별 상세 안내
(각 전문 에이전트 결과를 분야별로 정리)

### 📌 신청 순서 제안
어떤 정책을 먼저 신청하면 좋을지 우선순위 제안

### 💡 추가 조언
중복 신청 가능 여부, 주의사항 등

원칙: 각 에이전트 결과에 없는 내용 추가 금지.
"""


def synthesizer_node(state: MultiAgentState) -> dict:
    """전문 에이전트 결과를 통합합니다."""
    profile  = state.get("user_profile", {})
    selected = state.get("selected_agents", [])

    # 결과 수집
    results_map = {
        "scholarship": ("장학금·교육비", state.get("scholarship_result", "")),
        "employment":  ("취업·일자리",   state.get("employment_result", "")),
        "housing":     ("주거·월세",     state.get("housing_result", "")),
        "finance":     ("금융·적금",     state.get("finance_result", "")),
    }

    context = f"""
사용자 프로필:
- 나이: {profile.get('age')}세
- 지역: {profile.get('region')}
- 상황: {profile.get('employment')}
- 관심: {profile.get('interests', [])}

분석된 전문 에이전트 결과:
"""
    for key in selected:
        label, result = results_map.get(key, ("", ""))
        if result:
            context += f"\n\n=== {label} 전문 에이전트 결과 ===\n{result}"

    if not any(results_map[k][1] for k in selected):
        context += "\n(분석 결과 없음)"

    resp = _client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": context},
        ],
        max_tokens=2000,
    )

    final_answer = resp.choices[0].message.content or ""
    print(f"[synthesizer_node] 통합 답변 생성 완료")

    trace = list(state.get("execution_trace", []))
    trace.append({
        "node":    "synthesizer_node",
        "summary": f"{len(selected)}개 에이전트 결과 통합 완료",
    })

    return {
        "final_answer":    final_answer,
        "execution_trace": trace,
    }
