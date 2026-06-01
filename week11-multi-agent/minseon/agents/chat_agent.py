"""
chat_agent.py
─────────────
경로 C: 일상 대화 처리

정책과 무관한 인사·감사·짧은 반응을 자연스럽게 처리합니다.
"""

from openai import OpenAI
from state import MultiAgentState

_client = OpenAI()

_SYSTEM = """\
당신은 청년정책 AI 상담사입니다.
사용자가 정책 질문이 아닌 일상적인 대화(인사, 감사, 짧은 반응 등)를 보냈습니다.
짧고 자연스럽게 반응하세요. 반말로, 1-2문장 이내로 답하세요.
정책 추천이나 검색을 다시 시작하지 마세요.
"""


def chat_node(state: MultiAgentState) -> dict:
    """일상 대화에 자연스럽게 응답합니다."""
    messages = state.get("messages", [])

    llm_msgs = [{"role": "system", "content": _SYSTEM}]
    for m in messages:
        llm_msgs.append({"role": m["role"], "content": m["content"]})

    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=llm_msgs,
        max_tokens=100,
        temperature=0.7,
    )
    answer = resp.choices[0].message.content or "ㅎㅎ 도움이 됐으면 좋겠어! 더 궁금한 거 있으면 물어봐 😊"

    print(f"[chat_node] 일상 대화 응답")

    new_messages = list(messages) + [{"role": "assistant", "content": answer}]
    trace = list(state.get("execution_trace", []))
    trace.append({"node": "chat_node", "summary": "일상 대화 응답"})

    return {
        "messages":        new_messages,
        "final_answer":    answer,
        "execution_trace": trace,
    }
