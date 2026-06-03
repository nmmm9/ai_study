"""
policy_loader.py
────────────────
week11 policy_loader 재사용 (경로만 week12 기준으로 조정)
week11 data 폴더를 심볼릭 링크 또는 복사해서 사용하거나
WEEK11_DATA 환경변수로 경로를 지정할 수 있습니다.
"""

import os
from pathlib import Path

_HERE = Path(__file__).parent.parent

# week11 data를 그대로 참조 (같은 프로젝트 내)
_WEEK11 = _HERE.parent.parent / "week11-multi-agent" / "minseon"

_ROOTS = [
    (_HERE / "data").resolve(),                              # week12 자체 data (있으면)
    (_WEEK11 / "data").resolve(),                            # week11 data 공유
    (_WEEK11 / "data" / "scholarships").resolve(),
    (_WEEK11 / "data" / "youth_policies").resolve(),
    (_WEEK11 / "data" / "youthcenter").resolve(),
]

# 순서가 중요: 제목에서 먼저 매칭, 구체적인 카테고리 → 일반 카테고리 순
CATEGORY_TITLE_KEYWORDS: dict[str, list[str]] = {
    "장학금":   ["장학금", "학자금", "등록금", "근로장학", "장학재단"],
    "금융":     ["적금", "도약계좌", "희망적금", "이차보전", "대출", "저축계좌", "금융지원", "청년통장"],
    "주거":     ["월세", "전세", "임대", "청약", "주택", "주거"],
    "취업":     ["취업", "일자리", "채용", "구직", "인턴", "면접", "자격증", "직업훈련", "일경험", "고용", "취준"],
    "창업":     ["창업", "스타트업", "벤처", "창업공간", "창업몰"],
    "건강문화": ["건강", "심리", "마음건강", "의료", "문화", "도서", "예술", "체육", "여가"],
    "참여":     ["참여", "네트워크", "위원회", "협의체", "위촉", "청년단", "청년위원", "포럼", "자치경찰"],
    "복지":     [],  # catch-all
}

# UI 표시용 이모지 매핑
CATEGORY_EMOJI: dict[str, str] = {
    "장학금":   "📚",
    "금융":     "💰",
    "주거":     "🏠",
    "취업":     "💼",
    "창업":     "🚀",
    "건강문화": "🎭",
    "참여":     "🤝",
    "복지":     "🤲",
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
    title_lower   = title.lower()
    content_lower = content.lower()

    # 1차: 제목에서 키워드 매칭 (가장 신뢰도 높음)
    for cat, keywords in CATEGORY_TITLE_KEYWORDS.items():
        if keywords and any(kw in title_lower for kw in keywords):
            return cat

    # 2차: 본문 첫 500자에서 키워드 매칭
    snippet = content_lower[:500]
    for cat, keywords in CATEGORY_TITLE_KEYWORDS.items():
        if keywords and any(kw in snippet for kw in keywords):
            return cat

    return "복지"


def get_category_stats() -> dict[str, int]:
    """카테고리별 정책 수 반환."""
    docs = _load_all_docs()
    stats: dict[str, int] = {}
    for d in docs:
        stats[d["category"]] = stats.get(d["category"], 0) + 1
    return stats


def get_policies_by_category(category: str, top_k: int = 10) -> list[dict]:
    """특정 카테고리의 정책 목록 반환."""
    docs = _load_all_docs()
    result = [d for d in docs if d["category"] == category]
    return result[:top_k]


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
