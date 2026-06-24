"""
tool_dispatcher.py — 8가지 도구 실행 및 라우팅 (BACKEND 계층)

검색 계열 → grade_docs_node (관련성 평가 + self-correction 루프)
비교/목록  → generate_node  (바로 생성)
"""

import json
from backend.state    import FinalRAGState
from backend.tools.rag_tool import (
    execute_search,
    execute_compare,
    execute_list,
    execute_search_policies,
    execute_get_policy_details,
    execute_check_eligibility,
    execute_recommend_policies,
    execute_get_application_method,
    execute_get_upcoming_deadlines,
)

_GRADE_TOOLS = {
    "search_policy", "search_policies", "get_policy_details",
    "check_eligibility", "recommend_policies",
    "get_application_method", "get_upcoming_deadlines",
}


def tool_dispatcher(state: FinalRAGState) -> dict:
    tool_calls = state.get("tool_calls", [])
    if not tool_calls:
        return {"documents": [], "tool_name": "", "tool_calls": [], "tool_args": {}}

    tc   = tool_calls[0]
    func = tc.get("function", {})
    name = func.get("name", "")
    try:
        args = json.loads(func.get("arguments", "{}"))
    except (json.JSONDecodeError, TypeError):
        args = {}

    trace = list(state.get("execution_trace", []))

    if name == "search_policies":
        docs    = execute_search_policies(
            query=args.get("query", ""),
            keywords=args.get("keywords", []),
            category=args.get("category", ""),
            region=args.get("region", ""),
            top_k=args.get("top_k", 5),
        )
        summary = f"search_policies: '{args.get('query','')}' [{args.get('category','')}] → {len(docs)}개"

    elif name == "get_policy_details":
        docs    = execute_get_policy_details(args.get("policy_id", ""))
        summary = f"get_policy_details: '{args.get('policy_id','')}' → {len(docs)}개"

    elif name == "check_eligibility":
        docs    = execute_check_eligibility(
            policy_id=args.get("policy_id", ""),
            age=args.get("age", 0),
            annual_income=args.get("annual_income", 0),
            employment_status=args.get("employment_status", ""),
        )
        summary = f"check_eligibility: '{args.get('policy_id','')}' 나이={args.get('age','')} → {len(docs)}개"

    elif name == "recommend_policies":
        docs    = execute_recommend_policies(
            user_profile=args.get("user_profile", {}),
            top_k=args.get("top_k", 5),
        )
        summary = f"recommend_policies: {args.get('user_profile',{})} → {len(docs)}개"

    elif name == "get_application_method":
        docs    = execute_get_application_method(args.get("policy_id", ""))
        summary = f"get_application_method: '{args.get('policy_id','')}' → {len(docs)}개"

    elif name == "get_upcoming_deadlines":
        docs    = execute_get_upcoming_deadlines(
            region=args.get("region", ""),
            days_until_deadline=args.get("days_until_deadline", 14),
        )
        summary = f"get_upcoming_deadlines: region='{args.get('region','')}' → {len(docs)}개"

    elif name in ("search_policy", "search"):
        docs    = execute_search(
            keywords=args.get("keywords", []),
            category=args.get("category", ""),
            top_k=args.get("top_k", 5),
        )
        summary = f"search_policy: {args.get('keywords',[])} → {len(docs)}개"

    elif name == "compare_policies":
        docs    = execute_compare(args.get("policy_a", ""), args.get("policy_b", ""))
        summary = f"compare: {args.get('policy_a','')} vs {args.get('policy_b','')} → {len(docs)}개"

    elif name == "list_by_category":
        docs    = execute_list(args.get("category", ""), args.get("top_k", 8))
        summary = f"list_by_category: {args.get('category','')} → {len(docs)}개"

    else:
        docs, summary = [], f"알 수 없는 도구: {name}"

    print(f"[tool_dispatcher] {summary}")
    trace.append({"node": "tool_dispatcher", "summary": summary})

    return {
        "documents":       docs,
        "tool_name":       name,
        "tool_args":       args,
        "tool_calls":      [],
        "execution_trace": trace,
    }


def route_tool(state: FinalRAGState) -> str:
    """검색 계열은 grade 루프, 비교/목록은 바로 generate."""
    return "grade" if state.get("tool_name") in _GRADE_TOOLS else "generate"
