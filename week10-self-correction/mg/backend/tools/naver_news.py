"""네이버 뉴스 검색 — k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="naver_news_search",
    description="네이버 뉴스에서 최신 기사를 검색합니다. 제목/요약/링크/발행시각을 반환합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "검색 키워드"},
            "display": {"type": "integer", "description": "결과 개수 (기본 10, 최대 30)", "default": 10},
            "sort": {"type": "string", "enum": ["sim", "date"], "default": "date"},
        },
        "required": ["query"],
    },
)
async def naver_news_search(query: str, display: int = 10, sort: str = "date") -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{PROXY}/v1/naver-news/search",
            params={"q": query, "limit": min(display, 30), "sort": sort},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"네이버 뉴스 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}
