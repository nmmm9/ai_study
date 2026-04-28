"""한국 주식 추가 정보 — KRX via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="korean_stock_trade_info",
    description="한국 주식 종목코드의 일별 시세(시가/고가/저가/종가/거래량)를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "isuCd": {"type": "string", "description": "종목코드 (예: 005930)"},
            "bas_dd": {"type": "string", "description": "기준일자 YYYYMMDD (없으면 최신)"},
        },
        "required": ["isuCd"],
    },
)
async def korean_stock_trade_info(isuCd: str, bas_dd: str | None = None) -> dict:
    params = {"isuCd": isuCd}
    if bas_dd:
        params["bas_dd"] = bas_dd
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{PROXY}/v1/korean-stock/trade-info", params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"시세 조회 실패 (status {resp.status_code})"}


@register_tool(
    name="korean_stock_base_info",
    description="한국 주식 종목의 기본 정보(상장일, 시장, 업종, 액면가)를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "isuCd": {"type": "string", "description": "종목코드 (예: 005930)"},
        },
        "required": ["isuCd"],
    },
)
async def korean_stock_base_info(isuCd: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/korean-stock/base-info", params={"isuCd": isuCd}
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"종목 기본정보 조회 실패 (status {resp.status_code})"}
