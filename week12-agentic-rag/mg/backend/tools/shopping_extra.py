"""쇼핑 확장 — 다나와 / 마켓컬리 / 오늘의집.

각 사이트의 공식 BFF JSON 또는 __NEXT_DATA__ 직접 호출.
"""

import re
import json
import httpx
from urllib.parse import quote
from tools.registry import register_tool

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


# ─────────────────────────────────────
# 다나와 — search.danawa.com
# ─────────────────────────────────────

@register_tool(
    name="danawa_price_search",
    description="다나와 가격비교에서 상품을 검색합니다. 쇼핑몰별 최저가 후보를 반환.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "상품명 키워드"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
)
async def danawa_price_search(query: str, limit: int = 10) -> dict:
    url = f"https://search.danawa.com/dsearch.php?query={quote(query)}"
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return {"error": f"다나와 검색 실패 (status {resp.status_code})"}

    # 다나와 검색 결과 HTML 에서 상품 리스트 추출
    html = resp.text
    products = []
    # 상품 카드 pattern: pcode + 상품명 + 최저가
    for m in re.finditer(r'href="[^"]*pcode=(\d+)[^"]*"[^>]*>([^<]{3,200})</a>', html):
        pcode, name = m.group(1), m.group(2).strip()
        if any(p["pcode"] == pcode for p in products):
            continue
        products.append({
            "pcode": pcode,
            "name": name[:120],
            "detail_url": f"https://prod.danawa.com/info/?pcode={pcode}",
        })
        if len(products) >= limit:
            break

    return {"query": query, "count": len(products), "items": products}


@register_tool(
    name="danawa_price_compare",
    description="다나와 특정 상품의 쇼핑몰별 가격 비교를 조회합니다. pcode 필요.",
    parameters={
        "type": "object",
        "properties": {
            "pcode": {"type": "string", "description": "다나와 상품코드 (danawa_price_search 의 pcode)"},
        },
        "required": ["pcode"],
    },
)
async def danawa_price_compare(pcode: str) -> dict:
    url = "https://prod.danawa.com/info/ajax/getAllPriceCompareMallList.ajax.php"
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA, "Referer": f"https://prod.danawa.com/info/?pcode={pcode}"}) as client:
        resp = await client.post(url, data={"prodCode": pcode})
        if resp.status_code != 200:
            return {"error": f"가격비교 조회 실패 (status {resp.status_code})"}
    return {"pcode": pcode, "raw_html": resp.text[:2000]}


# ─────────────────────────────────────
# 마켓컬리 — api.kurly.com (공개 BFF)
# ─────────────────────────────────────

@register_tool(
    name="market_kurly_search",
    description="마켓컬리에서 상품을 검색합니다. 신선식품/가공식품/생활용품 등.",
    parameters={
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "상품 키워드"},
            "page": {"type": "integer", "default": 1},
        },
        "required": ["keyword"],
    },
)
async def market_kurly_search(keyword: str, page: int = 1) -> dict:
    url = f"https://api.kurly.com/search/v4/sites/market/normal-search"
    params = {"keyword": keyword, "page": page}
    headers = {"User-Agent": UA, "Origin": "https://www.kurly.com", "Referer": "https://www.kurly.com/"}
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        resp = await client.get(url, params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"마켓컬리 검색 실패 (status {resp.status_code})", "body": resp.text[:300]}


# ─────────────────────────────────────
# 오늘의집 — ohou.se/commerces/today_deals
# ─────────────────────────────────────

@register_tool(
    name="ohou_today_deal",
    description="오늘의집 '오늘의딜' 페이지의 현재 특가 상품을 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "default": 20},
        },
    },
)
async def ohou_today_deal(limit: int = 20) -> dict:
    url = "https://ohou.se/commerces/today_deals"
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return {"error": f"오늘의집 조회 실패 (status {resp.status_code})"}

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
    if not m:
        return {"error": "__NEXT_DATA__ 파싱 실패"}
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {"error": "JSON 파싱 실패"}

    items = []
    try:
        props = data.get("props", {}).get("pageProps", {})
        items = props.get("deals") or props.get("items") or props.get("products") or []
    except Exception:
        pass
    return {"count": len(items), "items": items[:limit]}
