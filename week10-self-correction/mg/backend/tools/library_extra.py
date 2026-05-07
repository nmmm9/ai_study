"""도서관 부가 기능 — 도서 상세, 도서관 검색, 도서 보유 도서관 — k-skill-proxy."""

import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"


@register_tool(
    name="library_book_detail",
    description="ISBN으로 도서 상세 정보(저자, 출판사, 분류, 대출 통계)를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "isbn13": {"type": "string", "description": "13자리 ISBN"},
        },
        "required": ["isbn13"],
    },
)
async def library_book_detail(isbn13: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/data4library/book-detail", params={"isbn13": isbn13}
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"도서 상세 조회 실패 (status {resp.status_code})"}


@register_tool(
    name="library_search",
    description="지역명으로 가까운 공공도서관을 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "region": {"type": "string", "description": "지역명 (예: 서울 강남구)"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["region"],
    },
)
async def library_search(region: str, limit: int = 10) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/data4library/library-search",
            params={"region": region, "pageSize": limit},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"도서관 검색 실패 (status {resp.status_code})"}


@register_tool(
    name="library_libraries_by_book",
    description="ISBN으로 해당 도서를 소장한 도서관 목록을 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "isbn13": {"type": "string", "description": "13자리 ISBN"},
            "region": {"type": "string", "description": "지역명 필터 (선택)"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["isbn13"],
    },
)
async def library_libraries_by_book(isbn13: str, region: str | None = None,
                                     limit: int = 10) -> dict:
    params: dict = {"isbn13": isbn13, "pageSize": limit}
    if region:
        params["region"] = region
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PROXY}/v1/data4library/libraries-by-book", params=params
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"도서 보유관 조회 실패 (status {resp.status_code})"}
