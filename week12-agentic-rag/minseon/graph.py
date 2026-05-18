"""
graph.py
────────
week12 Agentic RAG — LangGraph

흐름:
  START → agent_node
        ↓ tool call 있음          ↓ tool call 없음
  search_tool_node           generate_node → END
        ↓
  grade_docs_node
        ↓ relevant              ↓ not_relevant (retry < 2)
  generate_node → END     rewrite_node → agent_node (재시도)
                                ↓ retry >= 2
                          generate_node → END
"""

from langgraph.graph import StateGraph, START, END

from state import AgenticRAGState
from agents.agent_node       import agent_node,       route_agent
from agents.search_tool_node import search_tool_node
from agents.grade_node       import grade_docs_node,  route_grade
from agents.rewrite_node     import rewrite_node
from agents.generate_node    import generate_node


def build_graph():
    g = StateGraph(AgenticRAGState)

    # ── 노드 등록 ────────────────────────────────────────────
    g.add_node("agent_node",       agent_node)
    g.add_node("search_tool_node", search_tool_node)
    g.add_node("grade_docs_node",  grade_docs_node)
    g.add_node("rewrite_node",     rewrite_node)
    g.add_node("generate_node",    generate_node)

    # ── 엣지 ────────────────────────────────────────────────
    g.add_edge(START, "agent_node")

    # 에이전트 결정: 검색 or 직접 생성
    g.add_conditional_edges(
        "agent_node",
        route_agent,
        {
            "search":   "search_tool_node",
            "generate": "generate_node",
        },
    )

    # 검색 실행 후 관련성 평가
    g.add_edge("search_tool_node", "grade_docs_node")

    # 관련성 평가: 생성 or 재작성
    g.add_conditional_edges(
        "grade_docs_node",
        route_grade,
        {
            "generate": "generate_node",
            "rewrite":  "rewrite_node",
        },
    )

    # 재작성 후 에이전트로 돌아가 재검색
    g.add_edge("rewrite_node", "agent_node")

    g.add_edge("generate_node", END)

    return g.compile()


graph = build_graph()


def run(question: str) -> AgenticRAGState:
    initial: AgenticRAGState = {
        "question":        question,
        "retry_count":     0,
        "execution_trace": [],
    }
    return graph.invoke(initial)


def run_notify(
    name: str,
    email: str,
    age: int,
    region: str,
    send_notification: bool = True,
) -> None:
    """사용자 프로필 기반 Agentic RAG 실행 후 이메일 발송 (scheduler용)."""
    from notifier import send_email, build_email_html
    import user_db

    question = (
        f"나이 {age}살 {region} 거주 청년에게 맞는 청년정책을 "
        f"장학금, 취업, 주거, 금융 분야별로 추천해줘."
    )
    result     = run(question)
    answer     = result.get("answer", "")
    html_answer = answer.replace("\n", "<br>")

    if send_notification and answer:
        html_body = build_email_html(
            name=name,
            age=age,
            region=region,
            recommendation=html_answer,
        )
        ok = send_email(
            to_email=email,
            subject=f"[청년정책 AI] {name}님 맞춤 정책 알림",
            html_body=html_body,
        )
        if ok:
            user_db.mark_notified(email)
            user_db.log_notification(
                email=email,
                policy_titles=[answer[:80]],
            )


def get_mermaid() -> str:
    return graph.get_graph().draw_mermaid()
