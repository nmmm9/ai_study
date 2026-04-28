"""LangGraph StateGraph wiring.

Graph topology:

    [START] → supervisor → (parallel) → shopping
                                     → lifestyle      → writer → [END]
                                     → sports
                                     → info

Conditional edge from supervisor uses `plan` to dispatch to a subset of
domain agents. Domain agents run concurrently. After all selected
agents finish, the writer composes the final answer.

We also expose `agent_stream()` — an async generator that walks the graph
manually so we can emit fine-grained SSE events (node_start, tool_call,
tool_result, token, node_end) rather than relying on LangGraph's
built-in streaming (which is more coarse).
"""

import asyncio
from typing import AsyncGenerator

from agents.state import GraphState
from agents.supervisor import supervisor_node, DOMAIN_DESCRIPTIONS
from agents.domain_agent import run_domain_agent
from agents.writer import writer_stream
from services.memory import append_messages, get_history

# We build a LangGraph for visualization/educational purposes,
# and run a hand-rolled streaming pipeline below.
try:
    from langgraph.graph import StateGraph, END
    _HAS_LANGGRAPH = True
except ImportError:
    _HAS_LANGGRAPH = False


def build_graph():
    """Build a LangGraph StateGraph for inspection/visualization.

    The actual execution is done by `agent_stream` below for finer
    streaming control. This graph is exposed via /api/graph.
    """
    if not _HAS_LANGGRAPH:
        return None

    g = StateGraph(GraphState)

    DOMAINS = ["shopping", "lifestyle", "sports", "news", "finance",
               "government", "education", "info"]

    g.add_node("supervisor", lambda s: s)
    for d in DOMAINS:
        g.add_node(d, lambda s: s)
    g.add_node("writer", lambda s: s)

    g.set_entry_point("supervisor")

    def route(state: GraphState):
        plan = state.get("plan", []) or []
        if not plan:
            return ["writer"]
        return list(plan)

    routes = {d: d for d in DOMAINS}
    routes["writer"] = "writer"
    g.add_conditional_edges("supervisor", route, routes)

    for d in DOMAINS:
        g.add_edge(d, "writer")

    g.add_edge("writer", END)

    return g.compile()


def graph_metadata() -> dict:
    """Static metadata about the graph for the frontend visualizer."""
    DOMAINS = ["shopping", "lifestyle", "sports", "news", "finance",
               "government", "education", "info"]
    nodes = [
        {"id": "supervisor", "label": "Supervisor", "type": "router",
         "desc": "질문 분석 후 적절한 도메인 에이전트로 라우팅"},
    ]
    labels = {
        "shopping": "Shopping", "lifestyle": "Lifestyle", "sports": "Sports",
        "news": "News", "finance": "Finance", "government": "Government",
        "education": "Education", "info": "Info",
    }
    for d in DOMAINS:
        nodes.append({
            "id": d, "label": labels[d], "type": "agent",
            "desc": DOMAIN_DESCRIPTIONS[d],
        })
    nodes.append({"id": "writer", "label": "Writer", "type": "writer",
                  "desc": "수집된 정보를 종합해 최종 답변 작성"})

    edges = []
    for d in DOMAINS:
        edges.append({"from": "supervisor", "to": d})
    edges.append({"from": "supervisor", "to": "writer"})
    for d in DOMAINS:
        edges.append({"from": d, "to": "writer"})

    return {"nodes": nodes, "edges": edges}


async def agent_stream(
    question: str,
    model: str | None = None,
    history: list[dict] | None = None,
    thread_id: str | None = None,
) -> AsyncGenerator[tuple[str, dict | str | None], None]:
    """Run the multi-agent pipeline and yield (event_type, data) tuples.

    Event types:
    - "node_start": {"node": "supervisor"|"shopping"|...}
    - "node_end":   {"node": "...", "result_summary": "..."}
    - "edge":       {"from": "...", "to": "..."}
    - "supervisor_decision": {"plan": [...], "reasoning": "..."}
    - "tool_call":   {"domain", "tool", "args"}
    - "tool_result": {"domain", "tool", "result"}
    - "token":       text token (writer streaming)
    - "done":        None
    """
    # 0) Load conversation history from checkpointer if thread_id given.
    #    Falls back to client-supplied history (legacy behavior).
    if thread_id:
        history = get_history(thread_id, limit=10)
    history = history or []

    # 1) Supervisor
    yield "edge", {"from": "START", "to": "supervisor"}
    yield "node_start", {"node": "supervisor"}

    # When model is None or "auto", each stage uses its own tier from config.py
    override = model if model and model != "auto" else None
    sup = await supervisor_node(
        {"question": question, "history": history}, model=override,
    )
    plan: list[str] = sup.get("plan", [])
    reasoning: str = sup.get("_reasoning", "")

    yield "supervisor_decision", {"plan": plan, "reasoning": reasoning}
    yield "node_end", {
        "node": "supervisor",
        "result_summary": f"라우팅: {', '.join(plan) if plan else '(직접 답변)'}",
    }

    # 2) Domain agents (in parallel)
    all_results: list[dict] = []

    if plan:
        # Edges from supervisor to each agent
        for d in plan:
            yield "edge", {"from": "supervisor", "to": d}

        # Mark all as starting
        for d in plan:
            yield "node_start", {"node": d}

        # Use a queue to interleave events from concurrent agents
        queue: asyncio.Queue = asyncio.Queue()

        async def run_one(domain: str):
            async def on_event(ev_type: str, data: dict):
                await queue.put((ev_type, data))
            collected, _ = await run_domain_agent(
                domain, question, model=override,
                on_event=on_event, history=history,
            )
            await queue.put(("__agent_done__", {"domain": domain, "results": collected}))

        tasks = [asyncio.create_task(run_one(d)) for d in plan]
        remaining = len(plan)

        while remaining > 0:
            ev_type, data = await queue.get()
            if ev_type == "__agent_done__":
                remaining -= 1
                domain = data["domain"]
                results = data["results"]
                all_results.extend(results)
                yield "node_end", {
                    "node": domain,
                    "result_summary": f"{len(results)}개 도구 호출 완료",
                }
                yield "edge", {"from": domain, "to": "writer"}
            else:
                yield ev_type, data

        # Drain any pending tasks (should already be done)
        await asyncio.gather(*tasks, return_exceptions=True)
    else:
        yield "edge", {"from": "supervisor", "to": "writer"}

    # 3) Writer
    yield "node_start", {"node": "writer"}

    answer_chunks: list[str] = []
    async for token in writer_stream(
        question, all_results, model=override, history=history,
    ):
        answer_chunks.append(token)
        yield "token", token

    final_answer = "".join(answer_chunks)

    # 4) Persist this turn to the checkpointer
    if thread_id:
        append_messages(thread_id, [
            {"role": "user", "content": question},
            {"role": "assistant", "content": final_answer},
        ])

    yield "node_end", {"node": "writer", "result_summary": "답변 작성 완료"}
    yield "edge", {"from": "writer", "to": "END"}
    yield "done", None
