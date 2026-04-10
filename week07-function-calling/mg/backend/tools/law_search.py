"""한국 법률/판례 검색 — Beopmang API (공개 fallback)."""

import httpx
from tools.registry import register_tool

BEOPMANG_URL = "https://api.beopmang.org/api/v4/law"


@register_tool(
    name="korean_law_search",
    description="한국 법률, 판례, 조례를 검색합니다. 키워드로 관련 법률을 찾아줍니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "검색할 법률 키워드 (예: 근로기준법, 임대차보호법, 개인정보보호)"},
            "category": {"type": "string", "enum": ["law", "precedent", "ordinance"], "description": "law=법령, precedent=판례, ordinance=조례", "default": "law"},
        },
        "required": ["query"],
    },
)
async def korean_law_search(query: str, category: str = "law") -> dict:
    # 법망 REST API: action=search (법령), action=search_precedents (판례), action=search_ordinance (자치법규)
    action_map = {"law": "search", "precedent": "search_precedents", "ordinance": "search_ordinance"}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            BEOPMANG_URL,
            params={"action": action_map.get(category, "search_law"), "q": query},
        )

        if resp.status_code != 200:
            return {"error": f"법률 검색 실패 (status {resp.status_code})"}

        try:
            data = resp.json()
            results = data.get("results", data.get("data", data.get("items", [])))

            if isinstance(results, list):
                simplified = []
                for r in results[:5]:
                    simplified.append({
                        "title": r.get("title", r.get("법령명", r.get("name", ""))),
                        "content": str(r.get("content", r.get("조문내용", r.get("summary", ""))))[:300],
                    })
                return {"query": query, "category": category, "count": len(simplified), "results": simplified}

            return {"query": query, "data": data}
        except Exception:
            return {"query": query, "error": "파싱 실패"}
