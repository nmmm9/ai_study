"""
policy_loader.py
────────────────
week02 / week04 데이터의 마크다운 정책 문서를 로드하고 키워드 검색합니다.
벡터 DB 없이 단순 텍스트 매칭으로 검색합니다.
"""

import os
import re
from pathlib import Path

# ── 데이터 경로 ──────────────────────────────────────────────────
_HERE = Path(__file__).parent.parent  # week09-langgraph/minseon/
_ROOTS = [
    _HERE / ".." / ".." / "week04-rag-pipeline" / "minseon" / "data",
    _HERE / ".." / ".." / "week02-chunking" / "minseon" / "data" / "scholarships",
    _HERE / ".." / ".." / "week02-chunking" / "minseon" / "data" / "youth_policies",
]

# ── 카테고리별 키워드 매핑 ───────────────────────────────────────
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "장학금": ["장학금", "학자금", "등록금", "장학", "교육비", "대학생", "교육지원"],
    "취업":   ["취업", "일자리", "고용", "채용", "근로", "직업", "인턴", "일경험", "취준"],
    "주거":   ["주거", "월세", "전세", "임대", "청약", "주택", "기숙사", "집"],
    "금융":   ["적금", "계좌", "저축", "금융", "도약", "희망", "대출", "지원금"],
    "복지":   ["복지", "지원", "바우처", "혜택", "수당", "급여"],
}

_doc_cache: list[dict] | None = None


def _load_all_docs() -> list[dict]:
    """모든 정책 마크다운 파일을 로드합니다. (캐시 적용)"""
    global _doc_cache
    if _doc_cache is not None:
        return _doc_cache

    docs = []
    seen_titles = set()

    for root in _ROOTS:
        root = root.resolve()
        if not root.exists():
            continue
        for md_file in root.glob("*.md"):
            if md_file.name == "policy_relations.md":
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
                title   = _extract_title(content, md_file.stem)
                if title in seen_titles:
                    continue
                seen_titles.add(title)
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
    """마크다운에서 첫 번째 # 제목을 추출합니다."""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return fallback.replace("_", " ")


def _detect_category(content: str) -> str:
    """문서 내용으로 카테고리를 감지합니다."""
    content_lower = content.lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            scores[cat] += content_lower.count(kw)
    return max(scores, key=lambda c: scores[c])


def search_policies(
    keywords: list[str],
    category: str = "",
    top_k: int = 5,
) -> list[dict]:
    """키워드와 카테고리로 정책 문서를 검색합니다.

    Args:
        keywords: 검색 키워드 목록
        category: 카테고리 필터 (비어있으면 전체)
        top_k:    반환할 최대 문서 수

    Returns:
        [{"title", "content", "source", "category", "score"}, ...]
    """
    docs = _load_all_docs()
    scored = []

    for doc in docs:
        # 카테고리 필터
        if category and doc["category"] != category:
            continue

        # 키워드 스코어 계산
        text  = (doc["title"] + " " + doc["content"]).lower()
        score = sum(text.count(kw.lower()) for kw in keywords if kw)
        if score > 0:
            scored.append({**doc, "score": score})

    # 스코어 내림차순 정렬
    scored.sort(key=lambda d: d["score"], reverse=True)
    return scored[:top_k]


def search_all_policies(keywords: list[str], top_k: int = 5) -> list[dict]:
    """카테고리 필터 없이 전체 검색합니다."""
    return search_policies(keywords=keywords, category="", top_k=top_k)


def get_all_policy_titles() -> list[str]:
    """전체 정책 제목 목록을 반환합니다."""
    return [d["title"] for d in _load_all_docs()]


def get_policy_count() -> int:
    return len(_load_all_docs())
