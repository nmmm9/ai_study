"""
search_tool_node.py
───────────────────
에이전트가 요청한 tool call을 실제로 실행합니다.
search_policy 함수를 호출하여 관련 정책 문서를 검색합니다.
"""

import json
from state import AgenticRAGState
from tools.rag_tool import execute_search


def search_tool_node(state: AgenticRAGState) -> dict:
    """agent_node가 요청한 검색 tool call을 실행합니다."""
    tool_calls = state.get("tool_calls", [])
    all_docs: list[dict] = []

    for tc in tool_calls:
        func      = tc.get("function", {})
        func_name = func.get("name", "")
        if func_name != "search_policy":
            continue

        try:
            args     = json.loads(func.get("arguments", "{}"))
            keywords = args.get("keywords", [])
            category = args.get("category", "")
            top_k    = args.get("top_k", 5)
        except (json.JSONDecodeError, AttributeError):
            keywords, category, top_k = [], "", 5

        results = execute_search(keywords=keywords, category=category, top_k=top_k)
        all_docs.extend(results)
        print(f"[search_tool_node] 키워드={keywords} | {len(results)}개 검색됨")

    # 중복 제거 (title 기준)
    seen  = set()
    unique_docs = []
    for d in all_docs:
        if d["title"] not in seen:
            seen.add(d["title"])
            unique_docs.append(d)

    trace = list(state.get("execution_trace", []))
    trace.append({
        "node":    "search_tool_node",
        "summary": f"총 {len(unique_docs)}개 정책 문서 검색 완료",
    })

    return {
        "documents":       unique_docs,
        "tool_calls":      [],          # 소비 후 초기화
        "execution_trace": trace,
    }
