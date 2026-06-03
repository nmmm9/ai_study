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
            "약 490개 청년정책 데이터베이스에서 관련 정책을 검색합니다. "
            "정보가 필요하거나 부족할 때 이 도구를 호출하세요. "
            "category를 지정하면 해당 분야만 검색해 정확도가 높아집니다."
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
                    "description": (
                        "정책 카테고리 (지정 시 해당 분야만 검색):\n"
                        "- '장학금': 국가장학금, 학자금, 등록금 지원\n"
                        "- '금융': 청년도약계좌, 희망적금, 대출, 이차보전\n"
                        "- '주거': 청년월세, 전세자금, 주택 청약\n"
                        "- '취업': 취업지원, 자격증, 면접, 인턴, 일경험\n"
                        "- '창업': 청년창업, 스타트업 지원\n"
                        "- '건강문화': 마음건강, 문화, 여가, 도서\n"
                        "- '참여': 청년위원회, 네트워크, 협의체\n"
                        "- '복지': 생활지원, 자립, 기타\n"
                        "- '' (빈 문자열): 전체 검색"
                    ),
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
