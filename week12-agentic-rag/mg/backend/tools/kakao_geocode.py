"""카카오 지오코딩 — 주소/장소명을 위도/경도로 변환."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="kakao_geocode",
    description="주소 또는 장소명을 위도/경도 좌표로 변환합니다. 다른 위치 기반 도구의 좌표 인자로 사용됩니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "주소 또는 장소명 (예: '서울 강남역', '경복궁')"},
        },
        "required": ["query"],
    },
)
async def kakao_geocode(query: str) -> dict:
    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.get(
            f"{PROXY}/v1/kakao-local/geocode",
            params={"query": query},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"지오코딩 실패 (status {resp.status_code})", "body": resp.text[:300]}
