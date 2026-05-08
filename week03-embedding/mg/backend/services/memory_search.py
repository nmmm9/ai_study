import time
from dataclasses import dataclass

import numpy as np

from services.chunking_service import Chunk
from services.embedding_service import embed_texts


@dataclass
class ScoredChunk:
    index: int
    text: str
    score: float
    start: int
    end: int


async def search_in_memory(
    query: str, chunks: list[Chunk], top_k: int = 3
) -> tuple[list[ScoredChunk], int, int]:
    """
    In-memory search: embed ALL chunks + query every time, then cosine similarity.
    Returns (scored_chunks, embed_time_ms, search_time_ms).
    """
    all_texts = [query] + [c.text for c in chunks]
    embeddings, embed_time_ms = await embed_texts(all_texts)

    search_start = time.perf_counter()
    query_emb = np.array(embeddings[0])
    chunk_embs = np.array(embeddings[1:])

    norms = np.linalg.norm(chunk_embs, axis=1) * np.linalg.norm(query_emb)
    norms = np.where(norms == 0, 1e-10, norms)
    similarities = np.dot(chunk_embs, query_emb) / norms

    top_indices = np.argsort(similarities)[::-1][:top_k]
    search_time_ms = int((time.perf_counter() - search_start) * 1000)

    results = [
        ScoredChunk(
            index=chunks[idx].index,
            text=chunks[idx].text,
            score=float(similarities[idx]),
            start=chunks[idx].start,
            end=chunks[idx].end,
        )
        for idx in top_indices
    ]
    return results, embed_time_ms, search_time_ms
