"""식약처 추가 정보 — 부적합 검사, 회수, 건강식품 원료 — k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="mfds_food_inspection_fail",
    description="식약처 식품 부적합 검사 결과를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "식품명 키워드"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
)
async def mfds_food_inspection_fail(query: str, limit: int = 10) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/mfds/food-safety/inspection-fail",
            params={"query": query, "limit": limit},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"부적합 식품 조회 실패 (status {resp.status_code})"}


@register_tool(
    name="mfds_food_recall",
    description="식약처 식품 회수/판매중지 보고를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "제품명 키워드"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
)
async def mfds_food_recall(query: str, limit: int = 10) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/mfds/food-safety/product-report",
            params={"query": query, "limit": limit},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"회수식품 조회 실패 (status {resp.status_code})"}


@register_tool(
    name="mfds_health_food_ingredient",
    description="식약처 건강기능식품 원료 정보를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "원료명 키워드"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
)
async def mfds_health_food_ingredient(query: str, limit: int = 10) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/mfds/food-safety/health-food-ingredient",
            params={"query": query, "limit": limit},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"건강식품 원료 조회 실패 (status {resp.status_code})"}
