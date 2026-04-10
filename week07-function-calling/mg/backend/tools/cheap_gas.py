"""최저가 주유소 검색 — Opinet via k-skill-proxy.

proxy endpoint /v1/opinet/around 는 KATEC 좌표(x, y), radius, prodcd, sort 를 받는다.
locationHint 같은 파라미터는 존재하지 않으므로,
먼저 카카오맵에서 WGS84 좌표를 얻고 KATEC으로 변환한 뒤 proxy에 전달한다.
"""

import re
import math
import httpx
from tools.registry import register_tool

PROXY = "https://k-skill-proxy.nomadamas.org"
KAKAO_SEARCH_URL = "https://m.map.kakao.com/actions/searchView"
KAKAO_PANEL_URL = "https://place-api.map.kakao.com/places/panel3"

FUEL_CODES = {"gasoline": "B027", "diesel": "D047", "lpg": "K015"}


def _wgs84_to_katec(lat: float, lng: float) -> tuple[float, float]:
    """WGS84 → KATEC 좌표 변환.

    k-skills cheap-gas-nearby/src/parse.js wgs84ToKatec() 의 Python 포팅.
    1단계: WGS84 → Bessel 측지 변환 (3-parameter Molodensky)
    2단계: Bessel → KATEC TM 투영
    """
    # Constants
    WGS84_A = 6378137.0
    WGS84_F = 1 / 298.257223563
    BESSEL_A = 6377397.155
    BESSEL_F = 1 / 299.1528128
    KATEC_LAT0 = math.radians(38.0)
    KATEC_LON0 = math.radians(128.0)
    KATEC_FE = 400000.0
    KATEC_FN = 600000.0
    KATEC_SCALE = 0.9999
    DX, DY, DZ = 146.43, -507.89, -681.46

    # Step 1: WGS84 → Bessel (datum shift)
    src_es = 2 * WGS84_F - WGS84_F ** 2
    tgt_es = 2 * BESSEL_F - BESSEL_F ** 2

    lat_r = math.radians(lat)
    lng_r = math.radians(lng)
    sin_lat = math.sin(lat_r)
    cos_lat = math.cos(lat_r)
    N = WGS84_A / math.sqrt(1 - src_es * sin_lat ** 2)

    x_cart = N * cos_lat * math.cos(lng_r) + DX
    y_cart = N * cos_lat * math.sin(lng_r) + DY
    z_cart = N * (1 - src_es) * sin_lat + DZ

    bessel_lon = math.atan2(y_cart, x_cart)
    h = math.sqrt(x_cart ** 2 + y_cart ** 2)
    bessel_lat = math.atan2(z_cart, h * (1 - tgt_es))

    for _ in range(8):
        sin_b = math.sin(bessel_lat)
        Nb = BESSEL_A / math.sqrt(1 - tgt_es * sin_b ** 2)
        next_lat = math.atan2(z_cart + tgt_es * Nb * sin_b, h)
        if abs(next_lat - bessel_lat) < 1e-14:
            bessel_lat = next_lat
            break
        bessel_lat = next_lat

    # Step 2: Bessel → KATEC (TM projection)
    bessel_es = tgt_es
    esp = bessel_es / (1 - bessel_es)

    sin_b = math.sin(bessel_lat)
    cos_b = math.cos(bessel_lat)
    tan_b = math.tan(bessel_lat)
    Nv = BESSEL_A / math.sqrt(1 - bessel_es * sin_b ** 2)
    T = tan_b ** 2
    C = esp * cos_b ** 2
    A = (bessel_lon - KATEC_LON0) * cos_b

    def meridional_arc(phi):
        e2 = bessel_es
        return BESSEL_A * (
            (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * phi
            - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * phi)
            + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * phi)
            - (35 * e2 ** 3 / 3072) * math.sin(6 * phi)
        )

    M = meridional_arc(bessel_lat)
    M0 = meridional_arc(KATEC_LAT0)

    x = KATEC_FE + KATEC_SCALE * Nv * (
        A + (1 - T + C) * A ** 3 / 6
        + (5 - 18 * T + T ** 2 + 72 * C - 58 * esp) * A ** 5 / 120
    )
    y = KATEC_FN + KATEC_SCALE * (
        M - M0
        + Nv * tan_b * (
            A ** 2 / 2
            + (5 - T + 9 * C + 4 * C ** 2) * A ** 4 / 24
            + (61 - 58 * T + T ** 2 + 600 * C - 330 * esp) * A ** 6 / 720
        )
    )
    return x, y


@register_tool(
    name="cheap_gas_nearby",
    description="주변 최저가 주유소를 검색합니다. 반드시 사용자에게 위치를 물어본 후 호출하세요. 연료 종류(휘발유/경유/LPG)도 확인하세요.",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "위치 (예: 강남역, 서울역, 안양)"},
            "fuel_type": {"type": "string", "enum": ["gasoline", "diesel", "lpg"], "description": "연료 종류 (gasoline=휘발유, diesel=경유, lpg=LPG)", "default": "gasoline"},
            "radius": {"type": "integer", "description": "검색 반경 (미터, 기본 1000, 최대 5000)", "default": 1000},
        },
        "required": ["location"],
    },
)
async def cheap_gas_nearby(location: str, fuel_type: str = "gasoline", radius: int = 1000) -> dict:
    prodcd = FUEL_CODES.get(fuel_type, "B027")

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        # Step 1: 카카오맵에서 WGS84 좌표 확보
        lat, lng = await _resolve_coordinates(client, location)
        if lat is None or lng is None:
            return {"error": f"'{location}' 위치의 좌표를 찾을 수 없습니다"}

        # Step 2: WGS84 → KATEC 변환
        katec_x, katec_y = _wgs84_to_katec(lat, lng)

        # Step 3: proxy에 KATEC 좌표 기반 검색
        resp = await client.get(
            f"{PROXY}/v1/opinet/around",
            params={
                "x": str(katec_x),
                "y": str(katec_y),
                "radius": str(min(radius, 5000)),
                "prodcd": prodcd,
                "sort": "1",
            },
        )
        if resp.status_code != 200:
            return {"error": f"주유소 검색 실패 (status {resp.status_code})"}

        data = resp.json()

        # Opinet 응답: RESULT.OIL 배열
        oil_list = data.get("RESULT", {}).get("OIL", [])
        if isinstance(oil_list, list) and oil_list:
            stations = []
            for s in oil_list[:5]:
                stations.append({
                    "name": s.get("OS_NM", ""),
                    "price": s.get("PRICE", ""),
                    "brand": s.get("POLL_DIV_CD", ""),
                    "address": s.get("NEW_ADR", s.get("VAN_ADR", "")),
                    "id": s.get("UNI_ID", ""),
                    "distance": s.get("DISTANCE", ""),
                })
            return {"location": location, "fuel": fuel_type, "stations": stations}

        return data


async def _resolve_coordinates(client: httpx.AsyncClient, query: str):
    """카카오맵 검색 → panel3 JSON에서 WGS84 좌표 추출."""
    try:
        resp = await client.get(
            KAKAO_SEARCH_URL,
            params={"q": query},
            headers={"user-agent": "Mozilla/5.0"},
        )
        if resp.status_code != 200:
            return None, None

        ids = re.findall(r'"confirmid"\s*:\s*"(\d+)"', resp.text, re.I)
        if not ids:
            ids = re.findall(r'"id"\s*:\s*"?(\d+)"?', resp.text)
        if not ids:
            return None, None

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
            y = basic.get("ycoord")
            x = basic.get("xcoord")
            if y and x:
                return float(y), float(x)
    except Exception:
        pass
    return None, None
