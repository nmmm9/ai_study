"""
github_tools.py - GitHub API 호출 함수 모음

GitHub Search API를 사용해 트렌딩 레포지토리 수집
공식 트렌딩 API가 없어서 "최근 생성 + 스타 많은 순" 으로 대체
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()


def _headers():
    return {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}


def get_trending_repos(language: str = "", period: str = "weekly", limit: int = 25) -> list:
    days = {"daily": 1, "weekly": 7, "monthly": 30}.get(period, 7)
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    query = f"created:>{since} stars:>10"
    if language:
        query += f" language:{language}"

    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": min(limit, 30),
    }

    try:
        response = requests.get(
            "https://api.github.com/search/repositories",
            headers=_headers(),
            params=params,
            timeout=10,
        )
        if response.status_code != 200:
            return []

        items = response.json().get("items", [])
        return [
            {
                "name":        item["full_name"],
                "description": item.get("description") or "",
                "stars":       item["stargazers_count"],
                "forks":       item["forks_count"],
                "language":    item.get("language") or "Unknown",
                "url":         item["html_url"],
                "topics":      item.get("topics", []),
                "created_at":  item["created_at"],
            }
            for item in items
        ]
    except Exception:
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
