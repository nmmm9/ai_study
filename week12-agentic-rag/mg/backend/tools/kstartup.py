"""K-Startup 창업지원 공고 — 공공데이터포털 via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="kstartup_announcements",
    description="K-Startup 창업지원 공고를 검색합니다. 지원 사업, 모집 공고를 키워드로 조회.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "공고 제목/내용 키워드"},
            "limit": {"type": "integer", "default": 10},
        },
    },
)
async def kstartup_announcements(query: str | None = None, limit: int = 10) -> dict:
    params: dict = {"limit": limit}
    if query:
        params["q"] = query
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{PROXY}/v1/kstartup/announcements", params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"K-Startup 공고 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}


@register_tool(
    name="kstartup_business_info",
    description="K-Startup 사업 정보를 조회합니다 (지원 사업의 상세 내용).",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "사업명 키워드"},
            "limit": {"type": "integer", "default": 10},
        },
    },
)
async def kstartup_business_info(query: str | None = None, limit: int = 10) -> dict:
    params: dict = {"limit": limit}
    if query:
        params["q"] = query
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{PROXY}/v1/kstartup/business-info", params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"K-Startup 사업정보 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}


@register_tool(
    name="kstartup_contents",
    description="K-Startup 콘텐츠(가이드, 정책, 안내문 등)를 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "콘텐츠 키워드"},
            "limit": {"type": "integer", "default": 10},
        },
    },
)
async def kstartup_contents(query: str | None = None, limit: int = 10) -> dict:
    params: dict = {"limit": limit}
    if query:
        params["q"] = query
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{PROXY}/v1/kstartup/contents", params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"K-Startup 콘텐츠 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}


@register_tool(
    name="kstartup_statistics",
    description="K-Startup 통계(창업 지원 사업 통계, 분야별 현황)를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "year": {"type": "integer", "description": "조회 연도 (선택)"},
        },
    },
)
async def kstartup_statistics(year: int | None = None) -> dict:
    params: dict = {}
    if year:
        params["year"] = year
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{PROXY}/v1/kstartup/statistics", params=params)
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"K-Startup 통계 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}
