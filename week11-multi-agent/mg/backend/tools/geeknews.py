"""긱뉴스 검색 — feeds.feedburner.com/geeknews-feed (RSS)."""

import re
import httpx
from xml.etree import ElementTree as ET
from tools.registry import register_tool

FEED_URL = "https://feeds.feedburner.com/geeknews-feed"


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


async def _fetch_feed() -> list[dict]:
    async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
        resp = await client.get(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return []
        root = ET.fromstring(resp.text)

    items = []
    # RSS 2.0
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = _strip_html(item.findtext("description") or "")
        pub = (item.findtext("pubDate") or "").strip()
        creator_tag = item.find("{http://purl.org/dc/elements/1.1/}creator")
        author = (creator_tag.text or "").strip() if creator_tag is not None else ""
        items.append({
            "title": title,
            "link": link,
            "summary": desc[:500],
            "published": pub,
            "author": author,
        })

    return items


@register_tool(
    name="geeknews_search",
    description="긱뉴스(news.hada.io) 최신 글 또는 키워드로 검색합니다.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "검색 키워드 (없으면 최신 목록)"},
            "limit": {"type": "integer", "default": 10},
        },
    },
)
async def geeknews_search(query: str | None = None, limit: int = 10) -> dict:
    items = await _fetch_feed()
    if not items:
        return {"error": "긱뉴스 피드를 가져오지 못했습니다"}

    if query:
        q = query.lower()
        items = [
            it for it in items
            if q in it["title"].lower()
            or q in it["summary"].lower()
            or q in it["author"].lower()
        ]

    return {"query": query, "count": len(items), "items": items[:limit]}
