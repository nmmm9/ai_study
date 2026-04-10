"""로또 당첨번호 조회 — k-lotto 방식 (dhlottery.co.kr)."""

import re
import httpx
from tools.registry import register_tool

HEADERS = {"accept": "application/json, text/html;q=0.9", "user-agent": "k-skill/k-lotto"}
LATEST_URL = "https://www.dhlottery.co.kr/lt645/result"
DETAIL_URL = "https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do"


@register_tool(
    name="lotto_results",
    description="한국 로또 6/45 당첨번호를 조회합니다. 회차를 지정하지 않으면 최신 회차를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "round": {"type": "integer", "description": "회차 번호 (없으면 최신)"},
        },
    },
)
async def lotto_results(round: int = None) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        if round is None:
            resp = await client.get(LATEST_URL, headers=HEADERS)
            # k-lotto 원본: id="opt_val" value="(\d+)"
            match = re.search(r'id="opt_val"[^>]*value="(\d+)"', resp.text, re.I)
            if not match:
                # fallback: 회차 숫자 추출
                match = re.search(r"(\d+)\s*회", resp.text)
            if match:
                round = int(match.group(1))
            else:
                return {"error": "최신 회차를 찾을 수 없습니다"}

        resp = await client.get(
            DETAIL_URL,
            params={"srchDir": "center", "srchLtEpsd": str(round)},
            headers=HEADERS,
        )

        if resp.status_code != 200:
            return {"error": f"로또 {round}회 조회 실패"}

        try:
            data = resp.json()
            items = data.get("data", {}).get("list", [])
            if not items:
                return {"error": f"{round}회 결과 없음"}

            item = items[0]
            numbers = sorted([
                item.get("tm1WnNo"), item.get("tm2WnNo"), item.get("tm3WnNo"),
                item.get("tm4WnNo"), item.get("tm5WnNo"), item.get("tm6WnNo"),
            ])
            bonus = item.get("bnsWnNo")
            draw_date = item.get("ltRflYmd", "")
            if len(draw_date) == 8:
                draw_date = f"{draw_date[:4]}-{draw_date[4:6]}-{draw_date[6:8]}"

            return {
                "round": round,
                "date": draw_date,
                "numbers": numbers,
                "bonus": bonus,
                "prize_1st": f"{item.get('rnk1WnAmt', 0):,}원",
                "winners_1st": item.get("rnk1WnNope", 0),
            }
        except Exception as e:
            return {"error": f"파싱 실패: {str(e)}"}
