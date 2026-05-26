"""LangGraph wiring for week 11 — Plan-and-Execute.

Topology:

    [START] → Planner → Executor(step N) → Replanner ─┐
                            ▲                          │
                            │  ┌─ continue ────────────┤
                            │  ├─ revise (new plan) ───┘
                            │  └─ finish ─────┐
                            │                  ▼
                            │              Writer → Critic ─[loop]→ Writer
                            │                                       │
                            │                          [pass]──→ END
                            └─ (advance to next pending step)

Key changes vs week 10:
- Supervisor → Planner (produces ordered list of steps, not just routes)
- Executor advances one step at a time, dispatches to relevant domain agent
- Replanner decides after each step: continue / revise / finish
- Writer + Critic (reused from week 10) compose the final answer
"""

import asyncio
from typing import AsyncGenerator

from agents.state import GraphState
from agents.supervisor import DOMAIN_DESCRIPTIONS
from agents.planner import planner_node
from agents.replanner import replanner_node, MAX_REPLAN
from agents.domain_agent import run_domain_agent
from agents.retriever import run_retriever, format_chunks_for_writer
from agents.writer import writer_stream
from agents.critic import critic_node, build_revision_feedback, PASS_THRESHOLD, MAX_REVISIONS
from services.memory import append_messages, get_history

try:
    from langgraph.graph import StateGraph, END
    _HAS_LANGGRAPH = True
except ImportError:
    _HAS_LANGGRAPH = False


def build_graph():
    if not _HAS_LANGGRAPH:
        return None

    g = StateGraph(GraphState)
    DOMAINS = ["shopping", "lifestyle", "sports", "news", "finance",
               "government", "education", "info", "documents", "data",
               "travel", "culture", "health"]

    g.add_node("planner", lambda s: s)
    g.add_node("executor", lambda s: s)
    g.add_node("replanner", lambda s: s)
    for d in DOMAINS:
        g.add_node(d, lambda s: s)
    g.add_node("writer", lambda s: s)
    g.add_node("critic", lambda s: s)

    g.set_entry_point("planner")

    def planner_route(state: GraphState):
        plan = state.get("plan", []) or []
        if not plan:
            return "writer"
        return "executor"

    g.add_conditional_edges("planner", planner_route,
                            {"executor": "executor", "writer": "writer"})
    g.add_edge("executor", "replanner")

    def replanner_route(state: GraphState):
        if state.get("_replan_action") == "finish":
            return "writer"
        plan = state.get("plan", []) or []
        if any(s.get("status") == "pending" for s in plan):
            return "executor"
        return "writer"

    g.add_conditional_edges("replanner", replanner_route,
                            {"executor": "executor", "writer": "writer"})
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
    DOMAINS = ["shopping", "lifestyle", "sports", "news", "finance",
               "government", "education", "info", "documents", "data",
               "travel", "culture", "health"]
    nodes = [
        {"id": "planner", "label": "Planner", "type": "router",
         "desc": "질문을 단계별 plan 으로 분해"},
        {"id": "executor", "label": "Executor", "type": "executor",
         "desc": "각 step 을 해당 도메인 에이전트로 dispatch"},
        {"id": "replanner", "label": "Replanner", "type": "router",
         "desc": "단계 결과를 보고 continue / revise / finish 결정"},
    ]
    labels = {
        "shopping": "Shopping", "lifestyle": "Lifestyle", "sports": "Sports",
        "news": "News", "finance": "Finance", "government": "Government",
        "education": "Education", "info": "Info", "documents": "Documents",
        "data": "Data", "travel": "Travel", "culture": "Culture", "health": "Health",
    }
    for d in DOMAINS:
        nodes.append({
            "id": d, "label": labels[d], "type": "agent",
            "desc": DOMAIN_DESCRIPTIONS[d],
        })
    nodes.append({"id": "writer", "label": "Writer", "type": "writer",
                  "desc": "수집된 정보를 종합해 답변 작성"})
    nodes.append({"id": "critic", "label": "Critic", "type": "critic",
                  "desc": "답변 채점 (1~10). 7점 미만이면 재작성"})

    edges = [
        {"from": "planner", "to": "executor"},
        {"from": "planner", "to": "writer"},
        {"from": "executor", "to": "replanner"},
        {"from": "replanner", "to": "executor", "loop": True},
        {"from": "replanner", "to": "writer"},
        {"from": "writer", "to": "critic"},
        {"from": "critic", "to": "writer", "loop": True},
    ]
    for d in DOMAINS:
        edges.append({"from": "executor", "to": d})
        edges.append({"from": d, "to": "executor"})

    return {
        "nodes": nodes,
        "edges": edges,
        "config": {
            "pass_threshold": PASS_THRESHOLD,
            "max_revisions": MAX_REVISIONS,
            "max_replan": MAX_REPLAN,
        },
    }


def _summarize_results(tool_results: list[dict]) -> str:
    if not tool_results:
        return "(도구 호출 없음)"
    parts = []
    for r in tool_results:
        snippet = (r.get("result") or "")[:200]
        parts.append(f"{r.get('tool')}({r.get('args', {})}) → {snippet}")
    return " | ".join(parts)[:600]


async def agent_stream(
    question: str,
    model: str | None = None,
    history: list[dict] | None = None,
    thread_id: str | None = None,
) -> AsyncGenerator[tuple[str, dict | str | None], None]:
    """Plan-and-Execute pipeline.

    Event types added in week 11:
    - plan_created  / step_start / step_done / replan_decision
    Plus all events from week 10 (token, critic_score, writer_iteration, ...)
    """
    if thread_id:
        history = get_history(thread_id, limit=10)
    history = history or []

    override = model if model and model != "auto" else None

    # 1) Planner
    yield "edge", {"from": "START", "to": "planner"}
    yield "node_start", {"node": "planner"}

    plan_out = await planner_node(
        {"question": question, "history": history}, model=override,
    )
    plan: list[dict] = plan_out.get("plan", [])
    plan_reasoning = plan_out.get("_reasoning", "")

    yield "plan_created", {
        "plan": [
            {"id": s["id"], "domain": s["domain"], "task": s["task"]}
            for s in plan
        ],
        "reasoning": plan_reasoning,
    }
    yield "node_end", {
        "node": "planner",
        "result_summary": f"{len(plan)} 단계 plan 생성"
        if plan else "도구 불필요 — 직접 답변",
    }

    all_tool_results: list[dict] = []
    replan_count = 0

    # 2) Execution loop
    while True:
        pending = [s for s in plan if s.get("status") == "pending"]
        if not pending:
            break

        step = pending[0]
        domain = step.get("domain")

        yield "edge", {"from": "planner" if step["id"] == 1 else "replanner",
                       "to": "executor"}
        yield "node_start", {"node": "executor"}
        yield "step_start", {"step": {
            "id": step["id"], "domain": domain, "task": step["task"],
        }}

        collected: list[dict] = []
        if domain == "documents":
            # ── Agentic RAG path — invoke the Retriever instead of a generic agent
            yield "edge", {"from": "executor", "to": "documents"}
            yield "node_start", {"node": "documents"}

            queue: asyncio.Queue = asyncio.Queue()

            async def on_event_q(ev_type: str, data: dict):
                await queue.put((ev_type, data))

            ret_task = asyncio.create_task(run_retriever(
                step["task"], history=history, model=override,
                on_event=on_event_q,
            ))

            while not ret_task.done() or not queue.empty():
                try:
                    ev_type, data = await asyncio.wait_for(
                        queue.get(), timeout=0.05,
                    )
                    yield ev_type, data
                except asyncio.TimeoutError:
                    if ret_task.done():
                        break

            ret_result = await ret_task
            chunks = ret_result.get("chunks", []) or []
            # Wrap chunks as a tool_result so the Writer treats them uniformly
            citations_payload = format_chunks_for_writer(chunks)
            collected = [{
                "domain": "documents",
                "tool": "agentic_retriever",
                "args": {"task": step["task"]},
                "result": citations_payload,
                "_chunks": [{
                    "doc_name": c.doc_name,
                    "page": c.page,
                    "score": round(c.score or 0, 3),
                    "text": c.text,
                } for c in chunks],
            }]
            all_tool_results.extend(collected)

            yield "node_end", {
                "node": "documents",
                "result_summary": f"{len(chunks)}개 chunk 검색 (점수 {ret_result.get('final_score', 0)}/5)",
            }
            yield "edge", {"from": "documents", "to": "executor"}

        elif domain:
            yield "edge", {"from": "executor", "to": domain}
            yield "node_start", {"node": domain}

            queue: asyncio.Queue = asyncio.Queue()

            async def on_event_q(ev_type: str, data: dict):
                await queue.put((ev_type, data))

            agent_task = asyncio.create_task(run_domain_agent(
                domain, step["task"], model=override,
                on_event=on_event_q, history=history,
            ))

            while not agent_task.done() or not queue.empty():
                try:
                    ev_type, data = await asyncio.wait_for(
                        queue.get(), timeout=0.05,
                    )
                    yield ev_type, data
                except asyncio.TimeoutError:
                    if agent_task.done():
                        break

            collected_results, _ = await agent_task
            collected = collected_results
            all_tool_results.extend(collected)

            yield "node_end", {
                "node": domain,
                "result_summary": f"{len(collected)} 개 도구 호출",
            }
            yield "edge", {"from": domain, "to": "executor"}

        for s in plan:
            if s["id"] == step["id"]:
                s["status"] = "done"
                s["result"] = {
                    "summary": _summarize_results(collected),
                    "tool_count": len(collected),
                }
                break

        yield "step_done", {
            "step": {
                "id": step["id"], "domain": domain, "task": step["task"],
                "results_summary": _summarize_results(collected),
                "tool_count": len(collected),
            }
        }
        yield "node_end", {"node": "executor", "result_summary": f"step {step['id']} 완료"}

        # Replanner
        yield "edge", {"from": "executor", "to": "replanner"}
        yield "node_start", {"node": "replanner"}

        decision = await replanner_node({"question": question, "plan": plan}, model=override)
        action = decision["action"]
        rp_reasoning = decision["_reasoning"]
        new_plan = decision.get("new_plan", [])

        yield "replan_decision", {
            "action": action, "reasoning": rp_reasoning,
            "new_plan": [
                {"id": s["id"], "domain": s["domain"], "task": s["task"]}
                for s in new_plan
            ] if action == "revise" else [],
        }
        yield "node_end", {
            "node": "replanner",
            "result_summary": f"{action} ({rp_reasoning[:40]})",
        }

        if action == "finish":
            for s in plan:
                if s.get("status") == "pending":
                    s["status"] = "skipped"
            break

        if action == "revise" and replan_count < MAX_REPLAN:
            replan_count += 1
            kept = [s for s in plan if s.get("status") in ("done", "skipped")]
            plan = kept + new_plan
            continue

    # 3) Writer + Critic loop
    yield "edge", {"from": "replanner", "to": "writer"}

    iteration = 0
    revision_feedback: str | None = None
    previous_draft: str | None = None
    final_answer = ""
    critique: dict | None = None

    while True:
        iteration += 1
        is_revision = iteration > 1

        yield "writer_iteration", {"iteration": iteration, "is_revision": is_revision}
        if is_revision:
            yield "revision_start", {"iteration": iteration}
        yield "node_start", {"node": "writer"}

        answer_chunks: list[str] = []
        async for token in writer_stream(
            question, all_tool_results,
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

        yield "edge", {"from": "writer", "to": "critic"}
        yield "node_start", {"node": "critic"}

        critique = await critic_node(
            question=question,
            draft_answer=final_answer,
            tool_results=all_tool_results,
            iteration=iteration,
            model=override,
        )

        yield "critic_score", critique
        yield "node_end", {
            "node": "critic",
            "result_summary": f"점수 {critique['score']}/10 — {'통과' if critique['passed'] else '재작성'}",
        }

        if critique["passed"] or iteration > MAX_REVISIONS:
            break

        revision_feedback = build_revision_feedback(critique)
        previous_draft = final_answer
        yield "edge", {"from": "critic", "to": "writer", "loop": True}

    if thread_id:
        append_messages(thread_id, [
            {"role": "user", "content": question},
            {"role": "assistant", "content": final_answer},
        ])

    yield "edge", {"from": "critic", "to": "END"}
    yield "done", {
        "final_score": critique["score"] if critique else None,
        "iterations": iteration,
        "plan_steps": len(plan),
        "replan_count": replan_count,
    }
