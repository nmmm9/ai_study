"""
github_tools.py - GitHub Trending 페이지 스크래핑

github.com/trending 에서 직접 데이터를 가져옴.
→ "이번 주 획득 스타 수"를 정확하게 알 수 있어서
  OSSInsight와 유사한 결과를 얻을 수 있음.
"""

import math
import re

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _parse_number(text: str) -> int:
    """'1,234' 또는 '1.2k' 형태의 숫자 파싱"""
    text = text.strip().replace(",", "").replace(" ", "")
    if text.endswith("k") or text.endswith("K"):
        return int(float(text[:-1]) * 1000)
    try:
        return int(text)
    except ValueError:
        return 0


def calculate_trend_score(stars_this_period: int, total_stars: int, forks: int) -> float:
    """
    이번 기간 획득 스타 수 기반 트렌드 점수 (0~100)
    - stars_this_period : 이번 주/오늘 획득한 스타 (핵심 지표, 60%)
    - total_stars       : 전체 스타 (인지도, 20%)
    - forks             : 포크 수 (실활용도, 20%)
    """
    velocity_score = min(stars_this_period / 10, 60)          # 60점 (600개 이상이면 만점)
    size_score     = min(math.log1p(total_stars) / 12 * 20, 20)  # 20점
    fork_score     = min(math.log1p(forks) / 10 * 20, 20)        # 20점

    return round(velocity_score + size_score + fork_score, 2)


def get_trending_repos(language: str = "", period: str = "weekly", limit: int = 25) -> list:
    since_map = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
    since     = since_map.get(period, "weekly")

    lang_slug = language.lower().replace(" ", "-") if language else ""
    url       = f"https://github.com/trending/{lang_slug}?since={since}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []

        soup     = BeautifulSoup(resp.text, "html.parser")
        articles = soup.select("article.Box-row")

        repos = []
        for article in articles[:limit]:
            # 레포 이름
            name_tag = article.select_one("h2 a")
            if not name_tag:
                continue
            full_name = name_tag.get("href", "").strip("/")

            # 설명
            desc_tag    = article.select_one("p")
            description = desc_tag.get_text(strip=True) if desc_tag else ""

            # 언어
            lang_tag  = article.select_one("[itemprop='programmingLanguage']")
            lang      = lang_tag.get_text(strip=True) if lang_tag else "Unknown"

            # 전체 스타 / 포크
            links       = article.select("a.Link--muted")
            total_stars = _parse_number(links[0].get_text(strip=True)) if len(links) > 0 else 0
            forks       = _parse_number(links[1].get_text(strip=True)) if len(links) > 1 else 0

            # 이번 기간 획득 스타 (핵심!)
            period_stars_tag  = article.select_one("span.d-inline-block.float-sm-right")
            period_stars_text = period_stars_tag.get_text(strip=True) if period_stars_tag else "0"
            stars_this_period = _parse_number(re.sub(r"[^0-9,k]", "", period_stars_text.split()[0]))

            repo = {
                "name":              full_name,
                "description":       description,
                "stars":             total_stars,
                "forks":             forks,
                "language":          lang,
                "url":               f"https://github.com/{full_name}",
                "topics":            [],
                "stars_this_period": stars_this_period,
                "trend_score":       calculate_trend_score(stars_this_period, total_stars, forks),
            }
            repos.append(repo)

        return sorted(repos, key=lambda r: r["trend_score"], reverse=True)

    except Exception as e:
        print(f"[github_tools] 스크래핑 오류: {e}")
        return []


def get_language_stats(repos: list) -> dict:
    stats: dict = {}
    for repo in repos:
        lang = repo.get("language") or "Unknown"
        stats[lang] = stats.get(lang, 0) + 1
    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))


def get_top_topics(repos: list, top_n: int = 10) -> dict:
    topics: dict = {}
    for repo in repos:
        for topic in repo.get("topics", []):
            topics[topic] = topics.get(topic, 0) + 1
    return dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:top_n])
