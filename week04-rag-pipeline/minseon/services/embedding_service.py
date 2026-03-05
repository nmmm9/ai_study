"""
임베딩 서비스 - 텍스트를 벡터로 변환

[관심사 분리 역할]
  이 파일: OpenAI 임베딩 API 호출 (텍스트 → 숫자 벡터)
  chunking_service.py: 텍스트 청킹
  vector_store.py: 벡터 저장 및 유사도 검색
"""

from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"

def embed_texts(texts: list[str]) -> list[list[float]]:
    """OpenAI 임베딩 API로 텍스트 리스트를 벡터로 일괄 변환"""
    client = OpenAI()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]
