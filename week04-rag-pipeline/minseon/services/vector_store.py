"""
벡터 스토어 - ChromaDB 기반 벡터 DB

[관심사 분리 역할]
  이 파일: ChromaDB 저장/로드, 유사도 검색, 소스 다양성 보장
  embedding_service.py: 텍스트 → 벡터 변환
  rag_pipeline.py: 전체 파이프라인 조합 (이 클래스를 사용)

[ChromaDB 선택 이유]
  - 영구 저장 (PersistentClient)
  - 코사인 유사도 내장 (hnsw:space=cosine)
  - 벡터 저장/검색을 DB가 직접 처리 → numpy 불필요
"""

import uuid
import chromadb


class VectorStore:
    """
    ChromaDB 기반 벡터 데이터베이스

    저장 구조: ChromaDB PersistentClient (db_path 디렉터리)
    컬렉션: "documents" (코사인 유사도 공간)
    """

    def __init__(self, db_path: str):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )

    # ── 데이터 추가 ────────────────────────────────────────────

    def add(self, chunks: list[str], vectors: list[list[float]], metadatas: list[dict]) -> None:
        """청크 + 벡터 + 메타데이터를 ChromaDB 컬렉션에 추가"""
        ids = [str(uuid.uuid4()) for _ in chunks]
        self.collection.add(
            ids=ids,
            embeddings=vectors,
            documents=chunks,
            metadatas=metadatas,
        )

    def remove_source(self, source: str) -> None:
        """특정 소스의 모든 청크 제거"""
        results = self.collection.get(where={"source": source})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])

    # ── 검색 ──────────────────────────────────────────────────

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        threshold: float = 0.2,
        max_per_source: int = 2,
    ) -> list[dict]:
        """
        소스 다양성 보장 유사도 검색

        ChromaDB cosine distance = 1 - cosine_similarity
        → similarity = 1 - distance (threshold 0.2 → distance <= 0.8)

        Args:
            query_vector:   검색 질문의 벡터
            top_k:          반환할 최대 청크 수
            threshold:      최소 유사도 기준 (낮은 유사도 필터링)
            max_per_source: 동일 문서에서 최대 가져올 청크 수 (편중 방지)
        """
        total = self.collection.count()
        if total == 0:
            return []

        # max_per_source 필터링 여유분을 위해 더 많이 가져옴
        n_results = min(total, top_k * max_per_source * 3)

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        # distance → similarity 변환 + threshold 필터링
        scored = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            similarity = 1.0 - dist
            if similarity >= threshold:
                scored.append({"content": doc, "similarity": similarity, "metadata": meta})

        # 소스 다양성 보장: 같은 문서에서 max_per_source개까지만
        source_counts: dict[str, int] = {}
        final = []
        for item in scored:
            source = item["metadata"]["source"]
            count = source_counts.get(source, 0)
            if count < max_per_source:
                final.append(item)
                source_counts[source] = count + 1
            if len(final) >= top_k:
                break

        return final

    # ── 조회 ──────────────────────────────────────────────────

    def get_sources(self) -> list[dict]:
        """인덱싱된 소스 목록과 청크 수 반환"""
        results = self.collection.get(include=["metadatas"])
        source_counts: dict[str, int] = {}
        for meta in results["metadatas"]:
            src = meta["source"]
            source_counts[src] = source_counts.get(src, 0) + 1
        return [{"source": src, "chunks": cnt} for src, cnt in source_counts.items()]

    def total_chunks(self) -> int:
        return self.collection.count()
