"""K리그 축구 결과 — kleague.com POST API."""

import httpx
from datetime import datetime
from tools.registry import register_tool

# k-skills 원본 헤더
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "content-type": "application/json; charset=utf-8",
    "user-agent": "k-skill/kleague-results",
}


@register_tool(
    name="kleague_results",
    description="K리그 축구 경기 결과와 순위를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "조회할 날짜 (YYYY-MM-DD, 없으면 오늘)"},
            "league": {"type": "string", "enum": ["K1", "K2"], "description": "K1(1부) 또는 K2(2부)", "default": "K1"},
        },
    },
)
async def kleague_results(date: str = None, league: str = "K1") -> dict:
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    year, month, day = date.split("-")
    # k-skills 원본: normalizeLeagueId → 숫자 1 또는 2
    league_id = 1 if league == "K1" else 2
    # k-skills 원본: month는 zero-padded string
    month_padded = month.zfill(2)
    # k-skills 원본: dotted date format for filtering
    dotted_date = f"{year}.{month_padded}.{day}"

    async with httpx.AsyncClient(timeout=10) as client:
        # k-skills 원본: POST with JSON.stringify body
        resp = await client.post(
            "https://www.kleague.com/getScheduleList.do",
            content=f'{{"year":"{year}","month":"{month_padded}","leagueId":{league_id}}}',
            headers=HEADERS,
        )
        if resp.status_code != 200:
            return {"error": "K리그 조회 실패"}

        try:
            payload = resp.json()
            # k-skills 원본: payload.data.scheduleList
            data = payload.get("data", payload) if isinstance(payload, dict) else payload
            schedule_list = []
            if isinstance(data, dict):
                schedule_list = data.get("scheduleList", data.get("list", []))
            elif isinstance(data, list):
                schedule_list = data

            # Filter by exact date (dotted format: 2026.04.05)
            results = []
            for g in schedule_list:
                game_date = g.get("gameDate", "")
                if game_date == dotted_date or date.replace("-", "") in str(game_date).replace(".", "").replace("-", ""):
                    home_goal = g.get("homeGoal", "-")
                    away_goal = g.get("awayGoal", "-")
                    status = "종료" if g.get("endYn") == "Y" else g.get("gameStatus", "예정")
                    results.append({
                        "home": g.get("homeTeamName", ""),
                        "away": g.get("awayTeamName", ""),
                        "score": f"{home_goal}:{away_goal}",
                        "status": status,
                        "stadium": g.get("fieldName", g.get("fieldNameFull", "")),
                        "time": g.get("gameTime", ""),
                    })

            if not results:
                return {"date": date, "league": league, "games": [], "message": "해당 날짜에 경기가 없습니다"}
            return {"date": date, "league": league, "games": results}
        except Exception:
            return {"date": date, "error": "파싱 실패"}
