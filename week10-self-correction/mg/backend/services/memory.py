"""Conversation memory via LangGraph InMemorySaver checkpointer.

This module demonstrates LangGraph's checkpointer pattern: a tiny
single-node graph used purely as a thread-keyed key-value store.

The same code can be swapped to SqliteSaver / PostgresSaver for
persistence by changing one line.

Public API:
- append_messages(thread_id, messages)
- get_history(thread_id, limit)
- list_threads()
- delete_thread(thread_id)
- get_thread_summary(thread_id)
"""

from typing import Annotated, TypedDict
from operator import add

from langgraph.graph import StateGraph, END

try:
    from langgraph.checkpoint.memory import InMemorySaver as _Saver
except ImportError:  # pragma: no cover  — fallback for older versions
    from langgraph.checkpoint.memory import MemorySaver as _Saver


class ConvState(TypedDict):
    messages: Annotated[list[dict], add]


def _passthrough(_state: ConvState) -> dict:
    # Return empty update — input messages already merged via the
    # `add` reducer on graph entry. Returning state again would cause
    # the reducer to concatenate them a second time.
    return {}


_builder = StateGraph(ConvState)
_builder.add_node("turn", _passthrough)
_builder.set_entry_point("turn")
_builder.add_edge("turn", END)

_checkpointer = _Saver()
_mem_graph = _builder.compile(checkpointer=_checkpointer)

# Side index of thread metadata (for listing) — checkpointer alone
# doesn't expose a clean enumerate API across versions.
_thread_index: dict[str, dict] = {}


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def append_messages(thread_id: str, messages: list[dict]) -> None:
    """Append messages (role, content dicts) to a thread's checkpointed state.

    The Annotated[list, add] reducer concatenates the new messages onto
    the existing list automatically.
    """
    if not messages:
        return
    _mem_graph.invoke({"messages": messages}, config=_config(thread_id))

    # Update side index — first user message becomes thread title
    if thread_id not in _thread_index:
        first_user = next((m for m in messages if m.get("role") == "user"), None)
        title = (first_user or {}).get("content", "(no title)")
        _thread_index[thread_id] = {
            "thread_id": thread_id,
            "title": title[:60],
            "message_count": 0,
        }
    _thread_index[thread_id]["message_count"] += len(messages)


def get_history(thread_id: str, limit: int = 10) -> list[dict]:
    """Retrieve recent conversation history (most recent at end)."""
    if not thread_id:
        return []
    snapshot = _mem_graph.get_state(_config(thread_id))
    if not snapshot or not snapshot.values:
        return []
    msgs = snapshot.values.get("messages", []) or []
    return msgs[-limit:] if limit else list(msgs)


def list_threads() -> list[dict]:
    """List threads with title and message count, newest first."""
    return list(_thread_index.values())[::-1]


def delete_thread(thread_id: str) -> bool:
    """Best-effort thread removal (limited by checkpointer impl)."""
    removed = _thread_index.pop(thread_id, None) is not None
    # InMemorySaver storage is internal; we leave the checkpoint dangling.
    return removed


def get_thread_summary(thread_id: str) -> dict | None:
    return _thread_index.get(thread_id)
