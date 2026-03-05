"""
벡터 스토어 - 벡터 DB I/O 및 유사도 검색

[관심사 분리 역할]
  이 파일: JSON 벡터DB 저장/로드, 코사인 유사도 계산, 소스 다양성 보장 검색
  embedding_service.py: 텍스트 → 벡터 변환
  rag_pipeline.py: 전체 파이프라인 조합 (이 클래스를 사용)
"""

import json
import os

import numpy as np


class VectorStore:
    """
    JSON 파일 기반 벡터 데이터베이스

    저장 구조:
      {"chunks": [...], "vectors": [...], "metadatas": [...]}
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db = self._load()

    # ── DB I/O ────────────────────────────────────────────────

    def _load(self) -> dict:
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"chunks": [], "vectors": [], "metadatas": []}

    def save(self) -> None:
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.db, f, ensure_ascii=False)

    # ── 데이터 추가 ────────────────────────────────────────────

    def add(self, chunks: list[str], vectors: list[list[float]], metadatas: list[dict]) -> None:
        """청크 + 벡터 + 메타데이터를 DB에 추가하고 저장"""
        for chunk, vector, metadata in zip(chunks, vectors, metadatas):
            self.db["chunks"].append(chunk)
            self.db["vectors"].append(vector)
            self.db["metadatas"].append(metadata)
        self.save()

    def remove_source(self, source: str) -> None:
        """특정 소스의 모든 청크 제거"""
        keep = [
            (c, v, m)
            for c, v, m in zip(self.db["chunks"], self.db["vectors"], self.db["metadatas"])
            if m["source"] != source
        ]
        if keep:
            chunks, vectors, metadatas = zip(*keep)
            self.db["chunks"] = list(chunks)
            self.db["vectors"] = list(vectors)
            self.db["metadatas"] = list(metadatas)
        else:
            self.db = {"chunks": [], "vectors": [], "metadatas": []}
        self.save()

    # ── 검색 ──────────────────────────────────────────────────

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """두 벡터의 코사인 유사도 (-1 ~ 1, 높을수록 유사)"""
        a_arr, b_arr = np.array(a), np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        threshold: float = 0.2,
        max_per_source: int = 2,
    ) -> list[dict]:
        """
        소스 다양성 보장 유사도 검색

        Args:
            query_vector:   검색 질문의 벡터
            top_k:          반환할 최대 청크 수
            threshold:      최소 유사도 기준 (낮은 유사도 필터링)
            max_per_source: 동일 문서에서 최대 가져올 청크 수 (편중 방지)

        Returns:
            [{"content": str, "similarity": float, "metadata": dict}, ...]
        """
        if not self.db["chunks"]:
            return []

        # 모든 청크와 유사도 계산
        scored = [
            {
                "content":    self.db["chunks"][i],
                "similarity": self._cosine_similarity(query_vector, self.db["vectors"][i]),
                "metadata":   self.db["metadatas"][i],
            }
            for i in range(len(self.db["chunks"]))
        ]

        # 유사도 필터링 + 내림차순 정렬
        scored = [s for s in scored if s["similarity"] >= threshold]
        scored.sort(key=lambda x: x["similarity"], reverse=True)

        # 소스 다양성 보장: 같은 문서에서 max_per_source개까지만
        source_counts: dict[str, int] = {}
        results = []
        for item in scored:
            source = item["metadata"]["source"]
            count = source_counts.get(source, 0)
            if count < max_per_source:
                results.append(item)
                source_counts[source] = count + 1
            if len(results) >= top_k:
                break

        return results

    # ── 조회 ──────────────────────────────────────────────────

    def get_sources(self) -> list[dict]:
        """인덱싱된 소스 목록과 청크 수 반환"""
        source_counts: dict[str, int] = {}
        for meta in self.db["metadatas"]:
            src = meta["source"]
            source_counts[src] = source_counts.get(src, 0) + 1
        return [{"source": src, "chunks": cnt} for src, cnt in source_counts.items()]

    def total_chunks(self) -> int:
        return len(self.db["chunks"])
