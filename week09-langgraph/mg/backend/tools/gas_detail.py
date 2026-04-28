"""주유소 상세 정보 — Opinet via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="cheap_gas_detail",
    description="특정 주유소의 상세 정보(부가서비스, 셀프 여부, 영업시간)를 조회합니다. 주유소 ID 필요.",
    parameters={
        "type": "object",
        "properties": {
            "uniId": {"type": "string", "description": "주유소 고유 ID (cheap_gas_nearby 결과의 uniId)"},
        },
        "required": ["uniId"],
    },
)
async def cheap_gas_detail(uniId: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/opinet/detail", params={"id": uniId}
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"주유소 상세 조회 실패 (status {resp.status_code})"}
