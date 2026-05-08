"""서울 지하철 실시간 도착 — k-skill-proxy 경유."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="seoul_subway_arrival",
    description="서울 지하철 실시간 도착 정보를 역명으로 조회합니다. 예: 강남, 홍대입구, 서울역",
    parameters={
        "type": "object",
        "properties": {
            "station": {"type": "string", "description": "역명 (예: 강남, 홍대입구, 서울역, 신도림)"},
        },
        "required": ["station"],
    },
)
async def seoul_subway_arrival(station: str) -> dict:
    # '역' 제거 (API가 역명만 받음)
    station = station.replace("역", "").strip()

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{PROXY}/v1/seoul-subway/arrival",
            params={"stationName": station},
        )
        if resp.status_code != 200:
            return {"error": f"지하철 도착 조회 실패 (status {resp.status_code})"}
        return resp.json()
