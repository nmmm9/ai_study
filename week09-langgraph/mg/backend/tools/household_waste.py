"""생활쓰레기 배출정보 — 공공데이터포털 via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="household_waste_info",
    description="시군구별 생활쓰레기 배출 요일/방법/규격봉투 정보를 조회합니다. 시군구명을 정확히 입력하세요 (예: 강남구, 수원시).",
    parameters={
        "type": "object",
        "properties": {
            "sgg_name": {"type": "string", "description": "시군구명 (예: 강남구)"},
        },
        "required": ["sgg_name"],
    },
)
async def household_waste_info(sgg_name: str) -> dict:
    params = {
        "cond[SGG_NM::LIKE]": sgg_name,
        "pageNo": 1,
        "numOfRows": 100,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{PROXY}/v1/household-waste/info", params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"생활쓰레기 정보 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}
