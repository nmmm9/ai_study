"""서울 핫스팟 실시간 혼잡도 — 서울 도시데이터 via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="seoul_density",
    description="서울 121개 주요 핫스팟의 실시간 혼잡도와 인구 현황을 조회합니다. (예: '강남역', '명동', '홍대입구', '경복궁')",
    parameters={
        "type": "object",
        "properties": {
            "place": {"type": "string", "description": "핫스팟 이름 (예: 강남역, 명동, 홍대입구)"},
        },
        "required": ["place"],
    },
)
async def seoul_density(place: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/seoul-density/citydata",
            params={"place": place},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"서울 혼잡도 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}
