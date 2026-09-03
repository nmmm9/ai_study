"""
embedder.py — 텍스트 임베딩 모듈 (Modular RAG)

OpenAI text-embedding-3-small 모델로 벡터 변환
"""

from openai import OpenAI
from backend.config import settings

EMBEDDING_MODEL = "text-embedding-3-small"
_client = OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = _client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]
