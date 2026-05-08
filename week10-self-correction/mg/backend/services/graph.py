"""LangGraph StateGraph wiring for week 10 — Self-Correction loop.

Topology (key change vs week 09 — Critic + conditional loop):

    [START] → supervisor → (parallel) → shopping
                                     → lifestyle      ┐
                                     → sports         │
                                     → news           ├→ writer → critic ─┐
                                     → finance        │       ▲           │
                                     → government    │       │           │
                                     → education     │   [score < 7]      │
                                     → info          │   AND iter < 2     │
                                                    ┘       │           │
                                                            └───────────┘
                                                                    │
                                                            [score ≥ 7] → END

The Critic node scores the writer's draft (1-10). If the score is below
threshold AND the iteration cap hasn't been reached, control loops back
to writer with the critic feedback so the answer can be revised.

We expose `agent_stream()` — a hand-rolled async generator that emits
fine-grained SSE events (including critic_score, revision_start) so the
UI can show iteration count and score in real time.
"""

import asyncio
from typing import AsyncGenerator

from agents.state import GraphState
from agents.supervisor import supervisor_node, DOMAIN_DESCRIPTIONS
from agents.domain_agent import run_domain_agent
from agents.writer import writer_stream
from agents.critic import critic_node, build_revision_feedback, PASS_THRESHOLD, MAX_REVISIONS
from services.memory import append_messages, get_history

try:
    from langgraph.graph import StateGraph, END
    _HAS_LANGGRAPH = True
except ImportError:
    _HAS_LANGGRAPH = False


def build_graph():
    """Build a LangGraph StateGraph for inspection/visualization."""
    if not _HAS_LANGGRAPH:
        return None

    g = StateGraph(GraphState)

    DOMAINS = ["shopping", "lifestyle", "sports", "news", "finance",
               "government", "education", "info"]

    g.add_node("supervisor", lambda s: s)
    for d in DOMAINS:
        g.add_node(d, lambda s: s)
    g.add_node("writer", lambda s: s)
    g.add_node("critic", lambda s: s)

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

    g.add_edge("writer", "critic")

    def critic_route(state: GraphState):
        passed = state.get("critic_passed", True)
        iters = state.get("revisions", 0)
        if not passed and iters < MAX_REVISIONS:
            return "writer"
        return END

    g.add_conditional_edges("critic", critic_route, {"writer": "writer", END: END})

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
                  "desc": "수집된 정보를 종합해 최종 답변 작성 (재작성 가능)"})
    nodes.append({"id": "critic", "label": "Critic", "type": "critic",
                  "desc": "답변 품질 검수 (1~10점). 7점 미만이면 Writer 재작성."})

    edges = []
    for d in DOMAINS:
        edges.append({"from": "supervisor", "to": d})
    edges.append({"from": "supervisor", "to": "writer"})
    for d in DOMAINS:
        edges.append({"from": d, "to": "writer"})
    edges.append({"from": "writer", "to": "critic"})
    edges.append({"from": "critic", "to": "writer", "loop": True})

    return {"nodes": nodes, "edges": edges,
            "config": {"pass_threshold": PASS_THRESHOLD, "max_revisions": MAX_REVISIONS}}


async def agent_stream(
    question: str,
    model: str | None = None,
    history: list[dict] | None = None,
    thread_id: str | None = None,
) -> AsyncGenerator[tuple[str, dict | str | None], None]:
    """Run the multi-agent pipeline with Self-Correction loop.

    Event types:
    - "node_start" / "node_end" / "edge"       — graph topology
    - "supervisor_decision"                    — routing plan
    - "tool_call" / "tool_result"              — domain agent activity
    - "token"                                  — writer streaming token
    - "writer_iteration"                       — {iteration, is_revision}
    - "critic_score"                           — {score, passed, issues, suggestions, iteration}
    - "revision_start"                         — {iteration} (writer re-write)
    - "done"                                   — final
    """
    # Load conversation history
    if thread_id:
        history = get_history(thread_id, limit=10)
    history = history or []

    # 1) Supervisor
    yield "edge", {"from": "START", "to": "supervisor"}
    yield "node_start", {"node": "supervisor"}

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
        for d in plan:
            yield "edge", {"from": "supervisor", "to": d}
        for d in plan:
            yield "node_start", {"node": d}

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

        await asyncio.gather(*tasks, return_exceptions=True)
    else:
        yield "edge", {"from": "supervisor", "to": "writer"}

    # 3) Writer + Critic loop (Self-Correction)
    iteration = 0
    revision_feedback: str | None = None
    previous_draft: str | None = None
    final_answer = ""
    critique: dict | None = None

    while True:
        iteration += 1
        is_revision = iteration > 1

        yield "writer_iteration", {
            "iteration": iteration,
            "is_revision": is_revision,
        }
        if is_revision:
            yield "revision_start", {"iteration": iteration}
        yield "node_start", {"node": "writer"}

        answer_chunks: list[str] = []
        async for token in writer_stream(
            question, all_results,
            model=override, history=history,
            revision_feedback=revision_feedback,
            previous_draft=previous_draft,
        ):
            answer_chunks.append(token)
            yield "token", token

        final_answer = "".join(answer_chunks)
        yield "node_end", {
            "node": "writer",
            "result_summary": (
                f"재작성 완료 (iter {iteration})" if is_revision
                else "초안 작성 완료"
            ),
        }

        # 4) Critic
        yield "edge", {"from": "writer", "to": "critic"}
        yield "node_start", {"node": "critic"}

        critique = await critic_node(
            question=question,
            draft_answer=final_answer,
            tool_results=all_results,
            iteration=iteration,
            model=override,
        )

        yield "critic_score", critique
        yield "node_end", {
            "node": "critic",
            "result_summary": (
                f"점수 {critique['score']}/10 — "
                f"{'통과' if critique['passed'] else '재작성 필요'}"
            ),
        }

        # Decide: pass / revise / give up
        if critique["passed"] or iteration > MAX_REVISIONS:
            break

        # Loop back: writer re-writes with critic feedback
        revision_feedback = build_revision_feedback(critique)
        previous_draft = final_answer
        yield "edge", {"from": "critic", "to": "writer", "loop": True}

    # 5) Persist to checkpointer
    if thread_id:
        append_messages(thread_id, [
            {"role": "user", "content": question},
            {"role": "assistant", "content": final_answer},
        ])

    yield "edge", {"from": "critic", "to": "END"}
    yield "done", {
        "final_score": critique["score"] if critique else None,
        "iterations": iteration,
    }
