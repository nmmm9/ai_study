"""
embedder.py — 텍스트 임베딩 모듈 (Modular RAG)

OpenAI text-embedding-3-small 모델로 벡터 변환
"""

from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

EMBEDDING_MODEL = "text-embedding-3-small"
_client = OpenAI()


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = _client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]
