"""Tool Registry — Hermes-inspired decorator pattern for tool registration.

Usage:
    @register_tool(
        name="lotto_results",
        description="한국 로또 당첨번호를 조회합니다",
        parameters={
            "type": "object",
            "properties": {
                "round": {"type": "integer", "description": "회차 번호 (없으면 최신)"}
            },
        }
    )
    async def lotto_results(round: int = None) -> str:
        ...
"""

from typing import Callable, Any
import json

_tools: dict[str, dict] = {}


def register_tool(
    name: str,
    description: str,
    parameters: dict | None = None,
):
    """Decorator to register a function as an agent tool."""
    def decorator(func: Callable) -> Callable:
        _tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters or {"type": "object", "properties": {}},
            "handler": func,
        }
        return func
    return decorator


def get_all_tools() -> list[dict]:
    """Get OpenAI-compatible tool schemas for all registered tools."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in _tools.values()
    ]


async def execute_tool(name: str, arguments: dict) -> str:
    """Execute a registered tool by name. Returns result as string."""
    tool = _tools.get(name)
    if not tool:
        return json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)

    try:
        result = await tool["handler"](**arguments)
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def list_tool_names() -> list[str]:
    """List all registered tool names."""
    return list(_tools.keys())
