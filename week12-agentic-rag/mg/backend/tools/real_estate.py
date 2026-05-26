"""부동산 실거래가 조회 — MOLIT via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="real_estate_price",
    description="한국 부동산 실거래가를 조회합니다. 지역명과 매물 유형을 지정하세요.",
    parameters={
        "type": "object",
        "properties": {
            "region": {"type": "string", "description": "지역명 (예: 강남구, 서초구, 해운대구)"},
            "asset_type": {"type": "string", "enum": ["apartment", "officetel", "villa"], "description": "매물 유형", "default": "apartment"},
            "year_month": {"type": "string", "description": "조회 연월 (YYYYMM, 없으면 최근)"},
        },
        "required": ["region"],
    },
)
async def real_estate_price(region: str, asset_type: str = "apartment", year_month: str = None) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        # Step 1: Get region code
        code_resp = await client.get(
            f"{PROXY}/v1/real-estate/region-code",
            params={"q": region},
        )
        if code_resp.status_code != 200:
            return {"error": "지역 코드 조회 실패"}

        code_data = code_resp.json()
        # Proxy 응답: {"results": [{"lawd_cd": "11680", "name": "서울특별시 강남구"}], ...}
        results_list = code_data.get("results", [])
        if isinstance(results_list, list) and results_list:
            lawd_cd = results_list[0].get("lawd_cd", "")
        else:
            lawd_cd = code_data.get("lawd_cd", code_data.get("code", ""))
        if not lawd_cd:
            return {"error": f"'{region}' 지역을 찾을 수 없습니다"}

        # Step 2: Get transaction data
        from datetime import datetime
        if not year_month:
            year_month = datetime.now().strftime("%Y%m")

        resp = await client.get(
            f"{PROXY}/v1/real-estate/{asset_type}/trade",
            params={"lawd_cd": lawd_cd, "deal_ymd": year_month},
        )
        if resp.status_code != 200:
            return {"error": "실거래가 조회 실패"}
        return resp.json()
