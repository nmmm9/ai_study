"""
tool_dispatcher.py — 8가지 도구 실행 및 라우팅 (BACKEND 계층)

검색 계열 → grade_docs_node (관련성 평가 + self-correction 루프)
비교/목록  → generate_node  (바로 생성)
"""

import json
from backend.logging_config import get_logger
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
    execute_search_housing,
    execute_search_realtime,
    execute_search_news,
    execute_diagnose,
    execute_collab_recommend,
)

logger = get_logger(__name__)

# grade_docs_node를 거치는 도구: 벡터 DB 검색 결과는 관련성 평가 필요
_GRADE_TOOLS = {
    "search_policy", "search_policies", "get_policy_details",
    "check_eligibility", "recommend_policies",
    "get_application_method",
}

# _GRADE_TOOLS 외 나머지는 모두 바로 generate로 라우팅:
#   search_realtime_policies  → 실시간 웹/RSS 결과, 관련성 재평가 불필요
#   search_housing_announcements → LH/HUG API 실시간 공고
#   get_upcoming_deadlines    → SQLite 날짜 정렬 결과, 구조화된 데이터
#   compare_policies, list_by_category → 집계 결과, 관련성 평가 불필요

# 벡터 DB 유사도 조기탈출 임계값 (코사인 유사도 0~1)
# 이 값 미만이면 grade_docs 루프를 건너뛰고 즉시 web_search로 전환
_SIMILARITY_THRESHOLD = 0.40


def _check_early_exit(docs: list[dict]) -> tuple[bool, float]:
    """
    docs가 비어있거나 최고 유사도가 임계값 미만이면 조기탈출.
    키워드 검색 결과(score 필드 없음)는 조기탈출 대상 아님.
    반환: (early_exit: bool, max_similarity: float)
    """
    if not docs:
        return True, 0.0

    scores = [d["score"] for d in docs if "score" in d]
    if not scores:
        # 키워드 검색 fallback 결과 — 유사도 판단 불가, 정상 경로 진행
        return False, 1.0

    max_sim = max(scores)
    return max_sim < _SIMILARITY_THRESHOLD, max_sim


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
            days_until_deadline=args.get("days_until_deadline", 30),
            keyword=args.get("keyword", ""),
        )
        summary = f"get_upcoming_deadlines: region='{args.get('region','')}' keyword='{args.get('keyword','')}' → {len(docs)}개"

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

    elif name == "search_realtime_policies":
        docs    = execute_search_realtime(
            query=args.get("query", ""),
            region=args.get("region", ""),
            age=args.get("age", 0),
            top_k=args.get("top_k", 5),
        )
        summary = f"search_realtime: '{args.get('query','')}' region='{args.get('region','')}' → {len(docs)}건"

    elif name == "search_youth_news":
        docs    = execute_search_news(
            query=args.get("query", ""),
            days=args.get("days", 7),
            top_k=args.get("top_k", 5),
        )
        summary = f"search_youth_news: '{args.get('query','')}' 최근{args.get('days',7)}일 → {len(docs)}건"

    elif name == "diagnose_eligibility":
        docs    = execute_diagnose(args.get("query", ""))
        summary = "diagnose_eligibility: 자가진단 요청"

    elif name == "collab_recommend":
        docs    = execute_collab_recommend(
            session_id=args.get("session_id", ""),
            category=args.get("category", ""),
            top_k=args.get("top_k", 5),
        )
        summary = f"collab_recommend: category='{args.get('category','')}' → {len(docs)}개"

    elif name == "search_housing_announcements":
        docs    = execute_search_housing(
            query=args.get("query", ""),
            region=args.get("region", ""),
            ann_type=args.get("ann_type", ""),
            top_k=args.get("top_k", 5),
        )
        summary = f"search_housing: '{args.get('query','')}' region='{args.get('region','')}' → {len(docs)}개"

    else:
        docs, summary = [], f"알 수 없는 도구: {name}"

    # ── 벡터 DB 검색 결과 유사도 조기탈출 판정 ───────────────────────
    early_exit  = False
    max_sim     = 1.0
    if name in _GRADE_TOOLS:
        early_exit, max_sim = _check_early_exit(docs)
        if early_exit:
            summary += f" ⚡조기탈출(max_sim={max_sim:.2f}<{_SIMILARITY_THRESHOLD})"

    # ── 행동 로그 (협업 필터링용) ─────────────────────────────────
    if docs and name in _GRADE_TOOLS:
        try:
            session_id = state.get("tool_args", {}).get("session_id", "") or "anon"
            from backend.db.behavior_db import log_search_results
            log_search_results(session_id=session_id, docs=docs, query=args.get("query", ""))
        except Exception:
            pass

    # ── 회차별 tool call 이력 누적 ────────────────────────────────
    tool_history = list(state.get("tool_history", []))
    tool_history.append({
        "tool_name":  name,
        "args":       args,
        "docs_count": len(docs),
        "max_sim":    round(max_sim, 3),
        "early_exit": early_exit,
        "grade":      "",   # grade_docs_node에서 채워짐
    })

    logger.info(f"[tool_dispatcher] {summary}")
    trace.append({"node": "tool_dispatcher", "summary": summary})

    return {
        "documents":      docs,
        "tool_name":      name,
        "tool_args":      args,
        "tool_calls":     [],
        "early_exit":     early_exit,
        "max_similarity": max_sim,
        "tool_history":   tool_history,
        "execution_trace": trace,
    }


def route_tool(state: FinalRAGState) -> str:
    tool = state.get("tool_name", "")

    if tool == "diagnose_eligibility":
        return "diagnosis"  # 자가진단 전용 노드

    # 유사도 미달 → grade/rewrite 루프 건너뛰고 즉시 web_search
    if state.get("early_exit"):
        logger.info(f"[route_tool] 조기탈출 → web_search (max_sim={state.get('max_similarity', 0):.2f})")
        return "web_search"

    if tool in _GRADE_TOOLS:
        return "grade"      # 벡터 DB 결과 → 관련성 평가 후 generate
    return "generate"       # 실시간/DB/비교/목록/협업필터 → 바로 generate
