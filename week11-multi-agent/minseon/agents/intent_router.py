"""
intent_router.py
────────────────
의도 라우터 — 질문을 보고 경로 A / B를 결정

경로 A (explore): 맞춤 정책 탐색 → 대화로 프로필 수집 필요
경로 B (qa)     : 팩트 질문 → 바로 RAG 검색 후 답변

분류 기준:
  explore — "추천해줘", "뭐가 있어", "받을 수 있는 거", "맞는 정책"
  qa      — 특정 정책 이름 언급, "같이 받을 수 있어", "조건이 뭐야",
            "신청 기간", "자격이 어떻게 돼", "차이가 뭐야"
"""

from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from openai import OpenAI
from state import MultiAgentState

_client = OpenAI()

_SYSTEM = """\
사용자 질문을 아래 두 가지 중 하나로 분류하세요.

explore : 자신에게 맞는 정책을 찾아달라는 탐색·추천 요청
          예) "나한테 맞는 정책 찾아줘", "받을 수 있는 거 뭐가 있어?", "추천해줘"

qa      : 특정 정책에 대한 팩트 확인·비교·설명 요청
          예) "청년도약계좌랑 청년희망적금 같이 받을 수 있어?",
              "청년내일채움공제 신청 조건이 어떻게 돼?",
              "월세 지원 신청 기간이 언제야?",
              "A정책이랑 B정책 차이가 뭐야?"

반드시 explore 또는 qa 중 하나만 소문자로 응답하세요.
"""


def intent_router_node(state: MultiAgentState) -> dict:
    """질문 의도를 판단하여 경로를 결정합니다."""
    messages = state.get("messages", [])
    query    = state.get("user_query", "")

    # 마지막 사용자 메시지 추출
    if not query and messages:
        for m in reversed(messages):
            if m["role"] == "user":
                query = m["content"]
                break

    if not query:
        intent = "explore"
    else:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user",   "content": query},
            ],
            max_tokens=10,
            temperature=0,
        )
        raw    = (resp.choices[0].message.content or "explore").strip().lower()
        intent = "qa" if "qa" in raw else "explore"

    print(f"[intent_router] '{query[:30]}...' → {intent}")

    trace = list(state.get("execution_trace", []))
    trace.append({
        "node":    "intent_router_node",
        "summary": f"의도 분류: {intent} ({'탐색 모드' if intent == 'explore' else '직접 Q&A 모드'})",
    })

    return {
        "intent":          intent,
        "user_query":      query,
        "execution_trace": trace,
    }


def route_by_intent(state: MultiAgentState) -> str:
    return state.get("intent", "explore")
