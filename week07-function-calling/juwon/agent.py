"""
agent.py - Function Calling 핵심 로직

[7주차 핵심 흐름]
사용자 질문
  → OpenAI API 호출 (tools 목록 전달)
  → AI가 함수 선택 + 인자 생성
  → 함수 실행
  → 결과를 AI에게 다시 전달
  → 최종 자연어 답변 생성
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOLS, execute_tool

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """당신은 친절하고 전문적인 한국 여행 플래너 AI입니다.
사용자의 여행 계획을 도와주며, 필요할 때 반드시 적절한 도구를 사용해 정확한 정보를 제공합니다.

[도구 사용 기준]
- 날씨/기후 관련 → get_weather
- 관광지/명소/맛집 관련 → search_attractions
- 예산/비용 관련 → calculate_budget
- 여행 시기/계절 관련 → get_best_season

[답변 원칙]
- 도구 결과를 바탕으로 자연스럽고 친절하게 답변하세요
- 수치(온도, 금액 등)는 항상 도구 결과를 사용하고 추측하지 마세요
- 추가로 도움이 될 정보가 있으면 자연스럽게 덧붙여 주세요
"""


def chat(messages: list[dict]) -> tuple[str, list[dict]]:
    """
    Function Calling 포함 대화 처리

    Returns:
        (최종 답변 텍스트, 업데이트된 messages)
    """
    # Step 1: OpenAI API 호출 (tools 목록과 함께)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",  # AI가 알아서 함수 호출 여부 결정
    )

    message = response.choices[0].message

    # Step 2: 함수 호출이 없으면 바로 답변 반환
    if not message.tool_calls:
        return message.content, messages

    # Step 3: AI 응답을 messages에 추가
    messages.append(message)

    # Step 4: AI가 선택한 함수(들) 실행
    for tool_call in message.tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        print(f"\n  ┌─ [함수 호출] {tool_name}")
        print(f"  └─ [인자]     {tool_args}")

        result = execute_tool(tool_name, tool_args)

        # Step 5: 함수 실행 결과를 messages에 추가
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })

    # Step 6: 함수 결과를 바탕으로 최종 답변 생성
    final_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
    )

    final_message = final_response.choices[0].message
    messages.append(final_message)

    return final_message.content, messages
