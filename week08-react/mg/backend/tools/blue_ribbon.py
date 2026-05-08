"""블루리본 맛집 검색 — k-skill-proxy.

proxy endpoint는 latitude, longitude, distanceMeters, limit 를 받는다.
zone1/isAround 같은 파라미터는 블루리본 공식 표면 직접 호출용이고,
proxy 경유 시에는 좌표 기반으로 검색해야 한다.
좌표를 모르면 카카오맵 검색으로 anchor를 잡은 뒤 좌표를 전달하는 것이 정석이지만,
이 도구에서는 간이로 카카오맵 검색 → 좌표 추출 → proxy 호출 흐름을 사용한다.
"""

import re
import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"
KAKAO_SEARCH_URL = "https://m.map.kakao.com/actions/searchView"
KAKAO_PANEL_URL = "https://place-api.map.kakao.com/places/panel3"


@register_tool(
    name="blue_ribbon_nearby",
    description="블루리본 맛집을 지역명으로 검색합니다. 반드시 사용자에게 지역을 물어본 후 호출하세요. 예: 강남, 홍대, 부산 해운대",
    parameters={
        "type": "object",
        "properties": {
            "zone": {"type": "string", "description": "지역명 (예: 강남, 홍대, 이태원, 해운대)"},
            "distance": {"type": "integer", "description": "검색 반경 (미터, 기본 1000)", "default": 1000},
        },
        "required": ["zone"],
    },
)
async def blue_ribbon_nearby(zone: str, distance: int = 1000) -> dict:
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        # Step 1: 카카오맵에서 좌표를 찾는다
        lat, lng = await _resolve_coordinates(client, zone)
        if lat is None or lng is None:
            return {"error": f"'{zone}' 지역의 좌표를 찾을 수 없습니다"}

        # Step 2: proxy에 좌표 기반 검색 요청
        resp = await client.get(
            f"{PROXY}/v1/blue-ribbon/nearby",
            params={
                "latitude": str(lat),
                "longitude": str(lng),
                "distanceMeters": str(distance),
                "limit": "10",
            },
        )
        if resp.status_code != 200:
            return {"error": f"맛집 검색 실패 (status {resp.status_code})"}

        data = resp.json()

        # Simplify results
        items = data.get("items", [])
        if isinstance(items, list) and items:
            simplified = []
            for r in items[:10]:
                simplified.append({
                    "name": r.get("name", ""),
                    "category": r.get("category", ""),
                    "ribbonCount": r.get("ribbonCount", ""),
                    "ribbonType": r.get("ribbonType", ""),
                    "address": r.get("address", ""),
                    "distanceMeters": r.get("distanceMeters", ""),
                })
            return {"zone": zone, "count": len(simplified), "restaurants": simplified}

        return data


async def _resolve_coordinates(client: httpx.AsyncClient, query: str):
    """카카오맵 검색 → panel3 JSON에서 좌표 추출."""
    try:
        resp = await client.get(
            KAKAO_SEARCH_URL,
            params={"q": query},
            headers={"user-agent": "Mozilla/5.0"},
        )
        if resp.status_code != 200:
            return None, None

        # confirmid 추출
        ids = re.findall(r'"confirmid"\s*:\s*"(\d+)"', resp.text, re.I)
        if not ids:
            ids = re.findall(r'"id"\s*:\s*"?(\d+)"?', resp.text)
        if not ids:
            return None, None

        # panel3 JSON에서 좌표 추출
        panel_resp = await client.get(
            f"{KAKAO_PANEL_URL}/{ids[0]}",
            headers={
                "user-agent": "Mozilla/5.0",
                "accept": "application/json, text/plain, */*",
                "origin": "https://place.map.kakao.com",
                "referer": "https://place.map.kakao.com/",
            },
        )
        if panel_resp.status_code == 200:
            panel = panel_resp.json()
            basic = panel.get("basicInfo", {})
            lat = basic.get("wpointx") or basic.get("ycoord")
            lng = basic.get("wpointy") or basic.get("xcoord")
            # panel3 uses y=lat, x=lng
            if lat and lng:
                return float(basic.get("ycoord", lat)), float(basic.get("xcoord", lng))
    except Exception:
        pass
    return None, None
