"""
graph.py — LangGraph 워크플로우 (BACKEND 계층)

흐름:
  START → agent_node
    ↓ tool call?
    YES → tool_dispatcher
      ├─ 유사도 미달(조기탈출) → web_search_node → generate_node → END
      ├─ 벡터 검색 정상       → grade_docs_node
      │     → (relevant)     generate_node → END
      │     → (not_relevant) rewrite_node  → agent_node (최대 2회)
      │     → (2회 실패)     web_search_node → generate_node → END
      ├─ 실시간/주택/마감일   → generate_node → END
      └─ 비교/목록            → generate_node → END
    NO → generate_node → END
"""

from langgraph.graph import StateGraph, START, END

from backend.state                    import FinalRAGState
from backend.agents.agent_node        import agent_node,      route_agent
from backend.agents.tool_dispatcher   import tool_dispatcher,  route_tool
from backend.agents.grade_docs_node   import grade_docs_node,  route_grade
from backend.agents.rewrite_node      import rewrite_node
from backend.agents.generate_node     import generate_node
from backend.agents.web_search_node   import web_search_node
from backend.agents.diagnosis_node    import diagnosis_node


def _pre_generate(state: FinalRAGState) -> dict:
    """검색 전용 그래프의 종료 노드 — 상태를 그대로 통과."""
    return {}


def build_graph():
    g = StateGraph(FinalRAGState)

    g.add_node("agent_node",      agent_node)
    g.add_node("tool_dispatcher", tool_dispatcher)
    g.add_node("grade_docs_node", grade_docs_node)
    g.add_node("rewrite_node",    rewrite_node)
    g.add_node("web_search_node", web_search_node)
    g.add_node("diagnosis_node",  diagnosis_node)
    g.add_node("generate_node",   generate_node)

    g.add_edge(START, "agent_node")
    g.add_conditional_edges("agent_node",      route_agent,
        {"tool": "tool_dispatcher", "generate": "generate_node"})
    g.add_conditional_edges("tool_dispatcher", route_tool,
        {"grade": "grade_docs_node", "generate": "generate_node",
         "web_search": "web_search_node", "diagnosis": "diagnosis_node"})
    g.add_conditional_edges("grade_docs_node", route_grade,
        {"generate": "generate_node", "rewrite": "rewrite_node", "web_search": "web_search_node"})
    g.add_edge("rewrite_node",    "agent_node")
    g.add_edge("web_search_node", "generate_node")
    g.add_edge("diagnosis_node",  END)
    g.add_edge("generate_node",   END)

    return g.compile()


def build_retrieval_graph():
    """generate_node 직전까지만 실행 — FastAPI 스트리밍용."""
    g = StateGraph(FinalRAGState)

    g.add_node("agent_node",      agent_node)
    g.add_node("tool_dispatcher", tool_dispatcher)
    g.add_node("grade_docs_node", grade_docs_node)
    g.add_node("rewrite_node",    rewrite_node)
    g.add_node("web_search_node", web_search_node)
    g.add_node("diagnosis_node",  diagnosis_node)
    g.add_node("pre_generate",    _pre_generate)

    g.add_edge(START, "agent_node")
    g.add_conditional_edges("agent_node",      route_agent,
        {"tool": "tool_dispatcher", "generate": "pre_generate"})
    g.add_conditional_edges("tool_dispatcher", route_tool,
        {"grade": "grade_docs_node", "generate": "pre_generate",
         "web_search": "web_search_node", "diagnosis": "diagnosis_node"})
    g.add_conditional_edges("grade_docs_node", route_grade,
        {"generate": "pre_generate", "rewrite": "rewrite_node", "web_search": "web_search_node"})
    g.add_edge("rewrite_node",    "agent_node")
    g.add_edge("web_search_node", "pre_generate")
    g.add_edge("diagnosis_node",  END)
    g.add_edge("pre_generate",    END)

    return g.compile()


graph           = build_graph()
retrieval_graph = build_retrieval_graph()


def run(question: str) -> FinalRAGState:
    return graph.invoke({
        "question":        question,
        "retry_count":     0,
        "execution_trace": [],
    })


def run_retrieval(
    question: str,
    user_profile: dict | None = None,
    conversation_history: list | None = None,
) -> FinalRAGState:
    return retrieval_graph.invoke({
        "question":            question,
        "retry_count":         0,
        "execution_trace":     [],
        "user_profile":        user_profile or {},
        "conversation_history": conversation_history or [],
    })


def get_mermaid() -> str:
    return graph.get_graph().draw_mermaid()
