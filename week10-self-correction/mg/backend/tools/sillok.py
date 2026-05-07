"""조선왕조실록 검색 — sillok.history.go.kr.

k-skills 원본: POST 방식으로 topSearchWord, type, sillokType 파라미터를 사용.
검색 결과에서 goView('<article_id>', N) 패턴으로 기사 ID를 추출.
상세 페이지는 view-item left/right 에서 국역/원문을 파싱.
"""

import html as html_module
import httpx
import re
from tools.registry import register_tool

BASE_URL = "https://sillok.history.go.kr"
SEARCH_URL = f"{BASE_URL}/search/searchResultList.do"
DETAIL_URL = f"{BASE_URL}/id/"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/main/main.do",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}


def _clean(text: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_module.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


@register_tool(
    name="joseon_sillok_search",
    description="조선왕조실록에서 키워드로 역사 기록을 검색합니다. 왕 이름이나 사건으로 검색 가능합니다.",
    parameters={
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "검색 키워드 (예: 세종, 훈민정음, 임진왜란)"},
            "king": {"type": "string", "description": "특정 왕 이름으로 필터 (선택)"},
            "doc_type": {"type": "string", "enum": ["k", "w"], "description": "k=국역(한글), w=원문(한문)", "default": "k"},
        },
        "required": ["keyword"],
    },
)
async def joseon_sillok_search(keyword: str, king: str = None, doc_type: str = "k") -> dict:
    # k-skills 원본: POST with form data
    form_data = {
        "topSearchWord": keyword,
        "pageIndex": "1",
        "initPageUnit": "0",
        "type": doc_type,
        "sillokType": "S",
        "topSearchWord_ime": f'<span class="newbatang">{html_module.escape(keyword)}</span>',
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(SEARCH_URL, data=form_data, headers=HEADERS)
        if resp.status_code != 200:
            return {"error": "실록 검색 실패"}

        # k-skills 원본: goView('<article_id>', N) 패턴과 subject, text 파싱
        result_pattern = re.compile(
            r"<a\s+href=\"javascript:goView\('([^']+)',\s*\d+\);\"\s+class=\"subject\">(.*?)</a>\s*"
            r"<p\s+class=\"text\">(.*?)</p>",
            re.S,
        )
        matches = result_pattern.findall(resp.text)

        results = []
        for article_id, subject_html, summary_html in matches[:5]:
            title = _clean(subject_html)
            title = re.sub(r"^\d+\.\s*", "", title)
            summary = _clean(summary_html)

            if king and king not in title:
                continue

            # 상세 페이지에서 국역 excerpt 추출
            snippet = summary[:300]
            try:
                detail_resp = await client.get(
                    f"{DETAIL_URL}{article_id}",
                    headers={**HEADERS, "Referer": SEARCH_URL},
                )
                if detail_resp.status_code == 200:
                    # k-skills 원본: view-item left 에서 국역 텍스트
                    left_match = re.search(
                        r'<div\s+class="view-item\s+left">.*?<div\s+class="view-text">(.*?)</div>',
                        detail_resp.text,
                        re.S,
                    )
                    if left_match:
                        excerpt = _clean(left_match.group(1))
                        if excerpt:
                            snippet = excerpt[:300]
            except Exception:
                pass

            results.append({
                "title": title,
                "id": article_id,
                "url": f"{DETAIL_URL}{article_id}",
                "snippet": snippet,
            })

        return {"keyword": keyword, "count": len(results), "results": results}
