"""당근 4종 — 중고차/알바/부동산/중고거래.

각 스킬은 동일 패턴:
- 지역 키워드 → region_id 조회 (regions/keyword)
- search 페이지 HTML 파싱 또는 list API
- 상세는 detail page __NEXT_DATA__

여기서는 search 만 wrap (detail 은 URL 만 반환).
"""

import re
import json
import httpx
from urllib.parse import quote_plus
from tools.registry import register_tool

DAANGN_API = "https://www.daangn.com/kr/api/v1"
DAANGN_BASE = "https://www.daangn.com/kr"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


async def _resolve_region(client: httpx.AsyncClient, keyword: str) -> dict | None:
    try:
        resp = await client.get(f"{DAANGN_API}/regions/keyword", params={"keyword": keyword})
        if resp.status_code == 200:
            data = resp.json()
            regions = data.get("regions") or data.get("data") or []
            if regions:
                return regions[0]
    except Exception:
        pass
    return None


async def _next_data_search(path: str, params: dict) -> dict:
    """Fetch a daangn HTML page and extract __NEXT_DATA__ JSON."""
    url = f"{DAANGN_BASE}{path}"
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}, follow_redirects=True) as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return {"error": f"daangn 조회 실패 (status {resp.status_code})"}
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        if not m:
            return {"error": "__NEXT_DATA__ 파싱 실패", "snippet": resp.text[:500]}
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError as e:
            return {"error": f"JSON 파싱 실패: {e}"}


@register_tool(
    name="daangn_used_goods_search",
    description="당근 중고거래 매물을 키워드와 지역으로 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "검색 키워드 (예: '맥북', '아이폰')"},
            "region": {"type": "string", "description": "지역명 (예: '합정동')"},
            "limit": {"type": "integer", "default": 5},
        },
        "required": ["query"],
    },
)
async def daangn_used_goods_search(query: str, region: str | None = None, limit: int = 5) -> dict:
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}) as client:
        region_info = await _resolve_region(client, region) if region else None

    params: dict = {"search": query}
    if region_info:
        params["in"] = region_info.get("name", region)
    data = await _next_data_search("/buy-sell", params)
    if "error" in data:
        return data

    # Try common paths
    items = []
    try:
        props = data.get("props", {}).get("pageProps", {})
        items = props.get("articles") or props.get("items") or props.get("results") or []
    except Exception:
        pass

    return {
        "query": query,
        "region": region_info.get("name") if region_info else None,
        "count": len(items),
        "items": items[:limit],
    }


@register_tool(
    name="daangn_cars_search",
    description="당근중고차 매물을 검색합니다. 차종/지역/가격 조건으로 필터링.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "차종 키워드 (예: '레이', '아반떼')"},
            "region": {"type": "string"},
            "price_max": {"type": "integer", "description": "최대 가격(원)"},
            "limit": {"type": "integer", "default": 5},
        },
    },
)
async def daangn_cars_search(query: str | None = None, region: str | None = None,
                              price_max: int | None = None, limit: int = 5) -> dict:
    params: dict = {}
    if query:
        params["search"] = query
    if price_max:
        params["max"] = price_max
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}) as client:
        if region:
            r = await _resolve_region(client, region)
            if r:
                params["in"] = r.get("name", region)

    data = await _next_data_search("/cars", params)
    if "error" in data:
        return data
    items = []
    try:
        props = data.get("props", {}).get("pageProps", {})
        items = props.get("articles") or props.get("cars") or props.get("results") or []
    except Exception:
        pass
    return {"query": query, "region": region, "count": len(items), "items": items[:limit]}


@register_tool(
    name="daangn_jobs_search",
    description="당근알바 공고를 키워드와 지역으로 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "직종/업종 키워드 (예: '카페', '편의점')"},
            "region": {"type": "string"},
            "limit": {"type": "integer", "default": 5},
        },
        "required": ["query"],
    },
)
async def daangn_jobs_search(query: str, region: str | None = None, limit: int = 5) -> dict:
    params: dict = {"search": query}
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}) as client:
        if region:
            r = await _resolve_region(client, region)
            if r:
                params["in"] = r.get("name", region)
    data = await _next_data_search("/jobs", params)
    if "error" in data:
        return data
    items = []
    try:
        props = data.get("props", {}).get("pageProps", {})
        items = props.get("articles") or props.get("jobs") or props.get("results") or []
    except Exception:
        pass
    return {"query": query, "region": region, "count": len(items), "items": items[:limit]}


@register_tool(
    name="daangn_realty_search",
    description="당근부동산 매물을 지역과 거래 유형으로 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "region": {"type": "string", "description": "지역명 (예: '합정동')"},
            "sales_type": {"type": "string", "enum": ["APARTMENT", "OFFICETEL", "HOUSING", "STORE"]},
            "trade_type": {"type": "string", "enum": ["SALE", "LEASE", "MONTHLY_RENT"]},
            "limit": {"type": "integer", "default": 5},
        },
        "required": ["region"],
    },
)
async def daangn_realty_search(region: str, sales_type: str | None = None,
                                trade_type: str | None = None, limit: int = 5) -> dict:
    params: dict = {}
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}) as client:
        r = await _resolve_region(client, region)
        if r:
            params["in"] = r.get("name", region)
    if sales_type:
        params["salesType"] = sales_type
    if trade_type:
        params["tradeType"] = trade_type

    data = await _next_data_search("/realty", params)
    if "error" in data:
        return data
    items = []
    try:
        props = data.get("props", {}).get("pageProps", {})
        items = props.get("articles") or props.get("listings") or props.get("results") or []
    except Exception:
        pass
    return {"region": region, "count": len(items), "items": items[:limit]}
