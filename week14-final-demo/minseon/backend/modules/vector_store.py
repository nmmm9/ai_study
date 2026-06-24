"""
vector_store.py — ChromaDB 벡터 저장소 (Modular RAG)

database/chroma_db/ 에 정책 문서 임베딩을 저장·검색합니다.
build_index.py 로 먼저 인덱스를 빌드해야 사용 가능합니다.
"""

import chromadb
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent.parent / "database" / "chroma_db"

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(_DB_PATH))
        _collection = _client.get_or_create_collection(
            name="policies",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def is_built() -> bool:
    return _get_collection().count() > 0


def count() -> int:
    return _get_collection().count()


def search_vector(query_embedding: list[float], top_k: int = 5, category: str = "") -> list[dict]:
    col = _get_collection()
    where = {"category": category} if category else None

    results = col.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, col.count()),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    docs = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        docs.append({
            "title":    meta["title"],
            "content":  doc,
            "category": meta["category"],
            "score":    round(1 - dist, 4),
        })
    return docs


def add_documents(
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict],
) -> None:
    _get_collection().add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
