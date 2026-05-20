"""
vector_store.py - Supabase pgvector 기반 벡터 저장소

week11의 history.json을 대체.
분석 결과를 임베딩해서 Supabase에 저장하고,
자연어 쿼리로 유사한 과거 분석을 검색.
"""
import os
from openai import OpenAI
from database import get_supabase

_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


def _embed(text: str) -> list[float]:
    resp = _openai.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
    )
    return resp.data[0].embedding


def _report_to_text(report: dict) -> str:
    """리포트를 임베딩용 텍스트로 변환"""
    top_repos = ", ".join(r["name"] for r in report.get("repos", [])[:10])
    return (
        f"언어: {report.get('language', '전체')} | 기간: {report.get('period', 'weekly')}\n"
        f"트렌딩 레포: {top_repos}\n"
        f"AI/ML: {report.get('analysis_ai', '')[:400]}\n"
        f"웹/앱: {report.get('analysis_web', '')[:400]}\n"
        f"보안: {report.get('analysis_sec', '')[:400]}\n"
        f"결론: {report.get('judge_decision', '')[:400]}"
    )


def save_report(report: dict) -> str:
    """분석 결과를 pgvector에 저장하고 id 반환"""
    vector = _embed(_report_to_text(report))
    sb = get_supabase()

    result = sb.table("trend_reports").insert({
        "language":          report.get("language", "전체"),
        "period":            report.get("period", "weekly"),
        "repos":             report.get("repos", []),
        "language_stats":    report.get("language_stats", {}),
        "top_topics":        report.get("top_topics", {}),
        "analysis_ai":       report.get("analysis_ai", ""),
        "analysis_web":      report.get("analysis_web", ""),
        "analysis_sec":      report.get("analysis_sec", ""),
        "supervisor_report": report.get("supervisor_report", ""),
        "critic_feedback":   report.get("critic_feedback", ""),
        "judge_decision":    report.get("judge_decision", ""),
        "debate_history":    report.get("debate_history", []),
        "embedding":         vector,
    }).execute()

    return result.data[0]["id"] if result.data else ""


def search_reports(query: str, limit: int = 3) -> list[dict]:
    """pgvector 코사인 유사도로 관련 리포트 검색"""
    vector = _embed(query)
    sb = get_supabase()
    result = sb.rpc("search_trend_reports", {
        "query_embedding": vector,
        "match_count": limit,
    }).execute()
    return result.data or []


def load_all_reports() -> list[dict]:
    """저장된 모든 리포트 반환 (최신순, 임베딩 필드 제외)"""
    sb = get_supabase()
    result = (
        sb.table("trend_reports")
        .select(
            "id, created_at, language, period, repos, language_stats, "
            "top_topics, analysis_ai, analysis_web, analysis_sec, "
            "supervisor_report, critic_feedback, judge_decision, debate_history"
        )
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return result.data or []


def load_latest_report() -> dict | None:
    """가장 최근 리포트 반환"""
    sb = get_supabase()
    result = (
        sb.table("trend_reports")
        .select(
            "id, created_at, language, period, repos, language_stats, "
            "top_topics, analysis_ai, analysis_web, analysis_sec, "
            "supervisor_report, critic_feedback, judge_decision, debate_history"
        )
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def load_history_stats() -> list[dict]:
    """트렌드 차트용 시계열 통계 반환"""
    reports = load_all_reports()
    stats = []
    for r in reversed(reports):
        stats.append({
            "date":           r["created_at"][:10],
            "language_stats": r.get("language_stats", {}),
            "top_topics":     r.get("top_topics", {}),
            "repo_count":     len(r.get("repos", [])),
        })
    return stats
