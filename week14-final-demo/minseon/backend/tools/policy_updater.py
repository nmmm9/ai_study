"""
policy_updater.py — 실시간 정책 수집 → ChromaDB 업데이트

스케줄러에서 매일 8시에 호출됩니다.
  1. 온통청년 API (API 키 불필요) 에서 최신 정책 수집
  2. 공공데이터포털 API (API 키 필요) 에서 수집
  3. 이미 있는 정책은 스킵, 새 정책만 ChromaDB에 추가
"""

import re
from pathlib import Path
from datetime import datetime

_FETCHED_DIR = Path(__file__).parent.parent.parent / "database" / "data" / "fetched"
_FETCHED_DIR.mkdir(parents=True, exist_ok=True)


def _safe_name(title: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "", title)[:40]


def _embed_and_add(docs: list[dict]) -> int:
    """새 문서 임베딩 후 ChromaDB에 추가. 추가된 개수 반환."""
    if not docs:
        return 0

    from backend.modules.embedder import embed_texts
    from backend.modules.vector_store import add_documents, count as db_count

    base_id    = db_count()
    batch_size = 20
    added      = 0

    for i in range(0, len(docs), batch_size):
        batch      = docs[i : i + batch_size]
        texts      = [f"{d['title']}\n{d['content'][:800]}" for d in batch]
        embeddings = embed_texts(texts)

        add_documents(
            ids       = [f"doc_{base_id + added + j}" for j in range(len(batch))],
            embeddings= embeddings,
            documents = [d["content"][:1500] for d in batch],
            metadatas = [{"title": d["title"], "category": d["category"]} for d in batch],
        )
        added += len(batch)

    return added


def _is_new(title: str) -> bool:
    """같은 제목의 MD 파일이 없으면 신규 정책으로 판단."""
    return not (_FETCHED_DIR / f"{_safe_name(title)}.md").exists()


def _save_md(doc: dict) -> None:
    path = _FETCHED_DIR / f"{_safe_name(doc['title'])}.md"
    path.write_text(doc["content"], encoding="utf-8")


# ── 온통청년 API (API 키 불필요) ──────────────────────────────────

def update_from_youthcenter(max_count: int = 200) -> list[dict]:
    from backend.tools.youthcenter_crawler import fetch_policies, save_as_docs

    print("[updater] 온통청년 API 수집 중...")
    raw      = fetch_policies(query="청년", max_count=max_count)
    all_docs = save_as_docs(raw)

    new_docs = [d for d in all_docs if _is_new(d["title"])]
    for d in new_docs:
        _save_md(d)

    added = _embed_and_add(new_docs)
    print(f"[updater] 온통청년: 신규 {added}개 추가 / 전체 {len(all_docs)}개")
    return new_docs


# ── 공공데이터포털 API ────────────────────────────────────────────

def update_from_public_api(max_count: int = 200) -> list[dict]:
    from backend.tools.policy_fetcher import fetch_and_save, has_api_key

    if not has_api_key():
        print("[updater] PUBLIC_DATA_API_KEY 없음 — 공공API 건너뜀")
        return []

    print("[updater] 공공데이터포털 API 수집 중...")
    all_docs = fetch_and_save(max_count=max_count)

    new_docs = [d for d in all_docs if _is_new(d["title"])]
    added    = _embed_and_add(new_docs)
    print(f"[updater] 공공API: 신규 {added}개 추가 / 전체 {len(all_docs)}개")
    return new_docs


# ── 통합 업데이트 (스케줄러 진입점) ─────────────────────────────

async def run_daily_update() -> list[dict]:
    """매일 8시에 실행. 신규 정책 목록 반환."""
    print(f"\n[updater] === 일일 업데이트 시작 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    new_docs: list[dict] = []

    try:
        new_docs += update_from_youthcenter(max_count=200)
    except Exception as e:
        print(f"[updater] 온통청년 오류: {e}")

    try:
        new_docs += update_from_public_api(max_count=200)
    except Exception as e:
        print(f"[updater] 공공API 오류: {e}")

    print(f"[updater] === 완료: 신규 {len(new_docs)}개 ===\n")
    return new_docs
