"""한국어 신조어/유행어 사전 — 로컬 데이터셋 lookup.

k-skills/korean-slang-writing/data/seed-slang.json 에서 직접 읽음.
"""

import json
import os
from functools import lru_cache
from tools.registry import register_tool

# Find seed-slang.json relative to project root
_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [
    os.path.join(_HERE, "..", "..", "..", "..", "k-skills", "korean-slang-writing", "data", "seed-slang.json"),
    os.path.join(_HERE, "..", "data", "seed-slang.json"),
]


@lru_cache(maxsize=1)
def _load_slang() -> list[dict]:
    for path in _CANDIDATES:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("entries", [])
    return []


@register_tool(
    name="korean_slang_lookup",
    description="한국어 신조어/유행어의 의미, 사용 맥락, 예시를 조회합니다 (예: 중꺾마, 갓생, 인싸).",
    parameters={
        "type": "object",
        "properties": {
            "term": {"type": "string", "description": "검색할 신조어/유행어"},
            "limit": {"type": "integer", "default": 5},
        },
        "required": ["term"],
    },
)
async def korean_slang_lookup(term: str, limit: int = 5) -> dict:
    entries = _load_slang()
    if not entries:
        return {"error": "신조어 사전 데이터를 찾을 수 없습니다 (k-skills/korean-slang-writing/data/seed-slang.json)"}

    q = term.strip().lower()
    matched = []
    for e in entries:
        haystack = [e.get("term", "")]
        haystack.extend(e.get("aliases", []) or [])
        haystack.append(e.get("meaning_short", ""))
        if any(q in (h or "").lower() for h in haystack):
            matched.append({
                "term": e.get("term"),
                "aliases": e.get("aliases", []),
                "meaning": e.get("meaning_short"),
                "usage_context": e.get("usage_context", []),
                "mood_tags": e.get("mood_tags", []),
                "examples": e.get("example_usage", []),
                "era": e.get("era"),
                "still_usable": e.get("still_usable"),
            })
            if len(matched) >= limit:
                break

    return {
        "query": term,
        "count": len(matched),
        "results": matched,
        "total_dict_size": len(entries),
    }
