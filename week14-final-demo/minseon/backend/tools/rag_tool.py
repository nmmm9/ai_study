"""
rag_tool.py — OpenAI Function Calling 도구 정의 (BACKEND 계층)

8가지 도구:
  검색/조회: search_policies, get_policy_details, get_application_method, get_upcoming_deadlines
  추천/검증: check_eligibility, recommend_policies
  비교/목록: compare_policies, list_by_category
"""

from backend.tools.policy_loader import (
    search_policies,
    search_all_policies,
    get_policies_by_category,
    get_policy_by_id,
)
from backend.modules.vector_store import search_vector, is_built
from backend.modules.embedder import embed_query

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_policy",
        "description": (
            "약 620개 청년정책 DB에서 관련 정책을 검색합니다. "
            "특정 정책의 조건·금액·기간·신청 방법 등 구체적 정보가 필요할 때 사용하세요."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "검색 키워드 목록. 예) ['청년도약계좌', '적금', '가입조건']",
                },
                "category": {
                    "type": "string",
                    "description": (
                        "정책 카테고리 (지정 시 해당 분야만 검색):\n"
                        "일자리 / 진로 / 창업 / 주거 / 금융 / 교육 / 마음건강 / 신체건강 / 문화/예술 / 생활지원\n"
                        "빈 문자열('')이면 전체 검색"
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

COMPARE_TOOL = {
    "type": "function",
    "function": {
        "name": "compare_policies",
        "description": (
            "두 청년정책을 동시에 검색하여 조건·지원 금액·대상·차이점을 비교합니다. "
            "'A랑 B 비교해줘', 'A와 B 중 뭐가 유리해?' 등의 질문에 사용하세요."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "policy_a": {"type": "string", "description": "비교할 첫 번째 정책명"},
                "policy_b": {"type": "string", "description": "비교할 두 번째 정책명"},
            },
            "required": ["policy_a", "policy_b"],
        },
    },
}

LIST_TOOL = {
    "type": "function",
    "function": {
        "name": "list_by_category",
        "description": (
            "특정 카테고리의 청년정책 전체 목록을 가져옵니다. "
            "'취업 정책 어떤 게 있어?', '주거 지원 종류 알려줘' 등의 탐색 질문에 사용하세요."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "조회할 카테고리: 일자리 / 진로 / 창업 / 주거 / 금융 / 교육 / 마음건강 / 신체건강 / 문화/예술 / 생활지원",
                },
                "top_k": {
                    "type": "integer",
                    "description": "반환할 최대 개수 (기본값: 8)",
                    "default": 8,
                },
            },
            "required": ["category"],
        },
    },
}

SEARCH_POLICIES_TOOL = {
    "type": "function",
    "function": {
        "name": "search_policies",
        "description": (
            "키워드·카테고리·거주 지역을 기반으로 현재 시행 중인 청년정책을 검색합니다. "
            "특정 정책의 조건·금액·기간을 알고 싶을 때 사용하세요."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query":    {"type": "string",  "description": "검색 키워드 (예: '적금', '월세 지원')"},
                "category": {"type": "string",  "description": "정책 분야: 일자리/진로/창업/주거/금융/교육/마음건강/신체건강/문화·예술/생활지원"},
                "region":   {"type": "string",  "description": "거주 지역 (예: '서울', '경기도'). 전국 공통이면 빈 문자열"},
                "top_k":    {"type": "integer", "description": "반환 최대 개수 (기본값: 5)", "default": 5},
            },
            "required": [],
        },
    },
}

GET_POLICY_DETAILS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_policy_details",
        "description": (
            "정책명 또는 정책 ID로 해당 정책의 모든 상세 정보를 조회합니다. "
            "'이 정책 자세히 알려줘', '지원 내용 전부 알고 싶어' 등의 질문에 사용하세요."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string", "description": "정책명 또는 정책 ID (예: '청년도약계좌', '청년희망적금')"},
            },
            "required": ["policy_id"],
        },
    },
}

CHECK_ELIGIBILITY_TOOL = {
    "type": "function",
    "function": {
        "name": "check_eligibility",
        "description": (
            "사용자의 나이·소득·취업 상태를 기반으로 특정 정책에 신청 가능한지 판별합니다. "
            "'나 신청 가능해?', '자격이 되는지 확인해줘' 등의 질문에 사용하세요."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "policy_id":         {"type": "string",  "description": "검증할 정책명"},
                "age":               {"type": "integer", "description": "사용자 만 나이"},
                "annual_income":     {"type": "integer", "description": "연 소득 (단위: 만 원)"},
                "employment_status": {"type": "string",  "description": "취업 상태: 재직/구직중/프리랜서/대학생"},
            },
            "required": ["policy_id"],
        },
    },
}

RECOMMEND_POLICIES_TOOL = {
    "type": "function",
    "function": {
        "name": "recommend_policies",
        "description": (
            "사용자 프로필(나이·지역·소득·관심사 등)을 바탕으로 가장 적합한 정책 3~5가지를 추천합니다. "
            "'나한테 맞는 정책 추천해줘', '어떤 혜택 받을 수 있어?' 등의 질문에 사용하세요."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_profile": {
                    "type": "object",
                    "description": "사용자 프로필 JSON (age, region, annual_income, employment_status, interests 등)",
                },
                "top_k": {"type": "integer", "description": "추천 개수 (기본값: 5)", "default": 5},
            },
            "required": ["user_profile"],
        },
    },
}

GET_APPLICATION_METHOD_TOOL = {
    "type": "function",
    "function": {
        "name": "get_application_method",
        "description": (
            "특정 정책의 신청 방법·필요 서류·온라인 신청 링크를 안내합니다. "
            "'어떻게 신청해?', '필요한 서류가 뭐야?', '신청 링크 알려줘' 등의 질문에 사용하세요."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string", "description": "정책명 또는 정책 ID"},
            },
            "required": ["policy_id"],
        },
    },
}

GET_UPCOMING_DEADLINES_TOOL = {
    "type": "function",
    "function": {
        "name": "get_upcoming_deadlines",
        "description": (
            "신청 마감이 임박한 청년정책 목록을 조회합니다. "
            "'곧 마감되는 정책 알려줘', '이번 달 신청 가능한 정책 뭐야?' 등의 질문에 사용하세요."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "region":               {"type": "string",  "description": "거주 지역 (빈 문자열이면 전국)"},
                "days_until_deadline":  {"type": "integer", "description": "마감까지 남은 일수 기준 (기본값: 14)", "default": 14},
            },
            "required": [],
        },
    },
}

ALL_TOOLS = [
    SEARCH_POLICIES_TOOL,
    GET_POLICY_DETAILS_TOOL,
    CHECK_ELIGIBILITY_TOOL,
    RECOMMEND_POLICIES_TOOL,
    GET_APPLICATION_METHOD_TOOL,
    GET_UPCOMING_DEADLINES_TOOL,
    COMPARE_TOOL,
    LIST_TOOL,
]


def execute_search_policies(query: str = "", keywords: list = None, category: str = "", region: str = "", top_k: int = 5) -> list[dict]:
    if keywords is None:
        keywords = []
    combined = ([query] if query else []) + keywords + ([region] if region else [])
    search_text = " ".join(combined) if combined else "청년 지원 정책"

    if is_built():
        results = search_vector(embed_query(search_text), top_k=top_k, category=category)
        if results:
            return results

    return search_policies(keywords=combined, category=category, top_k=top_k) or \
           search_all_policies(keywords=combined, top_k=top_k)


def execute_get_policy_details(policy_id: str) -> list[dict]:
    docs = get_policy_by_id(policy_id)
    if not docs and is_built():
        docs = search_vector(embed_query(policy_id), top_k=1)
    return docs


def execute_check_eligibility(policy_id: str, age: int = 0, annual_income: int = 0, employment_status: str = "") -> list[dict]:
    return get_policy_by_id(policy_id) or (
        search_vector(embed_query(policy_id), top_k=1) if is_built() else
        search_policies(keywords=[policy_id], top_k=1)
    )


def execute_recommend_policies(user_profile: dict, top_k: int = 5) -> list[dict]:
    parts = []
    if user_profile.get("age"):
        parts.append(f"만 {user_profile['age']}세")
    if user_profile.get("region"):
        parts.append(user_profile["region"])
    if user_profile.get("interests"):
        interests = user_profile["interests"]
        parts.extend(interests if isinstance(interests, list) else [str(interests)])
    if user_profile.get("employment_status"):
        parts.append(user_profile["employment_status"])
    if user_profile.get("annual_income"):
        parts.append(f"소득 {user_profile['annual_income']}만원")

    query = " ".join(parts) if parts else "청년 지원 정책"

    if is_built():
        return search_vector(embed_query(query), top_k=top_k)
    return search_all_policies(keywords=parts[:3], top_k=top_k)


def execute_get_application_method(policy_id: str) -> list[dict]:
    return execute_get_policy_details(policy_id)


def execute_get_upcoming_deadlines(region: str = "", days_until_deadline: int = 14) -> list[dict]:
    query = f"{region} 청년정책 신청 마감 임박" if region else "청년정책 신청기간 마감 모집"
    if is_built():
        return search_vector(embed_query(query), top_k=8)
    keywords = ["마감", "신청기간", "모집"] + ([region] if region else [])
    return search_all_policies(keywords=keywords, top_k=8)


def execute_search(keywords: list[str], category: str = "", top_k: int = 5) -> list[dict]:
    if is_built():
        query = " ".join(keywords)
        embedding = embed_query(query)
        results = search_vector(query_embedding=embedding, top_k=top_k, category=category)
        if results:
            return results

    # 벡터 인덱스 없을 때 키워드 검색으로 fallback
    results = search_policies(keywords=keywords, category=category, top_k=top_k)
    if not results:
        results = search_all_policies(keywords=keywords, top_k=top_k)
    return results


def execute_compare(policy_a: str, policy_b: str) -> list[dict]:
    if is_built():
        docs_a = search_vector(embed_query(policy_a), top_k=3)
        docs_b = search_vector(embed_query(policy_b), top_k=3)
    else:
        docs_a = search_policies(keywords=[policy_a], top_k=3)
        docs_b = search_policies(keywords=[policy_b], top_k=3)

    seen, merged = set(), []
    for d in docs_a + docs_b:
        if d["title"] not in seen:
            seen.add(d["title"])
            merged.append(d)
    return merged


def execute_list(category: str, top_k: int = 8) -> list[dict]:
    return get_policies_by_category(category=category, top_k=top_k)
