"""
news_fetcher.py — 청년 관련 최신 뉴스 수집 (Tavily 일반검색 + 국내 언론사 도메인 제한)

search_realtime_policies(정부 정책 공고 전용)와 달리, 이 모듈은
취업·주거·경제·사회 등 청년과 관련된 "일반 뉴스"를 수집합니다.

⚠️ Tavily의 topic="news" 모드는 국내 언론사 커버리지가 거의 없어서
   (영어판 페이지나 무관한 결과만 반환) 대신 topic 없이 일반 검색 +
   time_range로 최신성을 확보하고, include_domains로 국내 언론사만 걸러냅니다.
"""

import requests

from backend.config import settings
from backend.logging_config import get_logger

logger = get_logger(__name__)

TAVILY_URL = "https://api.tavily.com/search"

# 국내 뉴스 도메인으로 제한 (안 하면 Tavily가 영어권 뉴스를 섞어 반환함)
NEWS_DOMAINS = [
    "news.naver.com", "yna.co.kr", "hani.co.kr", "chosun.com",
    "joongang.co.kr", "khan.co.kr", "hankookilbo.com", "ytn.co.kr",
    "kbs.co.kr", "mbc.co.kr", "sbs.co.kr", "yonhapnewstv.co.kr",
    "newsis.com", "news1.kr",
]


def _tavily_key() -> str | None:
    return settings.tavily_api_key or None


def _news_to_doc(item: dict) -> dict:
    title   = item.get("title", "").strip()
    content = item.get("content", "").strip()
    url     = item.get("url", "")
    pub_date = item.get("published_date", "")

    body = f"# {title}\n\n{content}"
    if pub_date:
        body = f"# {title}\n\n(보도일: {pub_date})\n\n{content}"

    return {
        "title":    title,
        "content":  body,
        "source":   "Tavily 뉴스검색",
        "category": "청년뉴스",
        "url":      url,
        "pub_date": pub_date,
    }


def _time_range_for(days: int) -> str:
    if days <= 1:
        return "day"
    if days <= 7:
        return "week"
    if days <= 31:
        return "month"
    return "year"


def search_youth_news(query: str = "", days: int = 7, top_k: int = 5) -> list[dict]:
    """
    청년 관련 최신 뉴스를 Tavily 일반검색(국내 언론사 도메인 제한)으로 조회합니다.

    query가 비어있으면 "청년" 일반 이슈를 검색하고,
    query가 있으면 "청년 {query}" 형태로 좁혀서 검색합니다.
    """
    key = _tavily_key()
    if not key:
        logger.warning("[news_fetcher] TAVILY_API_KEY 없음 — 뉴스 검색 불가")
        return []

    search_query = f"청년 {query} 뉴스".strip() if query else "청년 정책 취업 주거 이슈 뉴스"

    payload = {
        "api_key":         key,
        "query":           search_query,
        "search_depth":    "advanced",
        "time_range":      _time_range_for(days),
        "max_results":     top_k,
        "include_domains": NEWS_DOMAINS,
    }

    try:
        resp = requests.post(TAVILY_URL, json=payload, timeout=15)
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except Exception as e:
        logger.error(f"[news_fetcher] 검색 오류: {e}")
        return []

    docs = [_news_to_doc(r) for r in results if r.get("title")]
    logger.info(f"[news_fetcher] '{search_query}' (최근 {days}일) → {len(docs)}건")
    return docs
