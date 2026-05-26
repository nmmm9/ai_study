"""근처 공영주차장 검색 — 공공데이터포털 via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="parking_lot_nearby",
    description="근처 공영주차장을 검색합니다. 위도/경도와 주소 힌트를 입력하세요.",
    parameters={
        "type": "object",
        "properties": {
            "latitude": {"type": "number", "description": "위도"},
            "longitude": {"type": "number", "description": "경도"},
            "address_hint": {"type": "string", "description": "예: 서울특별시 종로구"},
            "radius": {"type": "integer", "description": "반경(미터). 기본 1500", "default": 1500},
            "limit": {"type": "integer", "default": 5},
        },
        "required": ["latitude", "longitude"],
    },
)
async def parking_lot_nearby(latitude: float, longitude: float,
                              address_hint: str = "", radius: int = 1500,
                              limit: int = 5) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius,
        "limit": limit,
    }
    if address_hint:
        params["address_hint"] = address_hint
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{PROXY}/v1/parking-lots/search", params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"주차장 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}
