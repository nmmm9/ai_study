"""LCK 롤 e스포츠 결과 — lolesports API."""

import httpx
from datetime import datetime
from tools.registry import register_tool


@register_tool(
    name="lck_results",
    description="LCK(LoL 챔피언스 코리아) e스포츠 경기 결과를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "조회할 날짜 (YYYY-MM-DD, 없으면 오늘)"},
            "team": {"type": "string", "description": "특정 팀 필터 (선택, 예: T1, 젠지, 한화)"},
        },
    },
)
async def lck_results(date: str = None, team: str = None) -> dict:
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # Team alias normalization
    aliases = {
        "t1": "T1", "skt": "T1", "sk텔레콤": "T1",
        "젠지": "Gen.G", "genG": "Gen.G", "geng": "Gen.G",
        "한화": "Hanwha Life", "hle": "Hanwha Life",
        "디플": "DRX", "drx": "DRX",
        "kt": "KT", "롤스터": "KT",
        "농심": "Nongshim", "ns": "Nongshim",
        "광동": "Kwangdong", "kdf": "Kwangdong",
        "담원": "Dplus", "dk": "Dplus", "디플러스": "Dplus",
        "브리온": "BRO", "bro": "BRO",
        "피어엑스": "FearX", "fearx": "FearX", "lsb": "FearX",
    }
    if team:
        team = aliases.get(team.lower(), team)

    async with httpx.AsyncClient(timeout=15) as client:
        # LoL Esports schedule API
        try:
            resp = await client.get(
                "https://esports-api.lolesports.com/persisted/gw/getSchedule",
                params={"hl": "ko-KR", "leagueId": "98767991310872058"},
                headers={
                    "x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z",
                    "user-agent": "k-skill/lck-analytics",
                },
            )
            if resp.status_code != 200:
                return {"error": f"LCK 조회 실패 (status {resp.status_code})"}

            data = resp.json()
            schedule = data.get("data", {}).get("schedule", {})
            events = schedule.get("events", [])

            results = []
            for event in events:
                start = event.get("startTime", "")
                if date not in start:
                    continue

                match = event.get("match", {})
                teams_data = match.get("teams", [])
                if len(teams_data) < 2:
                    continue

                t1_name = teams_data[0].get("name", "")
                t2_name = teams_data[1].get("name", "")
                t1_wins = teams_data[0].get("result", {}).get("gameWins", 0)
                t2_wins = teams_data[1].get("result", {}).get("gameWins", 0)
                state = event.get("state", "")

                if team and team not in t1_name and team not in t2_name:
                    continue

                results.append({
                    "team1": t1_name,
                    "team2": t2_name,
                    "score": f"{t1_wins}:{t2_wins}",
                    "state": state,
                    "time": start[:16],
                })

            if not results:
                return {"date": date, "matches": [], "message": f"{date}에 LCK 경기가 없습니다"}
            return {"date": date, "matches": results}

        except Exception as e:
            return {"error": f"LCK 조회 오류: {str(e)}"}
