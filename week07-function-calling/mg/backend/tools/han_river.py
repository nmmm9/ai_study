"""한강 수위 조회 — HRFCO via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="han_river_water_level",
    description="한강 수위와 유량을 관측소명으로 조회합니다. 예: 잠실, 여의도, 한강대교",
    parameters={
        "type": "object",
        "properties": {
            "station": {"type": "string", "description": "관측소명 (예: 잠실, 한강대교)"},
        },
        "required": ["station"],
    },
)
async def han_river_water_level(station: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{PROXY}/v1/han-river/water-level",
            params={"stationName": station},
        )
        if resp.status_code != 200:
            return {"error": f"조회 실패 (status {resp.status_code})"}
        return resp.json()
