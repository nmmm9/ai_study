"""문화 — 영화관 / 마라톤 / 공연 티켓.

- 영화: CGV/메가박스/롯데 search (간이 안내)
- 마라톤: gorunning.kr/races + triathlon.or.kr
- 티켓: yes24 + interpark
"""

import re
import httpx
from urllib.parse import quote
from tools.registry import register_tool

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


# ─────────────────────────────────────
# 영화관 검색 — CGV / 메가박스 / 롯데시네마
# ─────────────────────────────────────

@register_tool(
    name="korean_cinema_search",
    description="한국 영화관(CGV, 메가박스, 롯데시네마) 상영작/시간표를 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "chain": {"type": "string", "enum": ["cgv", "megabox", "lotte"]},
            "query": {"type": "string", "description": "영화관 이름 또는 영화 제목"},
        },
        "required": ["chain"],
    },
)
async def korean_cinema_search(chain: str, query: str | None = None) -> dict:
    chains = {
        "cgv": ("https://www.cgv.co.kr/movies/", "https://www.cgv.co.kr/theaters/"),
        "megabox": ("https://www.megabox.co.kr/movie", "https://www.megabox.co.kr/theater"),
        "lotte": ("https://www.lottecinema.co.kr/NLCHS/Movie/MovieList",
                  "https://www.lottecinema.co.kr/NLCHS/Cinema/Cinema"),
    }
    if chain not in chains:
        return {"error": f"지원 안 함: {chain}"}
    movies_url, theaters_url = chains[chain]
    return {
        "chain": chain,
        "query": query,
        "movies_url": movies_url,
        "theaters_url": theaters_url,
        "hint": "각 영화관 웹은 JS SPA 라 정확한 시간표는 공식 사이트에서 확인 권장",
    }


# ─────────────────────────────────────
# 마라톤/철인3종 일정
# ─────────────────────────────────────

@register_tool(
    name="korean_marathon_schedule",
    description="고러닝(gorunning.kr) 마라톤/철인3종 경기 일정을 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "year": {"type": "integer", "description": "조회 연도"},
            "limit": {"type": "integer", "default": 10},
        },
    },
)
async def korean_marathon_schedule(year: int | None = None, limit: int = 10) -> dict:
    url = "https://gorunning.kr/races/"
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return {"error": f"고러닝 조회 실패 (status {resp.status_code})"}

    races = []
    # 마라톤 카드 패턴
    for m in re.finditer(r'<article[^>]*>(.*?)</article>', resp.text, re.DOTALL):
        block = m.group(1)
        title_m = re.search(r'<h\d[^>]*>([^<]+)</h\d>', block)
        date_m = re.search(r'(\d{4}[-.]\d{2}[-.]\d{2})', block)
        if title_m:
            races.append({
                "title": title_m.group(1).strip(),
                "date": date_m.group(1) if date_m else None,
            })
        if len(races) >= limit:
            break
    return {"year": year, "count": len(races), "races": races, "source": url}


# ─────────────────────────────────────
# 공연 티켓 잔여석 — YES24 / 인터파크
# ─────────────────────────────────────

@register_tool(
    name="ticket_availability",
    description="YES24 / 인터파크 공연의 등급별 잔여석을 조회합니다.",
    parameters={
        "type": "object",
        "properties": {
            "platform": {"type": "string", "enum": ["yes24", "interpark"]},
            "goods_code": {"type": "string", "description": "공연 코드 (URL 마지막 숫자)"},
        },
        "required": ["platform", "goods_code"],
    },
)
async def ticket_availability(platform: str, goods_code: str) -> dict:
    if platform == "yes24":
        url = f"https://ticket.yes24.com/Perf/{goods_code}"
    elif platform == "interpark":
        url = f"https://tickets.interpark.com/goods/{goods_code}"
    else:
        return {"error": f"지원 안 함: {platform}"}

    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return {"error": f"티켓 조회 실패 (status {resp.status_code})"}

    return {
        "platform": platform,
        "goods_code": goods_code,
        "page_url": url,
        "hint": "잔여석 정보는 JS 로 동적 로딩되므로 공식 사이트에서 확인 권장",
        "title_snippet": (re.search(r'<title>([^<]+)</title>', resp.text) or [None, ""])[1].strip()[:120],
    }
