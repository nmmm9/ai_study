"""의약품 안전 정보 — 식약처 via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="mfds_drug_safety",
    description="식약처 의약품 안전 정보(e약은요)를 조회합니다. 의약품 이름을 입력하세요.",
    parameters={
        "type": "object",
        "properties": {
            "item_name": {"type": "string", "description": "의약품 이름 (예: 타이레놀)"},
            "limit": {"type": "integer", "default": 5},
        },
        "required": ["item_name"],
    },
)
async def mfds_drug_safety(item_name: str, limit: int = 5) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/mfds/drug-safety/lookup",
            params={"itemName": item_name, "limit": limit},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"의약품 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}
