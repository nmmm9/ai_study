"""기타 스킬 — 강남언니 / 네이버블로그 / 공중화장실 / 공시지가 / 특허 / 장학금 / 분실물.
"""

import os
import re
import json
import httpx
from urllib.parse import quote
from tools.registry import register_tool

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


# ─────────────────────────────────────
# 강남언니 — 성형/피부과 검색
# ─────────────────────────────────────

@register_tool(
    name="gangnamunni_clinic_search",
    description="강남언니에서 성형외과/피부과를 검색합니다. 평점, 리뷰 수, 진료과목 정보.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "병원명 또는 진료 키워드"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
)
async def gangnamunni_clinic_search(query: str, limit: int = 10) -> dict:
    url = f"https://www.gangnamunni.com/search?q={quote(query)}"
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return {"error": f"강남언니 조회 실패 (status {resp.status_code})"}

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
    if not m:
        return {"error": "__NEXT_DATA__ 파싱 실패"}
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return {"error": "JSON 파싱 실패"}

    hospitals = []
    try:
        props = data.get("props", {}).get("pageProps", {})
        hospitals = (props.get("hospitals") or props.get("results") or
                     props.get("searchResult", {}).get("hospitals") or [])
    except Exception:
        pass
    return {"query": query, "count": len(hospitals), "hospitals": hospitals[:limit]}


# ─────────────────────────────────────
# 네이버 블로그 검색
# ─────────────────────────────────────

@register_tool(
    name="naver_blog_search",
    description="네이버 블로그에서 키워드로 글을 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "검색 키워드"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
)
async def naver_blog_search(query: str, limit: int = 10) -> dict:
    # 네이버 검색 모바일 페이지에서 블로그 결과 추출
    url = f"https://m.search.naver.com/search.naver?where=m_blog&query={quote(query)}"
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return {"error": f"네이버 블로그 조회 실패 (status {resp.status_code})"}

    posts = []
    for m in re.finditer(r'<a[^>]*class="[^"]*total_tit[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                          resp.text, re.DOTALL):
        url2 = m.group(1)
        title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if title and url2:
            posts.append({"title": title[:120], "url": url2})
        if len(posts) >= limit:
            break
    return {"query": query, "count": len(posts), "posts": posts}


@register_tool(
    name="naver_blog_read",
    description="네이버 블로그 글 URL 의 본문을 추출합니다.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "블로그 글 URL (blog.naver.com/...)"},
        },
        "required": ["url"],
    },
)
async def naver_blog_read(url: str) -> dict:
    # mobile 버전이 더 가벼움
    mobile_url = url.replace("blog.naver.com", "m.blog.naver.com")
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": UA}, follow_redirects=True) as client:
        resp = await client.get(mobile_url)
        if resp.status_code != 200:
            return {"error": f"블로그 본문 조회 실패 (status {resp.status_code})"}

    # 본문 추출 (간이)
    body = re.sub(r'<script[^>]*>.*?</script>', '', resp.text, flags=re.DOTALL)
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    body = re.sub(r'<[^>]+>', '\n', body)
    body = re.sub(r'\n{3,}', '\n\n', body)
    title_m = re.search(r'<title>([^<]+)</title>', resp.text)
    return {
        "url": url,
        "title": title_m.group(1).strip() if title_m else "",
        "body": body.strip()[:5000],
    }


# ─────────────────────────────────────
# 공중화장실
# ─────────────────────────────────────

@register_tool(
    name="public_restroom_nearby",
    description="근처 공중화장실/개방화장실을 검색합니다. 위도/경도 또는 주소 필요.",
    parameters={
        "type": "object",
        "properties": {
            "lat": {"type": "number"},
            "lon": {"type": "number"},
            "address": {"type": "string"},
            "limit": {"type": "integer", "default": 5},
        },
    },
)
async def public_restroom_nearby(lat: float | None = None, lon: float | None = None,
                                  address: str | None = None, limit: int = 5) -> dict:
    return {
        "hint": "공중화장실 표준 데이터는 전국 CSV 파일이라 대용량입니다",
        "csv_url": "https://file.localdata.go.kr/file/download/public_restroom_info/info",
        "lat": lat, "lon": lon, "address": address,
        "guidance": "원본 SKILL.md 의 Kakao Map anchor → 지역별 CSV 절차 권장",
    }


# ─────────────────────────────────────
# 공시지가
# ─────────────────────────────────────

@register_tool(
    name="gongsijiga_search",
    description="국토교통부 개별공시지가를 조회합니다. 부동산공시가격알리미.",
    parameters={
        "type": "object",
        "properties": {
            "address": {"type": "string", "description": "주소 또는 지번"},
        },
        "required": ["address"],
    },
)
async def gongsijiga_search(address: str) -> dict:
    return {
        "address": address,
        "official_url": "https://www.realtyprice.kr/notice/gsindividual/search.htm",
        "hint": "공시지가는 npm gongsijiga-search CLI 또는 공식 사이트 조회 권장",
    }


# ─────────────────────────────────────
# 특허 — KIPRIS Plus
# ─────────────────────────────────────

@register_tool(
    name="korean_patent_search",
    description="한국 특허/실용신안을 검색합니다. KIPRIS Plus Open API. KIPRIS_API_KEY 환경변수 필요.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "발명 명칭/키워드"},
            "applicant": {"type": "string", "description": "출원인 (선택)"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
)
async def korean_patent_search(query: str, applicant: str | None = None,
                                limit: int = 10) -> dict:
    api_key = os.environ.get("KIPRIS_API_KEY")
    if not api_key:
        return {"error": "KIPRIS_API_KEY 환경변수가 필요합니다 (https://plus.kipris.or.kr)"}

    url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getWordSearch"
    params = {
        "word": query,
        "ServiceKey": api_key,
        "numOfRows": limit,
        "pageNo": 1,
    }
    if applicant:
        params["applicant"] = applicant
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        if resp.status_code == 200:
            return {"raw_xml": resp.text[:3000], "hint": "XML 응답 — 파싱 권장"}
        return {"error": f"KIPRIS 조회 실패 (status {resp.status_code})"}


# ─────────────────────────────────────
# 장학금 검색
# ─────────────────────────────────────

@register_tool(
    name="korean_scholarship_search",
    description="한국장학재단(KOSAF) + 대학 + 재단 + 기업 장학금 공고 통합 검색.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "장학금 키워드 (예: '저소득', '이공계', '예술')"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
)
async def korean_scholarship_search(query: str, limit: int = 10) -> dict:
    # KOSAF 공식 검색
    url = "https://www.kosaf.go.kr/ko/scholarShipInfo.do"
    return {
        "query": query,
        "kosaf_url": url,
        "hint": "KOSAF 검색은 JS POST 폼이라 직접 호출 어려움. 공식 사이트 또는 SKILL.md 의 multi-source 가이드 권장",
    }


# ─────────────────────────────────────
# 지하철 분실물 — LOST112 + 서울교통공사
# ─────────────────────────────────────

@register_tool(
    name="subway_lost_property",
    description="지하철/대중교통 분실물(유실물)을 LOST112 에서 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "item_name": {"type": "string", "description": "물품명 (예: '지갑', '핸드폰')"},
            "station": {"type": "string", "description": "역명 (선택)"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["item_name"],
    },
)
async def subway_lost_property(item_name: str, station: str | None = None,
                                limit: int = 10) -> dict:
    url = "https://www.lost112.go.kr/find/findList.do"
    headers = {"User-Agent": UA, "Origin": "https://www.lost112.go.kr",
               "Referer": "https://www.lost112.go.kr/find/findFreList.do"}
    payload = {
        "PRDT_NM": item_name,
        "FD_PLACE": station or "",
        "pageNum": 1,
        "PAGE_NUM": limit,
    }
    async with httpx.AsyncClient(timeout=15, headers=headers, follow_redirects=True) as client:
        resp = await client.post(url, data=payload)
        if resp.status_code != 200:
            return {"error": f"분실물 조회 실패 (status {resp.status_code})"}

    items = []
    for m in re.finditer(r'<tr[^>]*>\s*<td[^>]*>(\d+)</td>.*?<td[^>]*>([^<]+)</td>.*?<td[^>]*>([^<]+)</td>',
                          resp.text, re.DOTALL):
        items.append({
            "no": m.group(1),
            "field2": m.group(2).strip()[:80],
            "field3": m.group(3).strip()[:80],
        })
        if len(items) >= limit:
            break
    return {"item_name": item_name, "station": station,
            "count": len(items), "items": items, "source": url}
