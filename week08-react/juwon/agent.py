"""
agent.py - 8주차 ReAct + Plan-and-Execute Agent

[전체 흐름]
Phase 1 - Plan:    AI가 사용자 질문을 분석해 단계별 실행 계획 수립
Phase 2 - Execute: ReAct 루프로 계획을 따라 반복 실행
                   Thought(생각) → Action(도구 호출) → Observation(결과 확인) → 반복
Phase 3 - Output:  수집된 모든 데이터를 HTML 보고서로 생성
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOLS, execute_tool

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY", "").strip().strip('\ufeff')
client = OpenAI(api_key=api_key)


# ─────────────────────────────────────────────
# 시스템 프롬프트
# ─────────────────────────────────────────────

PLAN_SYSTEM = """당신은 여행 계획 전문가입니다.
사용자의 여행 요청을 분석해서 실행 계획을 JSON 형태로 작성하세요.

반드시 다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{
  "city": "여행지 도시명 (한글)",
  "days": 여행 일수 (숫자),
  "accommodation_type": "저렴 또는 중급 또는 고급",
  "meal_budget": "절약 또는 보통 또는 여유",
  "transport": "대중교통 또는 렌트카 또는 택시",
  "steps": [
    "날씨 및 여행 시기 확인",
    "관광지 탐색",
    "맛집 검색",
    "숙소 추천",
    "교통편 확인",
    "예산 계산",
    "축제 및 행사 확인",
    "꿀팁 수집",
    "날짜별 일정표 생성"
  ]
}
"""

REACT_SYSTEM = """당신은 전문 여행 플래너 AI입니다. ReAct 패턴으로 아래 계획을 실행하세요.

[실행 계획]
{plan_text}

[ReAct 규칙]
1. Thought: 다음에 무엇을 해야 할지 생각하세요
2. Action: 적절한 도구를 호출하세요
3. Observation: 결과를 확인하고 다음 행동을 결정하세요
4. 모든 단계가 완료되면 "모든 여행 정보 수집 완료"라고 말하세요

[도구 선택 기준]
- 날씨/기후 → get_weather
- 자연/문화 관광지 → search_attractions
- 맛집 → search_restaurants
- 숙소 → search_accommodation
- 교통편 → get_transportation
- 예산 → calculate_budget
- 여행 시기 → get_best_season
- 축제/행사 → get_festivals
- 꿀팁 → get_local_tips
- 일정표 → create_itinerary

[중요] 반드시 모든 단계의 도구를 호출하여 완성도 높은 여행 계획을 만드세요.
"""


# ─────────────────────────────────────────────
# Phase 1: Plan - 실행 계획 수립
# ─────────────────────────────────────────────

def plan_phase(user_query: str) -> dict:
    """
    Plan-and-Execute의 Plan 단계
    AI가 사용자 질문을 분석해 JSON 형태의 실행 계획 생성
    """
    print("\n" + "="*55)
    print("  [Phase 1] 📋 여행 계획 수립 중...")
    print("="*55)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",  "content": PLAN_SYSTEM},
            {"role": "user",    "content": user_query},
        ],
        response_format={"type": "json_object"},
    )

    plan = json.loads(response.choices[0].message.content)

    print(f"  ✈  목적지: {plan.get('city')}  |  {plan.get('days')}일 여행")
    print(f"  📝 실행 단계 ({len(plan.get('steps', []))}개):")
    for i, step in enumerate(plan.get("steps", []), 1):
        print(f"     {i}. {step}")

    return plan


# ─────────────────────────────────────────────
# Phase 2: Execute - ReAct 루프 실행
# ─────────────────────────────────────────────

def react_execute(plan: dict, user_query: str) -> tuple[dict, list]:
    """
    ReAct 루프: Thought → Action → Observation 반복
    Plan에서 수립한 계획을 따라 모든 도구를 순서대로 호출
    """
    print("\n" + "="*55)
    print("  [Phase 2] 🔄 ReAct 실행 시작")
    print("="*55)

    city   = plan.get("city", "")
    days   = plan.get("days", 3)
    steps  = plan.get("steps", [])

    plan_text = (
        f"도시: {city}, 총 {days}일 여행\n"
        f"숙박: {plan.get('accommodation_type', '중급')} | "
        f"식비: {plan.get('meal_budget', '보통')} | "
        f"교통: {plan.get('transport', '대중교통')}\n\n"
        f"실행 단계:\n" +
        "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
    )

    messages = [
        {"role": "system", "content": REACT_SYSTEM.format(plan_text=plan_text)},
        {"role": "user",   "content": user_query},
    ]

    collected  = {}   # 수집된 결과
    react_log  = []   # ReAct 로그 (발표용)
    iteration  = 0
    max_iter   = 25   # 최대 반복 횟수

    while iteration < max_iter:
        iteration += 1

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        message = response.choices[0].message

        # ── Action: 도구 호출 ──
        if message.tool_calls:
            messages.append(message)

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"\n  🔧 Thought → Action: [{tool_name}]")
                print(f"     인자: {tool_args}")

                result     = execute_tool(tool_name, tool_args)
                result_dict = json.loads(result)

                print(f"     Observation: ✅ 완료")

                # 결과 수집
                collected[tool_name] = result_dict

                # ReAct 로그 기록
                react_log.append({
                    "iteration": iteration,
                    "action":    tool_name,
                    "args":      tool_args,
                    "result":    result_dict,
                })

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tool_call.id,
                    "content":      result,
                })

        # ── Observation: 완료 판단 ──
        else:
            if message.content:
                print(f"\n  ✅ {message.content}")
            break

    # 메타 정보 추가
    collected["_meta"] = {
        "city":               city,
        "days":               days,
        "user_query":         user_query,
        "steps":              steps,
        "accommodation_type": plan.get("accommodation_type", "중급"),
        "meal_budget":        plan.get("meal_budget", "보통"),
        "transport":          plan.get("transport", "대중교통"),
        "total_iterations":   iteration,
        "tools_used":         list(collected.keys()),
    }

    print(f"\n  📊 총 {iteration}번 반복 | {len(react_log)}개 도구 호출 완료")
    return collected, react_log


# ─────────────────────────────────────────────
# 전체 Agent 실행
# ─────────────────────────────────────────────

def run_agent(user_query: str) -> tuple[dict, list]:
    """
    Plan-and-Execute + ReAct 전체 파이프라인 실행

    Returns:
        collected: 수집된 모든 여행 정보
        react_log: ReAct 실행 로그 (발표/디버깅용)
    """
    plan               = plan_phase(user_query)
    collected, react_log = react_execute(plan, user_query)
    return collected, react_log
