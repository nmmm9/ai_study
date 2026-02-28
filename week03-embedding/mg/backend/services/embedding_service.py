import time

from openai import AsyncOpenAI

_client = AsyncOpenAI()


async def embed_texts(texts: list[str]) -> tuple[list[list[float]], int]:
    """Embed a list of texts. Returns (embeddings, time_ms)."""
    start = time.perf_counter()
    response = await _client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    embeddings = [item.embedding for item in response.data]
    return embeddings, elapsed_ms


async def embed_single(text: str) -> tuple[list[float], int]:
    """Embed a single text. Returns (embedding, time_ms)."""
    embeddings, elapsed_ms = await embed_texts([text])
    return embeddings[0], elapsed_ms
