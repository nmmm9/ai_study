"""
policy_loader.py
────────────────
정책 문서 로드 + 검색

검색 우선순위:
  1순위 — RAG (시맨틱 검색): vector_store.json이 있을 때
  2순위 — 키워드 매칭: 벡터 스토어가 없거나 결과가 0개일 때

처음 실행 전 벡터 스토어 빌드 필요:
  Streamlit 사이드바 → "벡터 DB 빌드" 버튼
  또는: from tools.embedder import build_vector_store; build_vector_store(get_all_docs())
"""

from pathlib import Path

# ── 데이터 경로 ──────────────────────────────────────────────────
_HERE  = Path(__file__).parent.parent          # week10-notification/minseon/
_ROOTS = [
    (_HERE / ".." / ".." / "week04-rag-pipeline" / "minseon" / "data").resolve(),
    (_HERE / ".." / ".." / "week02-chunking" / "minseon" / "data" / "scholarships").resolve(),
    (_HERE / ".." / ".." / "week02-chunking" / "minseon" / "data" / "youth_policies").resolve(),
]

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "장학금": ["장학금", "학자금", "등록금", "장학", "교육비", "대학생", "교육지원"],
    "취업":   ["취업", "일자리", "고용", "채용", "근로", "직업", "인턴", "일경험", "취준"],
    "주거":   ["주거", "월세", "전세", "임대", "청약", "주택", "기숙사"],
    "금융":   ["적금", "계좌", "저축", "금융", "도약", "희망", "대출", "지원금"],
    "복지":   ["복지", "지원", "바우처", "혜택", "수당", "급여"],
}

_doc_cache: list[dict] | None = None


# ── 문서 로드 ────────────────────────────────────────────────────

def _load_all_docs() -> list[dict]:
    global _doc_cache
    if _doc_cache is not None:
        return _doc_cache

    docs: list[dict] = []
    seen: set[str]   = set()

    # 1. 로컬 MD 파일 (week02/week04)
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

    # 2. 공공데이터포털 API로 수집된 문서 (tools/data/fetched/)
    try:
        from tools.policy_fetcher import get_fetched_docs
        for doc in get_fetched_docs():
            if doc["title"] not in seen:
                seen.add(doc["title"])
                docs.append(doc)
    except Exception:
        pass

    # 3. Tavily 웹 검색으로 수집된 문서 (tools/data/web/)
    try:
        from tools.web_searcher import get_web_docs
        for doc in get_web_docs():
            if doc["title"] not in seen:
                seen.add(doc["title"])
                docs.append(doc)
    except Exception:
        pass

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


# ── 키워드 검색 (폴백) ───────────────────────────────────────────

def _keyword_search(
    keywords: list[str],
    category: str = "",
    top_k: int = 5,
) -> list[dict]:
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


# ── 메인 검색 함수 (RAG 우선) ────────────────────────────────────

def search_policies(
    keywords: list[str],
    category: str = "",
    top_k: int = 5,
) -> list[dict]:
    """
    RAG(시맨틱 검색)를 우선 시도하고, 실패 시 키워드 매칭으로 폴백.

    RAG 사용 조건: vector_store.json이 존재할 때
    """
    from tools.embedder import is_store_built, semantic_search

    if is_store_built():
        query   = " ".join(keywords)
        results = semantic_search(query, top_k=top_k * 2)

        # 카테고리 필터 적용
        if category:
            results = [r for r in results if r.get("category") == category]

        results = results[:top_k]

        if results:
            mode = "RAG"
            print(f"[policy_loader] {mode} 검색 — {len(results)}개 반환 "
                  f"(상위 score: {results[0]['score']:.3f})")
            return results

    # 폴백: 키워드 매칭
    results = _keyword_search(keywords, category, top_k)
    print(f"[policy_loader] 키워드 검색 — {len(results)}개 반환")
    return results


def search_all_policies(keywords: list[str], top_k: int = 5) -> list[dict]:
    """카테고리 필터 없이 전체 검색."""
    return search_policies(keywords=keywords, category="", top_k=top_k)


# ── 유틸 ────────────────────────────────────────────────────────

def get_all_docs() -> list[dict]:
    return _load_all_docs()

def get_all_policy_titles() -> list[str]:
    return [d["title"] for d in _load_all_docs()]

def get_policy_count() -> int:
    return len(_load_all_docs())
