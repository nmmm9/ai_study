"""Shared state for the multi-agent graph.

The graph state flows through every node. Each node may append to
`messages` (LLM conversation), `events` (UI trace), and `tool_results`
(for the writer to consult).
"""

from typing import Annotated, Literal, TypedDict
from operator import add


AgentName = Literal["supervisor", "shopping", "lifestyle", "sports", "info", "writer"]


class GraphState(TypedDict, total=False):
    # User question (immutable)
    question: str

    # OpenAI-style chat messages
    messages: Annotated[list[dict], add]

    # Agents that the supervisor wants to dispatch
    plan: list[str]

    # Tracks which domain agents have already completed
    completed_agents: Annotated[list[str], add]

    # Tool execution results, keyed by domain — writer consumes this
    tool_results: Annotated[list[dict], add]

    # Final answer text (writer outputs here)
    final_answer: str

    # Streaming hints — set by Supervisor before transitioning
    next_agent: AgentName
