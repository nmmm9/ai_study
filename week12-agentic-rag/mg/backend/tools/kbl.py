"""KBL 한국프로농구 결과 — api.kbl.or.kr 직접 호출."""

from datetime import datetime, timezone, timedelta
import httpx
from tools.registry import register_tool

KST = timezone(timedelta(hours=9))
BASE = "https://api.kbl.or.kr"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Origin": "https://www.kbl.or.kr",
    "Referer": "https://www.kbl.or.kr/",
}


@register_tool(
    name="kbl_results",
    description="KBL 한국프로농구 경기 결과/일정/팀 순위를 조회합니다. 날짜 미지정 시 오늘 기준.",
    parameters={
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "YYYY-MM-DD (없으면 오늘)"},
            "team": {"type": "string", "description": "팀명 필터 (예: 서울 SK, 부산 KCC)"},
            "include_standings": {"type": "boolean", "default": True},
        },
    },
)
async def kbl_results(date: str | None = None, team: str | None = None,
                     include_standings: bool = True) -> dict:
    if not date:
        date = datetime.now(KST).strftime("%Y-%m-%d")

    out: dict = {"date": date}

    async with httpx.AsyncClient(timeout=12, headers=HEADERS) as client:
        # Match list
        ymd = date.replace("-", "")
        try:
            mresp = await client.post(
                f"{BASE}/match/list",
                json={"gameDate": ymd},
            )
            if mresp.status_code == 200:
                matches = mresp.json()
                if team:
                    matches_data = matches.get("data") or matches.get("matchList") or matches
                    if isinstance(matches_data, list):
                        filtered = [m for m in matches_data if team in str(m)]
                        out["matches"] = filtered
                    else:
                        out["matches"] = matches
                else:
                    out["matches"] = matches
            else:
                out["matches_error"] = f"status {mresp.status_code}"
        except Exception as e:
            out["matches_error"] = str(e)

        # Standings
        if include_standings:
            try:
                sresp = await client.post(f"{BASE}/league/rank/team", json={})
                if sresp.status_code == 200:
                    out["standings"] = sresp.json()
                else:
                    out["standings_error"] = f"status {sresp.status_code}"
            except Exception as e:
                out["standings_error"] = str(e)

    return out
