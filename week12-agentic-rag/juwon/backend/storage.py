"""
storage.py - Supabase 기반 저장소 (week11 JSON → week12 Supabase)

week11의 storage.py와 동일한 인터페이스를 유지해서
graph.py, scheduler.py 등 기존 코드와 호환됨.
"""
from database import get_supabase
from vector_store import save_report, load_all_reports, load_latest_report


def save_history(data: dict) -> None:
    save_report(data)


def load_all_history() -> dict:
    """기존 week11 API와 호환 → {날짜문자열: 리포트} dict 반환"""
    reports = load_all_reports()
    return {r["created_at"][:16]: r for r in reports}


def load_latest_history() -> dict | None:
    return load_latest_report()


def load_previous_history() -> dict | None:
    """최신 직전 기록 반환 (비교용)"""
    reports = load_all_reports()
    return reports[1] if len(reports) >= 2 else None


# ── 키워드 구독 CRUD ──────────────────────────────────────────

def get_keywords() -> list[str]:
    sb = get_supabase()
    result = sb.table("keyword_subscriptions").select("keyword").order("created_at").execute()
    return [r["keyword"] for r in (result.data or [])]


def add_keyword(keyword: str) -> bool:
    sb = get_supabase()
    try:
        sb.table("keyword_subscriptions").insert({"keyword": keyword.strip().lower()}).execute()
        return True
    except Exception:
        return False


def delete_keyword(keyword: str) -> bool:
    sb = get_supabase()
    try:
        sb.table("keyword_subscriptions").delete().eq("keyword", keyword.strip().lower()).execute()
        return True
    except Exception:
        return False


def check_keyword_matches(repos: list) -> list[dict]:
    """분석된 레포 중 구독 키워드와 매칭되는 것 반환"""
    keywords = get_keywords()
    if not keywords:
        return []

    matched = []
    for repo in repos:
        text = (
            repo.get("name", "") + " " +
            repo.get("description", "") + " " +
            " ".join(repo.get("topics", []))
        ).lower()
        for kw in keywords:
            if kw in text:
                matched.append({"keyword": kw, "repo": repo})
                break
    return matched
