"""도서관 도서 검색 — 정보나루 via k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="library_book_search",
    description="공공도서관 정보나루에서 도서를 검색합니다. 키워드를 입력하면 ISBN과 함께 도서 목록을 반환합니다.",
    parameters={
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "도서명 또는 저자/키워드"},
            "page_size": {"type": "integer", "default": 10},
        },
        "required": ["keyword"],
    },
)
async def library_book_search(keyword: str, page_size: int = 10) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/data4library/book-search",
            params={"keyword": keyword, "pageNo": 1, "pageSize": page_size},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"도서 검색 실패 (status {resp.status_code})", "body": resp.text[:300]}
