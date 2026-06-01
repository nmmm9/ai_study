"""
conversation_agent.py
─────────────────────
대화형 프로필 수집 에이전트

사용자와 자연스러운 대화로 나이·지역·상황·관심분야를 수집합니다.
모든 정보가 모이면 <PROFILE> 태그로 JSON을 반환 → profile_complete = True
"""

import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from openai import OpenAI
from state import MultiAgentState

_client = OpenAI()

_SYSTEM = """\
당신은 청년정책 AI 상담사입니다.
맞춤 정책 추천을 위해 아래 4가지 항목만 수집하세요.

## 수집 항목 (이것만, 다른 건 절대 묻지 말 것)
1. age      — 나이 (숫자). 예) 22
2. region   — 거주 지역 (시/도). 예) 서울, 경기, 부산
3. interests — 관심 분야. 반드시 아래 4개 중 해당하는 것만 선택:
               ["장학금", "취업", "주거", "금융"]
4. employment — 현재 상황: "재학중" | "졸업" | "구직중" | "취업중"
                (장학금·취업 관심 시만 필수. 주거·금융만이면 "미확인"으로 처리)

## 핵심 규칙
- 대화 전체(첫 메시지 포함)를 스캔해 이미 언급된 정보를 먼저 추출하라.
  예) "장학금 종류 추천해줘" → interests=["장학금"] 즉시 파악
  예) "22살 서울인데 주거 정책 알려줘" → age=22, region=서울, interests=["주거"] 즉시 파악
- 이미 파악된 항목은 절대 다시 묻지 마라.
- 누락된 항목만, 한 번에 한 가지씩 물어봐라.
- 위 4가지 항목 외의 것(전공, 학교, 소득, 직장명 등)은 절대 묻지 마라.
- 반말로 짧게 친근하게 말하라.

## 완료 조건
필수 항목이 모두 파악되면 즉시 응답 마지막에 아래 태그를 붙이고 분석 시작을 알려라:

<PROFILE>{"age": 22, "region": "서울", "employment": "재학중", "interests": ["장학금"]}</PROFILE>

주거·금융만인 경우:
<PROFILE>{"age": 22, "region": "서울", "employment": "미확인", "interests": ["주거"]}</PROFILE>
"""


def conversation_node(state: MultiAgentState) -> dict:
    """사용자와 대화하며 프로필을 수집합니다."""
    messages  = state.get("messages", [])
    profile   = state.get("user_profile", {})

    # LLM으로 다음 대화 생성
    llm_msgs = [{"role": "system", "content": _SYSTEM}]
    for m in messages:
        llm_msgs.append({"role": m["role"], "content": m["content"]})

    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=llm_msgs,
        max_tokens=400,
    )
    assistant_msg = resp.choices[0].message.content or ""

    # 프로필 태그 추출
    profile_complete = False
    if "<PROFILE>" in assistant_msg and "</PROFILE>" in assistant_msg:
        try:
            raw     = assistant_msg.split("<PROFILE>")[1].split("</PROFILE>")[0]
            profile = json.loads(raw.strip())
            profile_complete = True
            # 태그 제거 후 마무리 멘트
            clean = assistant_msg.split("<PROFILE>")[0].strip()
            assistant_msg = clean or "좋아! 정보 다 모았어. 잠깐만 기다려, 맞춤 정책 찾아볼게 🔍"
        except Exception:
            pass

    new_messages = list(messages) + [{"role": "assistant", "content": assistant_msg}]
    trace = list(state.get("execution_trace", []))
    trace.append({
        "node":    "conversation_node",
        "summary": f"프로필 수집 {'완료' if profile_complete else '진행 중'}",
    })

    return {
        "messages":        new_messages,
        "user_profile":    profile,
        "profile_complete": profile_complete,
        "execution_trace": trace,
    }


def route_conversation(state: MultiAgentState) -> str:
    """프로필 완성 여부에 따라 분기."""
    return "complete" if state.get("profile_complete") else "continue"
