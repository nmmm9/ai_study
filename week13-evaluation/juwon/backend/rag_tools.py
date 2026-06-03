"""
rag_tools.py - Agentic RAG 도구 (Week 12/13)
ReAct 에이전트가 호출할 수 있는 3가지 검색 도구
"""
from langchain_core.tools import tool
from storage import load_all_history, search_reports


def _build_context(reports: list[dict]) -> str:
    parts = []
    for r in reports:
        date  = r.get("created_at", "")[:10]
        lang  = r.get("language") or "전체"
        repos = r.get("repos", [])
        top   = ", ".join(rp["name"] for rp in repos[:5])
        judge = r.get("judge_decision", "")[:400]
        parts.append(f"[{date} | {lang}]\n상위 레포: {top}\n분석: {judge}")
    return "\n\n---\n\n".join(parts)


@tool
def search_trend_history(query: str) -> str:
    """과거 GitHub 트렌드 분석 결과에서 관련 정보를 검색합니다. 특정 기술이나 트렌드에 대해 물어볼 때 사용하세요."""
    results = search_reports(query, limit=3)
    if not results:
        return "관련 과거 분석 데이터가 없습니다."
    return _build_context(results)


@tool
def get_recent_trends(limit: int = 3) -> str:
    """최근 N번의 트렌드 분석 요약을 가져옵니다. 최신 트렌드 현황을 파악할 때 사용하세요."""
    reports = load_all_history()[:limit]
    if not reports:
        return "저장된 분석 기록이 없습니다."
    return _build_context(reports)


@tool
def search_repo_analysis(repo_name: str) -> str:
    """특정 레포지토리가 과거 분석에서 언급된 내용을 찾습니다."""
    results = search_reports(repo_name, limit=5)
    found = []
    for r in results:
        matched = [rp for rp in r.get("repos", []) if repo_name.lower() in rp.get("name", "").lower()]
        if matched:
            date = r.get("created_at", "")[:10]
            found.append(f"[{date}] {matched[0]['name']}: {matched[0].get('description', '')}")
    return "\n".join(found) if found else f"'{repo_name}' 관련 분석 기록이 없습니다."
