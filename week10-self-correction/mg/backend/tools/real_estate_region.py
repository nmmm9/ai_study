"""법정동/행정구역 코드 검색 — k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="real_estate_region_code",
    description="법정동/행정구역 이름으로 lawd_cd(부동산 실거래가 조회용 5자리 코드)를 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "지역명 (예: 강남구, 수원시 영통구)"},
        },
        "required": ["query"],
    },
)
async def real_estate_region_code(query: str) -> dict:
    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.get(
            f"{PROXY}/v1/real-estate/region-code", params={"q": query}
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"행정구역 코드 검색 실패 (status {resp.status_code})"}
