from dataclasses import dataclass

import numpy as np
from openai import AsyncOpenAI

from services.chunking_service import Chunk

_client = AsyncOpenAI()


@dataclass
class ScoredChunk:
    index: int
    text: str
    score: float
    start: int
    end: int


async def embed_texts(texts: list[str]) -> list[list[float]]:
    response = await _client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [item.embedding for item in response.data]


async def search_similar(
    query: str, chunks: list[Chunk], top_k: int = 3
) -> list[ScoredChunk]:
    all_texts = [query] + [c.text for c in chunks]
    embeddings = await embed_texts(all_texts)

    query_emb = np.array(embeddings[0])
    chunk_embs = np.array(embeddings[1:])

    norms = np.linalg.norm(chunk_embs, axis=1) * np.linalg.norm(query_emb)
    norms = np.where(norms == 0, 1e-10, norms)
    similarities = np.dot(chunk_embs, query_emb) / norms

    top_indices = np.argsort(similarities)[::-1][:top_k]

    return [
        ScoredChunk(
            index=chunks[idx].index,
            text=chunks[idx].text,
            score=float(similarities[idx]),
            start=chunks[idx].start,
            end=chunks[idx].end,
        )
        for idx in top_indices
    ]
