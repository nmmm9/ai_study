"""
my_github.py - 내 GitHub 레포 분석 + 트렌드 비교 (Week 13)

내 GitHub 레포를 가져와서 현재 트렌딩과 비교하고
공부하면 좋을 기술을 추천해줌
"""
import os

import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

_llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY", ""))


def get_my_repos(username: str) -> list[dict]:
    token   = os.getenv("GITHUB_TOKEN", "").strip()
    headers = {
        "Authorization": f"token {token}",
        "Accept":        "application/vnd.github.v3+json",
    }
    repos = []
    page  = 1
    while len(repos) < 100:
        resp = requests.get(
            f"https://api.github.com/users/{username}/repos",
            headers=headers,
            params={"sort": "updated", "per_page": 30, "page": page},
            timeout=10,
        )
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        repos.extend(data)
        page += 1
        if len(data) < 30:
            break

    return [
        {
            "name":        r["name"],
            "description": r.get("description") or "",
            "language":    r.get("language") or "",
            "stars":       r.get("stargazers_count", 0),
            "topics":      r.get("topics", []),
            "updated_at":  r.get("updated_at", "")[:10],
        }
        for r in repos
        if not r.get("fork")
    ]


def analyze_my_github(username: str, trend_report: dict) -> dict:
    my_repos = get_my_repos(username)
    if not my_repos:
        return {"error": f"'{username}' 유저의 레포를 가져올 수 없습니다."}

    # 내 언어 통계
    my_langs: dict[str, int] = {}
    for r in my_repos:
        if r["language"]:
            my_langs[r["language"]] = my_langs.get(r["language"], 0) + 1
    my_lang_sorted = sorted(my_langs.items(), key=lambda x: x[1], reverse=True)

    trend_langs = trend_report.get("language_stats", {})
    trend_repos = trend_report.get("repos", [])

    my_repo_summary = "\n".join([
        f"- {r['name']} ({r['language'] or 'N/A'}): {r['description'][:60]}"
        for r in my_repos[:15]
    ])
    trend_summary = "\n".join([
        f"- {r['name']} ({r.get('language', 'N/A')}): {r.get('description', '')[:60]}"
        for r in trend_repos[:15]
    ])

    # 겹치는 언어 계산
    my_lang_set    = set(my_langs.keys())
    trend_lang_set = set(trend_langs.keys())
    overlap        = my_lang_set & trend_lang_set
    match_pct      = round(len(overlap) / max(len(my_lang_set), 1) * 100)

    response = _llm.invoke(f"""당신은 개발자 커리어 멘토입니다.
아래 개발자의 GitHub 레포와 현재 GitHub 트렌딩을 비교해서 인사이트를 제공해주세요.

[내 GitHub 레포 ({len(my_repos)}개, fork 제외)]
주요 사용 언어: {', '.join(f'{l}({c}개)' for l, c in my_lang_sorted[:5])}
{my_repo_summary}

[현재 GitHub 트렌딩]
트렌딩 언어: {', '.join(f'{l}({c}개)' for l, c in list(trend_langs.items())[:5])}
{trend_summary}

[Judge 트렌드 결론]
{trend_report.get('judge_decision', '')[:500]}

다음을 한국어로 분석해주세요:
1. 내가 사용하는 기술과 트렌딩 기술의 일치도 (몇 %나 겹치는지)
2. 내가 하고 있는 것 중 트렌드와 잘 맞는 부분
3. 트렌딩이지만 내가 아직 안 하고 있는 기술
4. 지금 당장 공부하면 좋을 기술 TOP 3 (이유 포함)
5. 한 줄 총평
""")

    return {
        "username":        username,
        "my_repo_count":   len(my_repos),
        "my_languages":    dict(my_lang_sorted[:7]),
        "trend_languages": dict(list(trend_langs.items())[:7]),
        "overlap_langs":   list(overlap),
        "match_pct":       match_pct,
        "analysis":        response.content,
        "my_repos":        my_repos[:10],
    }
