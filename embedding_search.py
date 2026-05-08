"""
3주차: Embedding & Vector DB
sentence-transformers + FAISS 기반 의미 유사도 검색

2주차 키워드 매칭의 한계(조사/어미 불일치)를 극복하기 위해
텍스트를 고차원 벡터로 변환하고 코사인 유사도로 검색한다.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

import faiss  # type: ignore

# 한국어 포함 다국어 지원 모델 (약 278MB, 최초 실행 시 자동 다운로드)
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


class EmbeddingStore:
    """
    청크를 벡터로 변환하여 FAISS 인덱스에 저장하고,
    질문 벡터와의 코사인 유사도로 관련 청크를 검색한다.

    사용 흐름:
        store = EmbeddingStore()
        store.build(chunks)          # 문서 로드 후 1회
        results = store.search(query)  # 질문마다 호출
    """

    def __init__(self, model_name: str = EMBED_MODEL):
        # 모델 로드 (첫 실행 시 다운로드, 이후 로컬 캐시 사용)
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks: list[str] = []

    @property
    def is_built(self) -> bool:
        return self.index is not None and len(self.chunks) > 0

    def build(self, chunks: list[str]) -> None:
        """
        청크 리스트를 임베딩하여 FAISS 인덱스 구축.

        normalize_embeddings=True 로 L2 정규화 → 내적(Inner Product) = 코사인 유사도
        """
        self.chunks = list(chunks)
        embeddings = self.model.encode(
            self.chunks,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        dim = embeddings.shape[1]
        # IndexFlatIP: 완전 탐색 + 내적 유사도 (소규모 문서에 적합)
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings.astype(np.float32))

    def search(self, query: str, top_k: int = 5) -> list[tuple[float, str]]:
        """
        질문과 가장 유사한 청크를 (유사도, 청크 텍스트) 형태로 반환.

        유사도 점수: -1.0 ~ 1.0 (1.0에 가까울수록 유사)
        """
        if not self.is_built:
            return []
        q_emb = self.model.encode(
            [query], normalize_embeddings=True, convert_to_numpy=True
        ).astype(np.float32)
        k = min(top_k, len(self.chunks))
        scores, indices = self.index.search(q_emb, k)
        return [
            (float(scores[0][i]), self.chunks[indices[0][i]])
            for i in range(k)
        ]
