"""
graph.py
────────
week11 멀티에이전트 LangGraph — 2개 경로

경로 A (explore): 탐색·추천 모드
    START → intent_router → conversation → orchestrator
          → [scholarship/employment/housing/finance] → synthesizer → END

경로 B (qa): 직접 Q&A 모드
    START → intent_router → qa_search → qa_answer → END
"""

from langgraph.graph import StateGraph, START, END

from state import MultiAgentState
from agents.intent_router import intent_router_node, route_by_intent
from agents.conversation_agent import conversation_node, route_conversation
from agents.orchestrator import orchestrator_node
from agents.specialist import (
    scholarship_node, employment_node,
    housing_node, finance_node,
)
from agents.synthesizer import synthesizer_node
from agents.qa_agent import qa_search_node, qa_answer_node


def build_graph():
    g = StateGraph(MultiAgentState)

    # ── 노드 등록 ────────────────────────────────────────────
    g.add_node("intent_router_node", intent_router_node)

    # 경로 A
    g.add_node("conversation_node",  conversation_node)
    g.add_node("orchestrator_node",  orchestrator_node)
    g.add_node("scholarship_node",   scholarship_node)
    g.add_node("employment_node",    employment_node)
    g.add_node("housing_node",       housing_node)
    g.add_node("finance_node",       finance_node)
    g.add_node("synthesizer_node",   synthesizer_node)

    # 경로 B
    g.add_node("qa_search_node",     qa_search_node)
    g.add_node("qa_answer_node",     qa_answer_node)

    # ── 엣지 ────────────────────────────────────────────────
    g.add_edge(START, "intent_router_node")

    # 의도에 따라 분기
    g.add_conditional_edges(
        "intent_router_node",
        route_by_intent,
        {
            "explore": "conversation_node",  # 경로 A
            "qa":      "qa_search_node",     # 경로 B
        },
    )

    # ── 경로 A ──────────────────────────────────────────────
    g.add_conditional_edges(
        "conversation_node",
        route_conversation,
        {
            "continue": END,                 # 대화 중 → 다음 입력 대기
            "complete": "orchestrator_node", # 완성 → 분석 시작
        },
    )
    g.add_edge("orchestrator_node", "scholarship_node")
    g.add_edge("scholarship_node",  "employment_node")
    g.add_edge("employment_node",   "housing_node")
    g.add_edge("housing_node",      "finance_node")
    g.add_edge("finance_node",      "synthesizer_node")
    g.add_edge("synthesizer_node",  END)

    # ── 경로 B ──────────────────────────────────────────────
    g.add_edge("qa_search_node", "qa_answer_node")
    g.add_edge("qa_answer_node", END)

    return g.compile()


graph = build_graph()


def run_step(
    messages: list,
    user_profile: dict = None,
    profile_complete: bool = False,
) -> MultiAgentState:
    # 마지막 사용자 메시지 추출 (라우터용)
    user_query = ""
    for m in reversed(messages):
        if m["role"] == "user":
            user_query = m["content"]
            break

    initial: MultiAgentState = {
        "messages":        messages,
        "user_query":      user_query,
        "user_profile":    user_profile or {},
        "profile_complete": profile_complete,
        "execution_trace": [],
    }
    return graph.invoke(initial)


def get_mermaid() -> str:
    return graph.get_graph().draw_mermaid()
