"""
app.py - 8주차 여행 플래너 AI Agent (Streamlit UI)

실행: streamlit run app.py

터미널 대신 웹 UI에서:
- 채팅으로 질문 입력
- ReAct 실행 과정 실시간 표시
- 완성된 여행 계획 HTML로 바로 확인
"""

import json
import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOLS, execute_tool
from html_generator import generate_html

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY", "").strip().strip('\ufeff')
client  = OpenAI(api_key=api_key)

# ── 페이지 설정 ─────────────────────────────────
st.set_page_config(
    page_title="✈ 여행 플래너 AI Agent",
    page_icon="✈",
    layout="wide",
)

# ── CSS ─────────────────────────────────────────
st.markdown("""
<style>
    .main { background: #f0f4ff; }
    .stChatMessage { border-radius: 12px; }
    .react-log { background: #1e293b; color: #60a5fa; border-radius: 8px;
                 padding: 10px 14px; font-family: monospace; font-size: 13px;
                 margin: 4px 0; }
    .phase-badge { background: #2563eb; color: white; border-radius: 20px;
                   padding: 4px 12px; font-size: 12px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ────────────────────────────────────────
st.markdown("## ✈ 여행 플래너 AI Agent")
st.markdown("*8주차 ReAct + Plan-and-Execute*")
st.divider()

# ── 세션 상태 초기화 ────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []   # 채팅 히스토리


# ── 시스템 프롬프트 ─────────────────────────────
PLAN_SYSTEM = """당신은 여행 계획 전문가입니다.
사용자의 여행 요청을 분석해서 실행 계획을 JSON 형태로 작성하세요.

반드시 다음 JSON 형식으로만 응답하세요:
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
날씨 → get_weather | 관광지 → search_attractions | 맛집 → search_restaurants
숙소 → search_accommodation | 교통 → get_transportation | 예산 → calculate_budget
여행시기 → get_best_season | 축제 → get_festivals | 꿀팁 → get_local_tips | 일정표 → create_itinerary

[중요] 반드시 모든 단계의 도구를 호출하여 완성도 높은 여행 계획을 만드세요.
"""


# ── Phase 1: Plan ───────────────────────────────
def plan_phase(user_query: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PLAN_SYSTEM},
            {"role": "user",   "content": user_query},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


# ── Phase 2: ReAct Execute ──────────────────────
def react_execute(plan: dict, user_query: str, status_container):
    city  = plan.get("city", "")
    days  = plan.get("days", 3)
    steps = plan.get("steps", [])

    plan_text = (
        f"도시: {city}, 총 {days}일 여행\n"
        f"숙박: {plan.get('accommodation_type','중급')} | "
        f"식비: {plan.get('meal_budget','보통')} | "
        f"교통: {plan.get('transport','대중교통')}\n\n실행 단계:\n" +
        "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
    )

    messages = [
        {"role": "system", "content": REACT_SYSTEM.format(plan_text=plan_text)},
        {"role": "user",   "content": user_query},
    ]

    collected  = {}
    react_log  = []
    iteration  = 0

    while iteration < 25:
        iteration += 1
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        message = response.choices[0].message

        if message.tool_calls:
            messages.append(message)
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # 실시간 진행 상황 표시
                status_container.markdown(
                    f'<div class="react-log">🔧 [{tool_name}] {tool_args}</div>',
                    unsafe_allow_html=True
                )

                result      = execute_tool(tool_name, tool_args)
                result_dict = json.loads(result)

                collected[tool_name] = result_dict
                react_log.append({"action": tool_name, "args": tool_args, "result": result_dict})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
        else:
            break

    collected["_meta"] = {
        "city": city, "days": days, "user_query": user_query, "steps": steps,
        "accommodation_type": plan.get("accommodation_type", "중급"),
        "meal_budget":        plan.get("meal_budget", "보통"),
        "transport":          plan.get("transport", "대중교통"),
        "total_iterations":   iteration,
    }

    return collected, react_log


# ── 이전 채팅 히스토리 표시 ─────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.write(msg["content"])
        else:
            # AI 메시지: HTML 결과 + 로그
            if msg.get("html"):
                st.components.v1.html(msg["html"], height=900, scrolling=True)
            if msg.get("text"):
                st.write(msg["text"])


# ── 채팅 입력 ────────────────────────────────────
if prompt := st.chat_input("여행 질문을 입력하세요... (예: 제주도 3박 4일 여행 계획 짜줘)"):

    # 사용자 메시지 표시
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI 응답
    with st.chat_message("assistant"):

        # Phase 1: Plan
        st.markdown('<span class="phase-badge">Phase 1</span> 📋 여행 계획 수립 중...', unsafe_allow_html=True)
        with st.spinner(""):
            plan = plan_phase(prompt)

        city  = plan.get("city", "여행지")
        days  = plan.get("days", 3)
        steps = plan.get("steps", [])

        st.success(f"✈ **{city}** {days}일 여행 계획 수립 완료!")

        with st.expander(f"📝 실행 단계 ({len(steps)}개)", expanded=False):
            for i, s in enumerate(steps, 1):
                st.write(f"{i}. {s}")

        # Phase 2: ReAct
        st.markdown('<span class="phase-badge">Phase 2</span> 🔄 ReAct 실행 중...', unsafe_allow_html=True)
        status_container = st.empty()

        with st.spinner("도구 호출 중..."):
            collected, react_log = react_execute(plan, prompt, status_container)

        status_container.empty()
        st.success(f"✅ {len(react_log)}개 도구 호출 완료!")

        with st.expander("🤖 ReAct 실행 로그", expanded=False):
            for i, log in enumerate(react_log, 1):
                st.markdown(
                    f'<div class="react-log">{i}. [{log["action"]}] {log["args"]}</div>',
                    unsafe_allow_html=True
                )

        # Phase 3: HTML 생성
        st.markdown('<span class="phase-badge">Phase 3</span> 📄 여행 계획서 생성 중...', unsafe_allow_html=True)
        html_content = generate_html(collected, react_log)

        st.divider()
        st.components.v1.html(html_content, height=900, scrolling=True)

        # 세션에 저장
        st.session_state.messages.append({
            "role": "assistant",
            "html": html_content,
            "text": f"✈ {city} {days}일 여행 계획 완성!"
        })
