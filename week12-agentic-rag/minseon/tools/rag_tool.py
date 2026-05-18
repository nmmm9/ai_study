"""
rag_tool.py
───────────
RAG 검색을 에이전트가 호출할 수 있는 Tool로 정의합니다.

week11 policy_loader를 래핑하여
OpenAI function calling 스펙에 맞게 제공합니다.
"""

from tools.policy_loader import search_policies, search_all_policies

# ── OpenAI tool 스펙 정의 ──────────────────────────────────────────
SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_policy",
        "description": (
            "청년정책 데이터베이스에서 관련 정책을 검색합니다. "
            "정보가 필요하거나 부족할 때 이 도구를 호출하세요."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "검색할 키워드 목록. 예) ['청년도약계좌', '적금', '금융']",
                },
                "category": {
                    "type": "string",
                    "description": "정책 카테고리: '장학금' | '취업' | '주거' | '금융' | '' (전체)",
                    "default": "",
                },
                "top_k": {
                    "type": "integer",
                    "description": "반환할 최대 문서 수 (기본값: 5)",
                    "default": 5,
                },
            },
            "required": ["keywords"],
        },
    },
}


def execute_search(keywords: list[str], category: str = "", top_k: int = 5) -> list[dict]:
    """Tool call 결과를 실제 검색으로 실행합니다."""
    results = search_policies(keywords=keywords, category=category, top_k=top_k)
    if not results:
        results = search_all_policies(keywords=keywords, top_k=top_k)
    return results
