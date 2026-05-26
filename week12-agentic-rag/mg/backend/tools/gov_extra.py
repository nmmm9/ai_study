"""정부/공공 확장 — 응급실 / SH 공고 / 법원경매 / 지방선거 / 기부.

응급실: e-gen.or.kr 직접 호출
SH: www.i-sh.co.kr 게시판 HTML 파싱
법원경매: courtauction.go.kr 공고
지방선거: info.nec.go.kr 후보 검색
기부: 1365.go.kr 안내
"""

import re
import httpx
from tools.registry import register_tool

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


# ─────────────────────────────────────
# 응급실 — e-gen.or.kr
# ─────────────────────────────────────

@register_tool(
    name="emergency_room_beds",
    description="응급실 위치 + 가용 병상 정보를 조회합니다. 위도/경도 또는 주소 키워드 입력.",
    parameters={
        "type": "object",
        "properties": {
            "lat": {"type": "number", "description": "위도"},
            "lon": {"type": "number", "description": "경도"},
            "address": {"type": "string", "description": "주소 키워드 (lat/lon 없을 때)"},
            "limit": {"type": "integer", "default": 5},
        },
    },
)
async def emergency_room_beds(lat: float | None = None, lon: float | None = None,
                               address: str | None = None, limit: int = 5) -> dict:
    if lat is None or lon is None:
        if not address:
            return {"error": "위도/경도 또는 주소가 필요합니다"}
        # Geocode via k-skill-proxy kakao
        async with httpx.AsyncClient(timeout=12) as c:
            r = await c.get("https://k-skill-proxy.nomadamas.org/v1/kakao-local/geocode",
                            params={"query": address})
            if r.status_code == 200:
                geo = r.json()
                docs = (geo.get("documents") or geo.get("results") or [])
                if docs:
                    first = docs[0]
                    lat = float(first.get("y") or first.get("lat"))
                    lon = float(first.get("x") or first.get("lon"))
        if lat is None or lon is None:
            return {"error": "주소 지오코딩 실패"}

    url = "https://www.e-gen.or.kr/egen/retrieve_emergency_room_list.do"
    headers = {
        "User-Agent": UA,
        "Origin": "https://www.e-gen.or.kr",
        "Referer": "https://www.e-gen.or.kr/egen/search_emergency_room.do",
        "X-Requested-With": "XMLHttpRequest",
    }
    payload = {"latitude": lat, "longitude": lon, "page": 1, "size": limit}
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        resp = await client.post(url, data=payload)
        if resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                return {"raw": resp.text[:2000]}
        return {"error": f"응급실 조회 실패 (status {resp.status_code})"}


# ─────────────────────────────────────
# SH 공고 — i-sh.co.kr
# ─────────────────────────────────────

@register_tool(
    name="sh_notice_search",
    description="SH 서울주택도시공사 임대주택/매입임대 공고를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ["rent", "sale"],
                     "description": "rent=임대, sale=분양", "default": "rent"},
            "limit": {"type": "integer", "default": 10},
        },
    },
)
async def sh_notice_search(type: str = "rent", limit: int = 10) -> dict:
    seq = "2" if type == "rent" else "1"
    url = f"https://www.i-sh.co.kr/app/lay2/program/S1T294C297/www/brd/m_247/list.do"
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}, follow_redirects=True) as client:
        resp = await client.get(url, params={"multi_itm_seq": seq})
        if resp.status_code != 200:
            return {"error": f"SH 공고 조회 실패 (status {resp.status_code})"}

    notices = []
    # <a href="view.do?multi_itm_seq=2&seq=N">제목</a> 패턴
    for m in re.finditer(r'view\.do\?multi_itm_seq=\d+&amp;seq=(\d+)[^>]*>([^<]+)</a>', resp.text):
        notices.append({
            "seq": m.group(1),
            "title": m.group(2).strip(),
            "url": f"https://www.i-sh.co.kr/app/lay2/program/S1T294C297/www/brd/m_247/view.do?multi_itm_seq={seq}&seq={m.group(1)}",
        })
        if len(notices) >= limit:
            break
    return {"type": type, "count": len(notices), "notices": notices}


# ─────────────────────────────────────
# 법원경매 — courtauction.go.kr
# ─────────────────────────────────────

@register_tool(
    name="court_auction_search",
    description="대법원 부동산 매각공고를 조회합니다. 법원/매각기일/사건번호 기반.",
    parameters={
        "type": "object",
        "properties": {
            "court": {"type": "string", "description": "법원명 (예: 서울중앙지방법원)"},
            "limit": {"type": "integer", "default": 10},
        },
    },
)
async def court_auction_search(court: str | None = None, limit: int = 10) -> dict:
    # 법원경매 portal은 JS 기반 SPA — 검색 URL 만 안내
    url = "https://www.courtauction.go.kr/pgj/index.on?w2xPath=/pgj/ui/pgj100/PGJ143M01.xml&pgjId=143M01"
    return {
        "hint": "법원경매정보 사이트는 JS 기반이라 직접 파싱이 어렵습니다",
        "search_url": url,
        "court_filter": court,
        "guidance": "원본 SKILL.md 의 안내대로 사용자가 직접 사이트에서 검색 권장",
    }


# ─────────────────────────────────────
# 지방선거 후보 — info.nec.go.kr
# ─────────────────────────────────────

@register_tool(
    name="local_election_candidate_search",
    description="중앙선관위 통합검색으로 지방선거 후보를 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "후보명 또는 지역명"},
            "election_year": {"type": "integer", "description": "선거 연도"},
        },
        "required": ["query"],
    },
)
async def local_election_candidate_search(query: str, election_year: int | None = None) -> dict:
    url = "https://info.nec.go.kr/search/searchCandidate.xhtml"
    params = {"searchKeyword": query}
    if election_year:
        params["electionYear"] = election_year
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}, follow_redirects=True) as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return {"error": f"선거 후보 조회 실패 (status {resp.status_code})"}

    # JSF 기반 - HTML 에서 후보 카드 추출
    candidates = []
    for m in re.finditer(r'<dl[^>]*class="[^"]*candi[^"]*"[^>]*>(.*?)</dl>', resp.text, re.DOTALL):
        block = m.group(1)
        name_m = re.search(r'<dt[^>]*>([^<]+)</dt>', block)
        if name_m:
            candidates.append({"name": name_m.group(1).strip()})
        if len(candidates) >= 20:
            break
    return {"query": query, "count": len(candidates), "candidates": candidates, "search_url": url}


# ─────────────────────────────────────
# 기부처 — 1365.go.kr
# ─────────────────────────────────────

@register_tool(
    name="donation_place_search",
    description="공식 기부처(자원봉사 1365 통합) 정보를 안내합니다. 분야별 기부처 검색.",
    parameters={
        "type": "object",
        "properties": {
            "category": {"type": "string", "description": "분야 (예: '아동', '환경', '의료')"},
        },
    },
)
async def donation_place_search(category: str | None = None) -> dict:
    # 1365 자원봉사 통합 안내 (구 나눔코리아 → 통합)
    return {
        "hint": "구 나눔코리아(nanumkorea.go.kr)는 1365 자원봉사로 통합되었습니다",
        "official_entry": "https://www.1365.go.kr/dntn/main.do",
        "category": category,
        "guidance": "분야 기부처는 1365 포털 또는 한국가이드스타(www.guidestar.or.kr) 권장",
    }
