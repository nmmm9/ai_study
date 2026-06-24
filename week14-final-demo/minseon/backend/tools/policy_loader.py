"""
policy_loader.py — 정책 문서 로더 (DATABASE 계층)

database/data 폴더의 627개 .md 파일을 읽어 메모리에 캐싱합니다.
10개 카테고리로 분류: 일자리/진로/창업/주거/금융/교육/마음건강/신체건강/문화예술/생활지원
"""

from pathlib import Path

_HERE  = Path(__file__).parent.parent.parent           # minseon/
_DATA  = _HERE / "database" / "data"

_ROOTS = [
    (_DATA).resolve(),
    (_DATA / "scholarships").resolve(),
    (_DATA / "youth_policies").resolve(),
    (_DATA / "youthcenter").resolve(),
]

CATEGORY_TITLE_KEYWORDS: dict[str, list[str]] = {
    "일자리":    ["취업", "일자리", "채용", "구직", "인턴", "면접", "고용", "취준"],
    "진로":      ["진로", "자격증", "직업훈련", "일경험", "직무", "역량강화", "NCS"],
    "창업":      ["창업", "스타트업", "벤처", "창업공간", "창업몰"],
    "주거":      ["월세", "전세", "임대", "청약", "주택", "주거"],
    "금융":      ["적금", "도약계좌", "희망적금", "이차보전", "대출", "저축계좌", "금융지원", "청년통장"],
    "교육":      ["장학금", "학자금", "등록금", "근로장학", "장학재단", "교육비"],
    "마음건강":  ["심리", "마음건강", "정신건강", "상담", "트라우마", "우울", "정신"],
    "신체건강":  ["신체", "건강검진", "의료비", "체육시설", "스포츠"],
    "문화/예술": ["문화", "도서", "예술", "여가", "공연", "전시", "영화", "관람"],
    "생활지원":  [],  # catch-all
}

CATEGORY_EMOJI: dict[str, str] = {
    "일자리":    "💼",
    "진로":      "🎯",
    "창업":      "💡",
    "주거":      "🏠",
    "금융":      "💰",
    "교육":      "🎓",
    "마음건강":  "❤️",
    "신체건강":  "🏃",
    "문화/예술": "🎨",
    "생활지원":  "🤲",
}

_doc_cache: list[dict] | None = None


def _load_all_docs() -> list[dict]:
    global _doc_cache
    if _doc_cache is not None:
        return _doc_cache

    docs: list[dict] = []
    seen: set[str]   = set()

    for root in _ROOTS:
        if not root.exists():
            continue
        for md_file in sorted(root.glob("*.md")):
            if md_file.name in ("policy_relations.md",):
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
                title   = _extract_title(content, md_file.stem)
                if title in seen:
                    continue
                seen.add(title)
                docs.append({
                    "title":    title,
                    "content":  content,
                    "source":   md_file.name,
                    "category": _detect_category(title, content),
                })
            except Exception:
                continue

    _doc_cache = docs
    return docs


def _extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return fallback.replace("_", " ")


def _detect_category(title: str, content: str) -> str:
    """제목 우선 → 내용 순으로 카테고리 판별."""
    title_lower = title.lower()
    snippet     = content.lower()[:500]

    for cat, keywords in CATEGORY_TITLE_KEYWORDS.items():
        if keywords and any(kw in title_lower for kw in keywords):
            return cat

    for cat, keywords in CATEGORY_TITLE_KEYWORDS.items():
        if keywords and any(kw in snippet for kw in keywords):
            return cat

    return "생활지원"


def get_category_stats() -> dict[str, int]:
    docs = _load_all_docs()
    stats: dict[str, int] = {}
    for d in docs:
        stats[d["category"]] = stats.get(d["category"], 0) + 1
    return stats


def get_policies_by_category(category: str, top_k: int = 30) -> list[dict]:
    return [d for d in _load_all_docs() if d["category"] == category][:top_k]


def search_policies(keywords: list[str], category: str = "", top_k: int = 5) -> list[dict]:
    docs   = _load_all_docs()
    scored = []
    for doc in docs:
        if category and doc["category"] != category:
            continue
        text  = (doc["title"] + " " + doc["content"]).lower()
        score = sum(text.count(kw.lower()) for kw in keywords if kw)
        if score > 0:
            scored.append({**doc, "score": score})
    scored.sort(key=lambda d: d["score"], reverse=True)
    return scored[:top_k]


def search_all_policies(keywords: list[str], top_k: int = 5) -> list[dict]:
    return search_policies(keywords=keywords, category="", top_k=top_k)


def get_all_policy_titles() -> list[str]:
    return [d["title"] for d in _load_all_docs()]


def get_policy_by_id(policy_id: str) -> list[dict]:
    """source 파일명 또는 정책 제목으로 특정 정책을 조회합니다."""
    docs = _load_all_docs()
    pid  = policy_id.lower().replace(".md", "")

    for doc in docs:
        if doc["source"].lower().replace(".md", "") == pid:
            return [doc]

    for doc in docs:
        if pid in doc["title"].lower():
            return [doc]

    return []
