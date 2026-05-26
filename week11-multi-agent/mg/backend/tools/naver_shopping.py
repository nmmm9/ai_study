"""네이버 쇼핑 검색 — k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="naver_shopping_search",
    description="네이버 쇼핑에서 상품을 검색합니다. 가격 비교, 평점, 리뷰 수를 반환합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "검색할 상품명"},
            "limit": {"type": "integer", "description": "결과 개수 (기본 10)", "default": 10},
            "sort": {
                "type": "string",
                "enum": ["sim", "price_asc", "price_dsc", "review", "date"],
                "default": "sim",
            },
        },
        "required": ["query"],
    },
)
async def naver_shopping_search(query: str, limit: int = 10, sort: str = "sim") -> dict:
    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.get(
            f"{PROXY}/v1/naver-shopping/search",
            params={"q": query, "limit": limit, "sort": sort},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"네이버 쇼핑 조회 실패 (status {resp.status_code})", "body": resp.text[:300]}
