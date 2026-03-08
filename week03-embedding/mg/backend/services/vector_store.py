import time
from dataclasses import dataclass
from pathlib import Path

import chromadb

_PERSIST_DIR = str(Path(__file__).resolve().parent.parent / "chroma_data")
_client = chromadb.PersistentClient(path=_PERSIST_DIR)


@dataclass
class VectorSearchResult:
    index: int
    text: str
    score: float


def create_collection(name: str) -> chromadb.Collection:
    return _client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(
    collection_name: str,
    texts: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict] | None = None,
) -> int:
    """Add chunks to a collection. Returns store_time_ms."""
    start = time.perf_counter()
    collection = create_collection(collection_name)
    ids = [f"chunk-{i}" for i in range(len(texts))]
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas or [{"index": i} for i in range(len(texts))],
    )
    return int((time.perf_counter() - start) * 1000)


def search(
    collection_name: str,
    query_embedding: list[float],
    top_k: int = 3,
) -> tuple[list[VectorSearchResult], int]:
    """Search a collection. Returns (results, search_time_ms)."""
    start = time.perf_counter()
    collection = _client.get_collection(collection_name)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "distances", "metadatas"],
    )
    search_time_ms = int((time.perf_counter() - start) * 1000)

    scored = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]
        score = 1.0 - distance  # cosine distance -> similarity
        idx = results["metadatas"][0][i].get("index", i)
        scored.append(
            VectorSearchResult(
                index=idx,
                text=results["documents"][0][i],
                score=score,
            )
        )
    return scored, search_time_ms


def collection_exists(name: str) -> bool:
    """Check if a collection exists and has data."""
    try:
        col = _client.get_collection(name)
        return col.count() > 0
    except Exception:
        return False


def list_collections() -> list[dict]:
    """List all collections with their count."""
    cols = _client.list_collections()
    result = []
    for col in cols:
        name = col.name if hasattr(col, "name") else str(col)
        try:
            result.append({"name": name, "count": col.count()})
        except Exception:
            result.append({"name": name, "count": 0})
    return result


def delete_collection(name: str) -> None:
    _client.delete_collection(name)


def get_all_embeddings(
    collection_name: str,
) -> tuple[list[list[float]], list[str], list[int]]:
    """Get all embeddings for visualization. Returns (embeddings, texts, indices)."""
    collection = _client.get_collection(collection_name)
    result = collection.get(include=["embeddings", "documents", "metadatas"])
    embeddings = result["embeddings"]
    texts = result["documents"]
    indices = [m.get("index", i) for i, m in enumerate(result["metadatas"])]
    return embeddings, texts, indices
