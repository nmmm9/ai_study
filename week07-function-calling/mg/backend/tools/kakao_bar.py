"""카카오맵 주변 바/술집 검색 — place-api.map.kakao.com panel3 사용.

k-skills 원본은 panel3 endpoint (https://place-api.map.kakao.com/places/panel3/<id>)를 사용한다.
place.map.kakao.com/main/v/ 는 deprecated된 경로이므로 panel3를 사용한다.
"""

import httpx
import re
from tools.registry import register_tool

SEARCH_URL = "https://m.map.kakao.com/actions/searchView"
PANEL_URL = "https://place-api.map.kakao.com/places/panel3"

BROWSER_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "ko,en-US;q=0.9,en;q=0.8",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
}

PANEL_HEADERS = {
    **BROWSER_HEADERS,
    "accept": "application/json, text/plain, */*",
    "origin": "https://place.map.kakao.com",
    "referer": "https://place.map.kakao.com/",
}


@register_tool(
    name="kakao_bar_nearby",
    description="카카오맵에서 주변 바/술집을 검색합니다. 지역명을 입력하면 근처 술집 정보를 반환합니다.",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "지역명 (예: 강남역, 홍대입구, 이태원)"},
        },
        "required": ["location"],
    },
)
async def kakao_bar_nearby(location: str) -> dict:
    query = f"{location} 술집"

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(
            SEARCH_URL,
            params={"q": query},
            headers=BROWSER_HEADERS,
        )
        if resp.status_code != 200:
            return {"error": "카카오맵 검색 실패"}

        # Extract place IDs from response
        place_ids = re.findall(r'"confirmid"\s*:\s*"(\d+)"', resp.text, re.I)
        if not place_ids:
            place_ids = re.findall(r'"id"\s*:\s*"?(\d+)"?', resp.text)

        results = []
        for pid in place_ids[:8]:
            try:
                # k-skills 원본: panel3 endpoint 사용
                detail = await client.get(
                    f"{PANEL_URL}/{pid}",
                    headers=PANEL_HEADERS,
                )
                if detail.status_code == 200:
                    data = detail.json()
                    basic = data.get("basicInfo", {})
                    addr_info = basic.get("address", {})
                    new_addr = addr_info.get("newaddr", {})

                    # 영업시간 확인
                    open_hours = basic.get("openHour", {})
                    period_list = open_hours.get("periodList", [])
                    time_info = ""
                    if period_list:
                        time_list = period_list[0].get("timeList", [])
                        if time_list:
                            time_info = f"{time_list[0].get('timeSE', '')}"

                    results.append({
                        "name": basic.get("placenamefull", ""),
                        "category": basic.get("category", {}).get("catename", ""),
                        "address": new_addr.get("newaddrfull", addr_info.get("addrfull", "")),
                        "phone": basic.get("phonenum", ""),
                        "openHour": time_info,
                    })
            except Exception:
                continue

        return {"location": location, "count": len(results), "bars": results[:5]}
