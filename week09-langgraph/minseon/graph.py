"""
graph.py
────────
청년정책 에이전트 — LangGraph StateGraph 조립

그래프 구조:
    START
      │
      ▼
  parse_query_node       ← 질문 분석 (type / category / keywords)
      │
      ▼  [route_by_query_type]
  ┌───┴──────────────────────────────────┐
  │ need_profile (일반 추천 요청)         │ skip_profile (특정 정책 문의)
  ▼                                      │
profile_node                             │
  │                                      │
  └──────────────────┬───────────────────┘
                     ▼
               search_node              ← 정책 문서 검색
                     │
                     ▼  [route_by_results]
              ┌──────┴──────────────────┐
              │ retry (결과 없음)        │ proceed (결과 있음)
              ▼                         ▼
    (search_node 재실행)          recommend_node   ← Claude 맞춤 추천
                                        │
                                        ▼
                                       END
"""

from langgraph.graph import StateGraph, START, END

from state import YouthPolicyState
from nodes import (
    parse_query_node,
    profile_node,
    search_node,
    recommend_node,
    route_by_query_type,
    route_by_results,
)


def build_graph():
    """청년정책 에이전트 그래프를 생성하고 컴파일합니다."""

    g = StateGraph(YouthPolicyState)

    # ── 노드 등록 ────────────────────────────────────────────
    g.add_node("parse_query_node", parse_query_node)
    g.add_node("profile_node",     profile_node)
    g.add_node("search_node",      search_node)
    g.add_node("recommend_node",   recommend_node)

    # ── 시작 엣지 ────────────────────────────────────────────
    g.add_edge(START, "parse_query_node")

    # ── 조건부 엣지 1: 질문 유형 → 프로필 수집 필요 여부 ─────
    g.add_conditional_edges(
        "parse_query_node",
        route_by_query_type,
        {
            "need_profile": "profile_node",   # 일반 추천 → 프로필 먼저
            "skip_profile": "search_node",    # 특정 정책 → 바로 검색
        },
    )

    # ── 일반 엣지 ────────────────────────────────────────────
    g.add_edge("profile_node", "search_node")

    # ── 조건부 엣지 2: 검색 결과 없으면 전체 DB 재검색 ────────
    g.add_conditional_edges(
        "search_node",
        route_by_results,
        {
            "retry":   "search_node",      # 결과 없음 → 자기 자신으로 루프
            "proceed": "recommend_node",   # 결과 있음 → 추천 생성
        },
    )

    # ── 종료 엣지 ────────────────────────────────────────────
    g.add_edge("recommend_node", END)

    return g.compile()


graph = build_graph()


def run(user_query: str) -> YouthPolicyState:
    """그래프를 실행하고 최종 State를 반환합니다."""
    initial: YouthPolicyState = {
        "user_query":         user_query,
        "search_retry_count": 0,
        "execution_trace":    [],
    }
    return graph.invoke(initial)


def stream_run(user_query: str):
    """그래프를 스트리밍 모드로 실행합니다.

    Yields:
        (node_name: str, state_updates: dict)
    """
    initial: YouthPolicyState = {
        "user_query":         user_query,
        "search_retry_count": 0,
        "execution_trace":    [],
    }
    for event in graph.stream(initial, stream_mode="updates"):
        for node_name, updates in event.items():
            yield node_name, updates


def get_mermaid() -> str:
    return graph.get_graph().draw_mermaid()
