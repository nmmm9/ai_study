"""
rag_tools.py - Agentic RAG 검색 도구

LangChain @tool로 등록해서 에이전트가 필요할 때 직접 호출.
도구 3종:
  search_trend_history  - 과거 트렌드 분석 시맨틱 검색
  search_repo_analysis  - 특정 레포 과거 기록 검색
  get_recent_trends     - 최근 N번 분석 요약
"""
from langchain_core.tools import tool
from vector_store import search_reports, load_all_reports


@tool
def search_trend_history(query: str) -> str:
    """
    과거 GitHub 트렌드 분석 결과에서 관련 정보를 검색합니다.
    특정 기술, 언어, 기간에 대한 이전 분석이 필요할 때 호출하세요.
    예: "지난달 AI 트렌드", "Rust 관련 이전 분석", "웹 프레임워크 변화"
    """
    results = search_reports(query, limit=3)
    if not results:
        return "관련 과거 분석 데이터가 없습니다."

    parts = []
    for r in results:
        date    = r.get("created_at", "")[:10]
        lang    = r.get("language") or "전체"
        period  = r.get("period", "")
        repos   = r.get("repos", [])
        top5    = ", ".join(rp["name"] for rp in repos[:5])
        judge   = r.get("judge_decision", "")[:300]
        sim     = r.get("similarity", 0)
        parts.append(
            f"[{date} | {lang} | {period} | 유사도:{sim:.2f}]\n"
            f"상위 레포: {top5}\n"
            f"결론: {judge}..."
        )

    return "\n\n---\n\n".join(parts)


@tool
def search_repo_analysis(repo_name: str) -> str:
    """
    특정 레포지토리에 대한 과거 분석 기록을 검색합니다.
    "이 레포 어때?", "이전에 이 레포 나왔어?" 같은 질문에 사용하세요.
    """
    results = search_reports(f"레포지토리 {repo_name} 분석", limit=5)
    if not results:
        return f"{repo_name}에 대한 과거 분석 기록이 없습니다."

    found = []
    for r in results:
        repos   = r.get("repos", [])
        matched = [rp for rp in repos if repo_name.lower() in rp.get("name", "").lower()]
        if not matched:
            continue
        rp   = matched[0]
        date = r.get("created_at", "")[:10]
        found.append(
            f"[{date}] {rp['name']}\n"
            f"별점: {rp.get('stars', 0):,} | 트렌드점수: {rp.get('trend_score', 0)}\n"
            f"설명: {rp.get('description', '')}\n"
            f"관련 결론: {r.get('judge_decision', '')[:200]}..."
        )

    if not found:
        return f"{repo_name}이 포함된 과거 분석이 없습니다."
    return "\n\n---\n\n".join(found)


@tool
def get_recent_trends(limit: int = 3) -> str:
    """
    최근 N번의 트렌드 분석 요약을 가져옵니다.
    최근 흐름 파악, 반복 등장 레포 확인 시 사용하세요.
    """
    reports = load_all_reports()[:limit]
    if not reports:
        return "저장된 분석 기록이 없습니다."

    parts = []
    for r in reports:
        date   = r.get("created_at", "")[:10]
        lang   = r.get("language") or "전체"
        period = r.get("period", "")
        repos  = r.get("repos", [])
        top5   = ", ".join(rp["name"] for rp in repos[:5])
        judge  = r.get("judge_decision", "")[:200]
        parts.append(
            f"[{date} | {lang} | {period}]\n"
            f"상위: {top5}\n"
            f"요약: {judge}..."
        )

    return "\n\n---\n\n".join(parts)
