"""
PDF 문서 처리 및 임베딩 생성 모듈
OpenAI Embedding API를 사용하여 문서를 벡터화
"""

import os
from typing import List, Tuple
from pypdf import PdfReader
from openai import OpenAI
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle


class DocumentProcessor:
    """PDF 문서를 처리하고 임베딩을 생성/관리하는 클래스"""

    def __init__(self, client: OpenAI):
        self.client = client
        self.chunks: List[str] = []
        self.embeddings: np.ndarray = None
        self.embedding_model = "text-embedding-3-small"

    def load_pdf(self, pdf_path: str, chunk_size: int = 500) -> None:
        """
        PDF 파일을 로드하고 청크로 분할

        Args:
            pdf_path: PDF 파일 경로
            chunk_size: 각 청크의 최대 문자 수
        """
        print(f"📄 PDF 파일 로딩 중: {pdf_path}")

        reader = PdfReader(pdf_path)
        full_text = ""

        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            full_text += text + "\n"
            print(f"  페이지 {page_num}/{len(reader.pages)} 처리 완료")

        # 텍스트를 청크로 분할
        self.chunks = self._split_text(full_text, chunk_size)
        print(f"✅ 총 {len(self.chunks)}개의 청크로 분할 완료\n")

    def _split_text(self, text: str, chunk_size: int) -> List[str]:
        """텍스트를 청크로 분할 (문장 단위 유지)"""
        sentences = text.replace('\n', ' ').split('. ')
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def create_embeddings(self) -> None:
        """모든 청크에 대한 임베딩 생성"""
        print("🔄 임베딩 생성 중...")

        embeddings_list = []
        for i, chunk in enumerate(self.chunks, 1):
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=chunk
            )
            embeddings_list.append(response.data[0].embedding)

            if i % 10 == 0:
                print(f"  {i}/{len(self.chunks)} 청크 처리 완료")

        self.embeddings = np.array(embeddings_list)
        print(f"✅ 임베딩 생성 완료 (shape: {self.embeddings.shape})\n")

    def search_similar_chunks(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        쿼리와 유사한 청크 검색

        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 수

        Returns:
            [(청크 텍스트, 유사도 점수), ...] 리스트
        """
        if self.embeddings is None:
            raise ValueError("임베딩이 생성되지 않았습니다. create_embeddings()를 먼저 실행하세요.")

        # 쿼리 임베딩 생성
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=query
        )
        query_embedding = np.array([response.data[0].embedding])

        # 코사인 유사도 계산
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]

        # 상위 k개 결과 추출
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        results = [(self.chunks[i], float(similarities[i])) for i in top_indices]

        return results

    def save_embeddings(self, filepath: str) -> None:
        """임베딩 데이터를 파일로 저장"""
        data = {
            'chunks': self.chunks,
            'embeddings': self.embeddings
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        print(f"💾 임베딩 데이터 저장 완료: {filepath}")

    def load_embeddings(self, filepath: str) -> None:
        """저장된 임베딩 데이터 로드"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")

        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        self.chunks = data['chunks']
        self.embeddings = data['embeddings']
        print(f"📂 임베딩 데이터 로드 완료: {len(self.chunks)}개 청크")
