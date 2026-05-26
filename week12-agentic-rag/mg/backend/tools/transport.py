"""교통 — 고속버스 / 시외버스 / 휴양림 / 길찾기.

- 고속버스: KOBUS rotinf.do
- 시외버스: Tmoney intercitybus trmlInfEnty.do
- 휴양림: foresttrip.go.kr (HTML)
- 길찾기: ODsay (need ODSAY_API_KEY env)
"""

import os
import httpx
from tools.registry import register_tool

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
PROXY = "https://k-skill-proxy.nomadamas.org"


# ─────────────────────────────────────
# 고속버스 — KOBUS
# ─────────────────────────────────────

@register_tool(
    name="express_bus_search",
    description="고속버스 노선/시간표를 KOBUS 에서 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "depart": {"type": "string", "description": "출발 터미널 코드 또는 이름 (예: '서울경부', 'NAEK010')"},
            "arrival": {"type": "string", "description": "도착 터미널 코드 또는 이름"},
            "date": {"type": "string", "description": "출발일 YYYYMMDD"},
            "grade": {"type": "string", "description": "등급: 일반/우등/프리미엄"},
        },
        "required": ["depart", "arrival", "date"],
    },
)
async def express_bus_search(depart: str, arrival: str, date: str,
                              grade: str | None = None) -> dict:
    url = "https://www.kobus.co.kr/mrs/rotinf.do"
    payload = {
        "depTrmlCd": depart,
        "arrTrmlCd": arrival,
        "depPlandTime": date,
    }
    if grade:
        payload["lineGrdCd"] = grade
    headers = {
        "User-Agent": UA,
        "Origin": "https://www.kobus.co.kr",
        "Referer": "https://www.kobus.co.kr/main.do",
        "X-Requested-With": "XMLHttpRequest",
    }
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        resp = await client.post(url, data=payload)
        if resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                return {"raw": resp.text[:2000]}
        return {"error": f"고속버스 조회 실패 (status {resp.status_code})"}


# ─────────────────────────────────────
# 시외버스 — Tmoney
# ─────────────────────────────────────

@register_tool(
    name="intercity_bus_search",
    description="시외버스 노선/시간표를 Tmoney 에서 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "depart": {"type": "string", "description": "출발 터미널 코드"},
            "arrival": {"type": "string", "description": "도착 터미널 코드"},
            "date": {"type": "string", "description": "출발일 YYYYMMDD"},
        },
        "required": ["depart", "arrival", "date"],
    },
)
async def intercity_bus_search(depart: str, arrival: str, date: str) -> dict:
    url = "https://intercitybus.tmoney.co.kr/otck/readPcpySats.do"
    headers = {
        "User-Agent": UA,
        "Origin": "https://intercitybus.tmoney.co.kr",
        "Referer": "https://intercitybus.tmoney.co.kr/",
        "X-Requested-With": "XMLHttpRequest",
    }
    payload = {"startTrmnNo": depart, "endTrmnNo": arrival, "passDate": date}
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        resp = await client.post(url, data=payload)
        if resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                return {"raw": resp.text[:2000]}
        return {"error": f"시외버스 조회 실패 (status {resp.status_code})"}


@register_tool(
    name="bus_terminal_list",
    description="고속/시외버스 터미널 코드 목록을 조회합니다. (시외버스용)",
    parameters={"type": "object", "properties": {}},
)
async def bus_terminal_list() -> dict:
    url = "https://intercitybus.tmoney.co.kr/otck/trmlInfEnty.do"
    headers = {"User-Agent": UA, "X-Requested-With": "XMLHttpRequest"}
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        resp = await client.post(url, data={})
        if resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                return {"raw": resp.text[:2000]}
        return {"error": f"터미널 목록 조회 실패 (status {resp.status_code})"}


# ─────────────────────────────────────
# 숲나들e (국립휴양림)
# ─────────────────────────────────────

@register_tool(
    name="foresttrip_vacancy",
    description="국립자연휴양림 예약 가능 객실/캠핑장을 날짜로 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "check_in": {"type": "string", "description": "입실일 YYYY-MM-DD"},
            "nights": {"type": "integer", "description": "박수", "default": 1},
            "region": {"type": "string", "description": "지역명 (선택)"},
        },
        "required": ["check_in"],
    },
)
async def foresttrip_vacancy(check_in: str, nights: int = 1,
                              region: str | None = None) -> dict:
    # 숲나들e 는 Playwright/JS 기반이라 직접 호출이 제한적
    return {
        "hint": "숲나들e 는 JS SPA 라서 서버 사이드 직접 조회가 제한됩니다",
        "check_in": check_in,
        "nights": nights,
        "region": region,
        "search_url": f"https://foresttrip.go.kr/index.jsp",
        "guidance": "원본 SKILL.md 의 Playwright 스크립트 권장",
    }


# ─────────────────────────────────────
# 길찾기 — ODsay (proxy + Kakao geocode)
# ─────────────────────────────────────

@register_tool(
    name="korean_transit_route",
    description="한국 도어투도어 대중교통 길찾기 (지하철+버스+도보). 출발/도착 주소나 좌표 필요. ODSAY_API_KEY 환경변수 필요.",
    parameters={
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "출발지 (주소/장소명)"},
            "destination": {"type": "string", "description": "도착지 (주소/장소명)"},
        },
        "required": ["origin", "destination"],
    },
)
async def korean_transit_route(origin: str, destination: str) -> dict:
    api_key = os.environ.get("ODSAY_API_KEY")
    if not api_key:
        return {"error": "ODSAY_API_KEY 환경변수가 필요합니다 (https://lab.odsay.com 발급)"}

    async with httpx.AsyncClient(timeout=15) as client:
        # 1) Geocode both
        o = await client.get(f"{PROXY}/v1/kakao-local/geocode", params={"query": origin})
        d = await client.get(f"{PROXY}/v1/kakao-local/geocode", params={"query": destination})
        if o.status_code != 200 or d.status_code != 200:
            return {"error": "지오코딩 실패"}
        try:
            o_doc = (o.json().get("documents") or o.json().get("results") or [])[0]
            d_doc = (d.json().get("documents") or d.json().get("results") or [])[0]
            o_lat, o_lon = float(o_doc.get("y") or o_doc["lat"]), float(o_doc.get("x") or o_doc["lon"])
            d_lat, d_lon = float(d_doc.get("y") or d_doc["lat"]), float(d_doc.get("x") or d_doc["lon"])
        except (IndexError, KeyError, ValueError):
            return {"error": "좌표 추출 실패"}

        # 2) ODsay searchPubTransPathT
        odsay_url = "https://api.odsay.com/v1/api/searchPubTransPathT"
        params = {
            "apiKey": api_key,
            "SX": o_lon, "SY": o_lat,
            "EX": d_lon, "EY": d_lat,
            "OPT": 0,  # 0=추천, 1=최소환승, 2=최소시간
        }
        r = await client.get(odsay_url, params=params)
        if r.status_code == 200:
            data = r.json()
            return {
                "origin": {"address": origin, "lat": o_lat, "lon": o_lon},
                "destination": {"address": destination, "lat": d_lat, "lon": d_lon},
                "routes": data.get("result", {}).get("path", [])[:5],
            }
        return {"error": f"ODsay 조회 실패 (status {r.status_code})"}
