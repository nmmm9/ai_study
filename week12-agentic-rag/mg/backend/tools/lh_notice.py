"""LH 청약 공고 검색 — 공공데이터포털 via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="lh_notice_search",
    description="LH 한국토지주택공사 청약 공고를 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "region": {"type": "string", "description": "광역시도명 (예: 서울특별시, 부산광역시)"},
            "status": {"type": "string", "description": "공고 상태 (기본: 공고중)", "default": "공고중"},
            "page_size": {"type": "integer", "default": 20},
        },
    },
)
async def lh_notice_search(region: str | None = None, status: str = "공고중", page_size: int = 20) -> dict:
    params: dict = {"panSs": status, "pageSize": page_size}
    if region:
        params["cnpCdNm"] = region
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{PROXY}/v1/lh-notice/search", params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"LH 공고 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}
