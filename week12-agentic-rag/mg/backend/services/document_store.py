"""ChromaDB-based document store for Agentic RAG.

Each uploaded document is split into chunks, embedded, and stored with
metadata so the retriever can cite which document/page/chunk a passage
came from.

Design choices:
- Persistent ChromaDB at `./chroma_data/` (committed to .gitignore)
- OpenAI text-embedding-3-small (1536 dims, cheap)
- Cosine similarity (Chroma default)
- One collection per project — single-user demo, not multi-tenant
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Optional

import chromadb
from openai import AsyncOpenAI

_client = AsyncOpenAI()

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_data")
os.makedirs(CHROMA_PATH, exist_ok=True)

COLLECTION_NAME = "k_agent_docs"
EMBEDDING_MODEL = "text-embedding-3-small"

_chroma = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _chroma.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)


@dataclass
class Chunk:
    id: str
    text: str
    doc_id: str
    doc_name: str
    chunk_index: int
    page: Optional[int] = None
    score: Optional[float] = None


async def embed_one(text: str) -> list[float]:
    """Embed a single string."""
    resp = await _client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return resp.data[0].embedding


async def embed_many(texts: list[str]) -> list[list[float]]:
    """Batch-embed multiple strings (OpenAI accepts up to ~2048 inputs)."""
    if not texts:
        return []
    out: list[list[float]] = []
    BATCH = 96
    for i in range(0, len(texts), BATCH):
        batch = texts[i:i + BATCH]
        resp = await _client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        out.extend(d.embedding for d in resp.data)
    return out


async def add_chunks(chunks: list[Chunk]) -> int:
    """Embed and persist chunks. Returns number added."""
    if not chunks:
        return 0
    embeddings = await embed_many([c.text for c in chunks])
    _collection.add(
        ids=[c.id for c in chunks],
        embeddings=embeddings,
        documents=[c.text for c in chunks],
        metadatas=[{
            "doc_id": c.doc_id,
            "doc_name": c.doc_name,
            "chunk_index": c.chunk_index,
            "page": c.page if c.page is not None else -1,
        } for c in chunks],
    )
    return len(chunks)


async def search(
    query: str,
    top_k: int = 5,
    doc_id: Optional[str] = None,
) -> list[Chunk]:
    """Vector search. Optionally scoped to a specific document."""
    embedding = await embed_one(query)
    where = {"doc_id": doc_id} if doc_id else None
    res = _collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=where,
    )

    ids = res.get("ids", [[]])[0]
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    distances = res.get("distances", [[]])[0]

    chunks: list[Chunk] = []
    for i, cid in enumerate(ids):
        meta = metas[i] or {}
        # Cosine distance → similarity (1 - distance)
        score = 1.0 - float(distances[i]) if i < len(distances) else None
        chunks.append(Chunk(
            id=cid,
            text=docs[i],
            doc_id=meta.get("doc_id", ""),
            doc_name=meta.get("doc_name", ""),
            chunk_index=int(meta.get("chunk_index", 0)),
            page=int(meta.get("page", -1)) if meta.get("page", -1) != -1 else None,
            score=score,
        ))
    return chunks


def list_documents() -> list[dict]:
    """List unique documents currently indexed."""
    all_metas = _collection.get(include=["metadatas"]).get("metadatas", [])
    by_doc: dict[str, dict] = {}
    for m in all_metas:
        if not m:
            continue
        did = m.get("doc_id", "")
        if did not in by_doc:
            by_doc[did] = {
                "doc_id": did,
                "doc_name": m.get("doc_name", "(unknown)"),
                "chunks": 0,
            }
        by_doc[did]["chunks"] += 1
    return list(by_doc.values())


def delete_document(doc_id: str) -> int:
    """Remove all chunks for a given document. Returns count deleted."""
    res = _collection.get(where={"doc_id": doc_id}, include=[])
    ids = res.get("ids", [])
    if ids:
        _collection.delete(ids=ids)
    return len(ids)


def collection_stats() -> dict:
    """Quick stats for /api/documents."""
    count = _collection.count()
    return {
        "total_chunks": count,
        "documents": list_documents(),
    }


def new_doc_id() -> str:
    return f"doc-{uuid.uuid4().hex[:10]}"


def new_chunk_id(doc_id: str, idx: int) -> str:
    return f"{doc_id}::c{idx}"
