"""식품 안전 정보 — 식약처 via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="mfds_food_safety",
    description="식약처 부적합/회수 식품 안전 정보를 조회합니다. 식품명 키워드를 입력하세요.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "식품명 또는 키워드"},
            "limit": {"type": "integer", "default": 5},
        },
        "required": ["query"],
    },
)
async def mfds_food_safety(query: str, limit: int = 5) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/mfds/food-safety/search",
            params={"query": query, "limit": limit},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"식품안전 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}
