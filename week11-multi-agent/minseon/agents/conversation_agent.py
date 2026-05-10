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
사용자와 친근한 대화로 아래 4가지 정보를 자연스럽게 수집하세요.

수집 항목:
1. 나이 (숫자)
2. 거주 지역 (시/도 단위: 서울, 경기, 부산 등)
3. 현재 상황 ("재학중" | "졸업" | "구직중" | "취업중")
4. 관심 분야 (장학금/취업/주거/금융 중 해당하는 것 모두)

규칙:
- 한 번에 한 가지 질문만 하세요
- 친근하고 짧게 말하세요 (반말 사용)
- 사용자 답변에서 정보를 자연스럽게 파악하세요
- 4가지가 모두 파악되면 아래 형식으로 응답 마지막에 추가:

<PROFILE>{"age": 25, "region": "서울", "employment": "구직중", "interests": ["취업", "주거"]}</PROFILE>

정보가 부족하면 계속 대화하세요.
"""


def conversation_node(state: MultiAgentState) -> dict:
    """사용자와 대화하며 프로필을 수집합니다."""
    messages  = state.get("messages", [])
    profile   = state.get("user_profile", {})

    # 대화 시작이면 인사 메시지 추가
    if not messages:
        greeting = "안녕! 나는 청년정책 AI야 😊\n맞춤 정책을 찾아주려면 몇 가지만 알아야 해.\n먼저 나이가 어떻게 돼?"
        trace = list(state.get("execution_trace", []))
        trace.append({"node": "conversation_node", "summary": "대화 시작"})
        return {
            "messages":        [{"role": "assistant", "content": greeting}],
            "profile_complete": False,
            "execution_trace": trace,
        }

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
