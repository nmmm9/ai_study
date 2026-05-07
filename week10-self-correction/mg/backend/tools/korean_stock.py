"""한국 주식 검색 — KRX via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="korean_stock_search",
    description="한국 주식 종목을 검색해 종목코드와 시세 정보를 조회합니다 (KRX 공식 데이터).",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "종목명 또는 종목코드 (예: 삼성전자, 005930)"},
            "bas_dd": {"type": "string", "description": "기준일자 YYYYMMDD (선택)"},
        },
        "required": ["query"],
    },
)
async def korean_stock_search(query: str, bas_dd: str | None = None) -> dict:
    params = {"q": query}
    if bas_dd:
        params["bas_dd"] = bas_dd
    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.get(f"{PROXY}/v1/korean-stock/search", params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"주식 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}
