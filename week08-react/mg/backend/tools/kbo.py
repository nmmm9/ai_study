"""KBO 야구 경기 결과 — koreabaseball.com API."""

import re
import httpx
from datetime import datetime
from tools.registry import register_tool


@register_tool(
    name="kbo_results",
    description="KBO 프로야구 경기 일정과 결과를 조회합니다. 날짜를 지정하지 않으면 오늘 경기를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "조회할 날짜 (YYYY-MM-DD, 없으면 오늘)"},
        },
    },
)
async def kbo_results(date: str = None) -> dict:
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    year, month, day = date.split("-")

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        resp = await client.post(
            "https://www.koreabaseball.com/ws/Schedule.asmx/GetScheduleList",
            data={
                "leId": "1",
                "srIdList": "0,9",
                "seasonId": year,
                "gameMonth": month,
                "gameDay": day,
                "teamId": "",
            },
            headers={
                "user-agent": "Mozilla/5.0",
                "content-type": "application/x-www-form-urlencoded",
            },
        )

        if resp.status_code != 200:
            return {"date": date, "error": "KBO 조회 실패"}

        try:
            data = resp.json()
            rows = data.get("rows", [])

            games = []
            current_date = ""

            for row_obj in rows:
                cells = row_obj.get("row", [])
                for cell in cells:
                    cls = cell.get("Class", "")
                    text = cell.get("Text", "")

                    if cls == "day":
                        current_date = re.sub(r"<[^>]+>", "", text).strip()

                    if cls == "play":
                        # Parse: <span>TEAM1</span><em><span>SCORE1</span><span>vs</span><span>SCORE2</span></em><span>TEAM2</span>
                        teams = re.findall(r"<span[^>]*>([^<]+)</span>", text)
                        # teams: [TEAM1, SCORE1, 'vs', SCORE2, TEAM2] or similar
                        teams_clean = [t for t in teams if t.strip() and t.strip() != "vs"]

                        if len(teams_clean) >= 4:
                            games.append({
                                "date": current_date,
                                "away": teams_clean[0],
                                "away_score": teams_clean[1],
                                "home_score": teams_clean[2],
                                "home": teams_clean[3],
                                "result": f"{teams_clean[0]} {teams_clean[1]}:{teams_clean[2]} {teams_clean[3]}",
                            })
                        elif len(teams_clean) >= 2:
                            games.append({
                                "date": current_date,
                                "away": teams_clean[0],
                                "home": teams_clean[-1],
                                "result": f"{teams_clean[0]} vs {teams_clean[-1]}",
                            })

            # Filter by exact requested date (e.g. "04.05")
            target_date = f"{month}.{day}"
            filtered = [g for g in games if target_date in g.get("date", "")]

            if not filtered:
                return {"date": date, "games": [], "message": f"{date}에는 경기가 없습니다 (월요일은 보통 휴식일)"}

            return {"date": date, "games": filtered}
        except Exception as e:
            return {"date": date, "error": f"파싱 실패: {str(e)}"}
