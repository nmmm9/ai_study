"""
policy_loader.py
────────────────
week10 policy_loader 재사용 (경로만 week11 기준으로 조정)
"""

from pathlib import Path

_HERE  = Path(__file__).parent.parent
_ROOTS = [
    (_HERE / "data").resolve(),
    (_HERE / "data" / "scholarships").resolve(),
    (_HERE / "data" / "youth_policies").resolve(),
    (_HERE / "data" / "youthcenter").resolve(),   # 온통청년 수집 데이터
]

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "장학금": ["장학금", "학자금", "등록금", "장학", "교육비", "대학생"],
    "취업":   ["취업", "일자리", "고용", "채용", "근로", "인턴", "취준"],
    "주거":   ["주거", "월세", "전세", "임대", "청약", "주택"],
    "금융":   ["적금", "계좌", "저축", "금융", "도약", "희망", "대출"],
    "복지":   ["복지", "지원", "바우처", "수당"],
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
            if md_file.name == "policy_relations.md":
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
                    "category": _detect_category(content),
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


def _detect_category(content: str) -> str:
    lower  = content.lower()
    scores = {cat: sum(lower.count(kw) for kw in kws)
              for cat, kws in CATEGORY_KEYWORDS.items()}
    return max(scores, key=lambda c: scores[c])


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
