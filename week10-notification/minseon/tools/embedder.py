"""
embedder.py
───────────
OpenAI text-embedding-3-small 기반 RAG 엔진

[처음 실행 시]
  정책 문서 로드 → 단락 단위 청킹 → 임베딩 생성 → vector_store.json 저장

[이후 실행 시]
  vector_store.json 로드 → 질문 임베딩 → 코사인 유사도 계산 → 유사 청크 반환

벡터 DB로 FAISS 대신 numpy를 사용합니다.
(정책 문서 수가 수십~수백 개 수준이라 numpy로 충분)
"""

import json
import os
from pathlib import Path

import numpy as np
from openai import OpenAI

CACHE_PATH  = Path(__file__).parent / "vector_store.json"
EMBED_MODEL = "text-embedding-3-small"   # 1536차원, 저렴하고 빠름
CHUNK_SIZE  = 600                         # 청크 최대 글자 수

_client: OpenAI | None = None
_store:  dict   | None = None            # 메모리 캐시


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


# ── 청킹 ────────────────────────────────────────────────────────

def _chunk_doc(doc: dict) -> list[dict]:
    """
    마크다운 문서를 단락(\n\n) 기준으로 분할합니다.
    CHUNK_SIZE를 넘으면 강제 분할합니다.
    """
    paragraphs = [p.strip() for p in doc["content"].split("\n\n") if p.strip()]
    chunks  = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= CHUNK_SIZE:
            current += para + "\n\n"
        else:
            if current.strip():
                chunks.append(_make_chunk(doc, current.strip()))
            current = para + "\n\n"

    if current.strip():
        chunks.append(_make_chunk(doc, current.strip()))

    return chunks if chunks else [_make_chunk(doc, doc["content"][:CHUNK_SIZE])]


def _make_chunk(doc: dict, content: str) -> dict:
    return {
        "title":    doc["title"],
        "source":   doc["source"],
        "category": doc["category"],
        "content":  content,
    }


# ── 임베딩 ──────────────────────────────────────────────────────

def _embed_batch(texts: list[str], batch_size: int = 50) -> list[list[float]]:
    """OpenAI API 호출 (배치 처리)."""
    client = _get_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch    = texts[i : i + batch_size]
        response = client.embeddings.create(model=EMBED_MODEL, input=batch)
        all_embeddings.extend(item.embedding for item in response.data)

    return all_embeddings


# ── 벡터 스토어 빌드 ────────────────────────────────────────────

def build_vector_store(docs: list[dict]) -> None:
    """
    정책 문서 전체를 임베딩하여 CACHE_PATH에 저장합니다.
    이미 저장된 경우에도 강제로 재빌드합니다.
    """
    global _store

    # 1. 청킹
    all_chunks: list[dict] = []
    for doc in docs:
        all_chunks.extend(_chunk_doc(doc))
    print(f"[embedder] {len(docs)}개 문서 → {len(all_chunks)}개 청크")

    # 2. 임베딩 텍스트: 제목 + 본문 (검색 품질 향상)
    texts = [f"{c['title']}\n{c['content']}" for c in all_chunks]
    print(f"[embedder] OpenAI 임베딩 생성 중... ({EMBED_MODEL})")
    embeddings = _embed_batch(texts)

    # 3. 저장
    store = {"chunks": all_chunks, "embeddings": embeddings}
    CACHE_PATH.write_text(
        json.dumps(store, ensure_ascii=False, indent=None),
        encoding="utf-8",
    )
    _store = None  # 메모리 캐시 초기화 (다음 검색 시 다시 로드)
    print(f"[embedder] 벡터 스토어 저장 완료 → {CACHE_PATH.name}")


# ── 벡터 스토어 로드 ────────────────────────────────────────────

def _load_store() -> dict:
    global _store
    if _store is not None:
        return _store

    if not CACHE_PATH.exists():
        return {"chunks": [], "embeddings": np.empty((0, 0), dtype=np.float32)}

    raw = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    _store = {
        "chunks":     raw["chunks"],
        "embeddings": np.array(raw["embeddings"], dtype=np.float32),
    }
    return _store


def is_store_built() -> bool:
    return CACHE_PATH.exists()


# ── 시맨틱 검색 ─────────────────────────────────────────────────

def semantic_search(query: str, top_k: int = 5) -> list[dict]:
    """
    질문과 의미적으로 가장 유사한 정책 청크를 반환합니다.

    Returns:
        [{"title", "source", "category", "content", "score"}, ...]
        score: 0~1 사이의 코사인 유사도 (높을수록 유사)
    """
    store = _load_store()
    if len(store["chunks"]) == 0:
        return []

    # 질문 임베딩
    client    = _get_client()
    resp      = client.embeddings.create(model=EMBED_MODEL, input=[query])
    query_emb = np.array(resp.data[0].embedding, dtype=np.float32)

    # 코사인 유사도: 내적 / (|a| * |b|)
    embs = store["embeddings"]                              # (N, D)
    q_norm   = query_emb / (np.linalg.norm(query_emb) + 1e-10)
    e_norms  = embs / (np.linalg.norm(embs, axis=1, keepdims=True) + 1e-10)
    scores   = e_norms @ q_norm                             # (N,)

    # 상위 top_k * 2개 후보 중 문서 중복 제거
    candidate_idx = np.argsort(scores)[::-1][: top_k * 3]

    results: list[dict] = []
    seen_titles: set[str] = set()

    for idx in candidate_idx:
        chunk = store["chunks"][idx]
        title = chunk["title"]
        if title in seen_titles:
            continue
        seen_titles.add(title)
        results.append({**chunk, "score": float(scores[idx])})
        if len(results) >= top_k:
            break

    return results


def get_store_stats() -> dict:
    """벡터 스토어 현황 반환."""
    if not is_store_built():
        return {"built": False}
    store = _load_store()
    return {
        "built":       True,
        "chunk_count": len(store["chunks"]),
        "doc_count":   len({c["title"] for c in store["chunks"]}),
        "file_size_kb": round(CACHE_PATH.stat().st_size / 1024, 1),
    }
