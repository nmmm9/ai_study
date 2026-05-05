"""
graph.py
────────
week10 에이전트 — 두 개의 LangGraph 그래프

[chat_graph]  챗봇 답변
    START → chat_parse_node
              ↓ [chat_route_by_type]
              ├─ need_profile → chat_profile_node → chat_search_node
              └─ skip_profile →                    chat_search_node
                                                        ↓ [chat_route_by_results]
                                                        ├─ retry  → chat_search_node
                                                        └─ proceed → chat_recommend_node → END

[notify_graph] 이메일 자동 알림
    START → profile_build_node → search_node
              ↓ [route_by_results]
              ├─ retry  → search_node
              └─ proceed → match_node
                              ↓ [route_by_match]
                              ├─ send → notify_node → END
                              └─ skip → END
"""

from langgraph.graph import StateGraph, START, END

from state import NotifyState
from nodes import (
    # chat
    chat_parse_node, chat_profile_node, chat_search_node, chat_recommend_node,
    chat_route_by_type, chat_route_by_results,
    # notify
    profile_build_node, search_node, match_node, notify_node,
    route_by_results, route_by_match,
)


# ── 챗봇 그래프 ──────────────────────────────────────────────────

def _build_chat_graph():
    g = StateGraph(NotifyState)

    g.add_node("chat_parse_node",     chat_parse_node)
    g.add_node("chat_profile_node",   chat_profile_node)
    g.add_node("chat_search_node",    chat_search_node)
    g.add_node("chat_recommend_node", chat_recommend_node)

    g.add_edge(START, "chat_parse_node")

    g.add_conditional_edges(
        "chat_parse_node",
        chat_route_by_type,
        {"need_profile": "chat_profile_node", "skip_profile": "chat_search_node"},
    )

    g.add_edge("chat_profile_node", "chat_search_node")

    g.add_conditional_edges(
        "chat_search_node",
        chat_route_by_results,
        {"retry": "chat_search_node", "proceed": "chat_recommend_node"},
    )

    g.add_edge("chat_recommend_node", END)
    return g.compile()


# ── 알림 그래프 ──────────────────────────────────────────────────

def _build_notify_graph():
    g = StateGraph(NotifyState)

    g.add_node("profile_build_node", profile_build_node)
    g.add_node("search_node",        search_node)
    g.add_node("match_node",         match_node)
    g.add_node("notify_node",        notify_node)

    g.add_edge(START, "profile_build_node")
    g.add_edge("profile_build_node", "search_node")

    g.add_conditional_edges(
        "search_node",
        route_by_results,
        {"retry": "search_node", "proceed": "match_node"},
    )

    g.add_conditional_edges(
        "match_node",
        route_by_match,
        {"send": "notify_node", "skip": END},
    )

    g.add_edge("notify_node", END)
    return g.compile()


chat_graph   = _build_chat_graph()
notify_graph = _build_notify_graph()


# ── 실행 헬퍼 ────────────────────────────────────────────────────

def run_chat(
    user_query: str,
    logged_in_user: dict | None = None,
) -> NotifyState:
    """
    챗봇 모드 실행.
    logged_in_user 있으면 나이·지역이 자동으로 프로필에 주입됩니다.
    """
    initial: NotifyState = {
        "user_query":         user_query,
        "search_retry_count": 0,
        "execution_trace":    [],
    }
    if logged_in_user:
        initial["user_name"]   = logged_in_user.get("name", "")
        initial["user_email"]  = logged_in_user.get("email", "")
        initial["user_age"]    = logged_in_user.get("age", 0)
        initial["user_region"] = logged_in_user.get("region", "")
        initial["user_profile"] = {
            "age":    logged_in_user.get("age"),
            "region": logged_in_user.get("region"),
        }
    return chat_graph.invoke(initial)


def run_notify(
    name: str,
    email: str,
    age: int,
    region: str,
    send_notification: bool = True,
) -> NotifyState:
    """알림 모드 실행. send_notification=False 이면 이메일 미발송."""
    initial: NotifyState = {
        "user_name":          name,
        "user_email":         email if send_notification else "",
        "user_age":           age,
        "user_region":        region,
        "search_retry_count": 0,
        "execution_trace":    [],
    }
    return notify_graph.invoke(initial)


def get_chat_mermaid() -> str:
    return chat_graph.get_graph().draw_mermaid()


def get_notify_mermaid() -> str:
    return notify_graph.get_graph().draw_mermaid()
