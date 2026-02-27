"""
4주차 과제: RAG 파이프라인 - 핵심 로직

이전 주차 학습 내용을 통합한 완전한 RAG 파이프라인:
  1주차 LLM API  +  2주차 청킹  +  3주차 임베딩/벡터DB
  → 문서 검색 기반 대화 히스토리 유지 챗봇
"""

import json
import os

import numpy as np
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI

load_dotenv()

# ── 설정 ──────────────────────────────────────────────────────
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 90
DB_PATH = "./vector_db.json"
MAX_HISTORY = 10  # 대화 히스토리 유지 개수 (user+assistant 쌍)


class RagPipeline:
    """
    RAG 파이프라인 전체를 관리하는 클래스

    [인덱싱]  문서 로딩 → 청킹 → 임베딩 → 벡터DB 저장
    [검색+생성] 질문 임베딩 → 유사도 검색 → 대화 히스토리 + LLM 답변
    """

    def __init__(self, db_path: str = DB_PATH):
        self.client = OpenAI()
        self.db_path = db_path
        self.db = self._load_db()
        self.conversation: list[dict] = []  # [{"role": ..., "content": ...}]

    # ── 벡터 DB I/O ────────────────────────────────────────────

    def _load_db(self) -> dict:
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"chunks": [], "vectors": [], "metadatas": []}

    def _save_db(self) -> None:
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.db, f, ensure_ascii=False)

    # ── 인덱싱: 문서 로딩 ─────────────────────────────────────

    def load_document(self, file_path: str) -> str:
        """파일 확장자에 따라 텍스트 추출 (md / txt / pdf)"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in (".md", ".markdown", ".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".pdf":
            import fitz  # pymupdf
            doc = fitz.open(file_path)
            return "\n\n".join(page.get_text() for page in doc)
        raise ValueError(f"지원하지 않는 파일 형식: {ext}")

    # ── 인덱싱: 청킹 ──────────────────────────────────────────

    def split_text(self, text: str) -> list[str]:
        """Recursive Character Splitting (2주차와 동일한 방식)"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
            length_function=len,
        )
        return splitter.split_text(text)

    # ── 인덱싱: 임베딩 ────────────────────────────────────────

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """OpenAI 임베딩 API로 텍스트 리스트를 벡터로 일괄 변환"""
        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]

    # ── 인덱싱: 전체 파이프라인 ──────────────────────────────

    def index_document(self, file_path: str, source_name: str | None = None) -> dict:
        """
        문서를 RAG 파이프라인에 인덱싱

        로딩 → 청킹 → 임베딩 → 벡터DB 저장 (같은 소스는 덮어쓰기)

        Returns:
            {"source": str, "chunks": int, "chars": int}
        """
        source = source_name or os.path.basename(file_path)

        # 같은 소스 기존 데이터 제거 (덮어쓰기)
        self._remove_source_from_db(source)

        text = self.load_document(file_path)
        chunks = self.split_text(text)
        vectors = self.embed_texts(chunks)

        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            self.db["chunks"].append(chunk)
            self.db["vectors"].append(vector)
            self.db["metadatas"].append({"source": source, "chunk_index": i})

        self._save_db()
        return {"source": source, "chunks": len(chunks), "chars": len(text)}

    # ── 검색: 코사인 유사도 ───────────────────────────────────

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """두 벡터의 코사인 유사도 (-1 ~ 1, 높을수록 유사)"""
        a_arr, b_arr = np.array(a), np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))

    def search(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.0,
    ) -> list[dict]:
        """
        질문과 의미적으로 유사한 청크를 검색

        Args:
            query: 검색할 질문 텍스트
            top_k: 반환할 최대 청크 수
            threshold: 최소 유사도 기준 (0.0 = 필터 없음)

        Returns:
            [{"content": str, "similarity": float, "metadata": dict}, ...]
        """
        if not self.db["chunks"]:
            return []

        query_vector = self.embed_texts([query])[0]

        similarities = [
            self._cosine_similarity(query_vector, vec)
            for vec in self.db["vectors"]
        ]

        # 유사도 높은 순으로 정렬 후 top_k 추출
        top_indices = np.argsort(similarities)[::-1][:top_k]

        return [
            {
                "content": self.db["chunks"][idx],
                "similarity": similarities[idx],
                "metadata": self.db["metadatas"][idx],
            }
            for idx in top_indices
            if similarities[idx] >= threshold
        ]

    # ── 생성: 시스템 프롬프트 구성 ───────────────────────────

    def _build_system_prompt(self, hits: list[dict]) -> str:
        """검색된 청크를 포함한 시스템 프롬프트 생성"""
        if not hits:
            return (
                "당신은 친절한 AI 어시스턴트입니다. 한국어로 답변합니다.\n"
                "현재 인덱싱된 문서에서 관련 내용을 찾지 못했습니다. "
                "일반적인 지식으로 최선을 다해 답변해주세요."
            )

        context = "\n\n---\n\n".join(h["content"] for h in hits)
        return (
            "당신은 주어진 문서를 기반으로 질문에 답변하는 AI 어시스턴트입니다.\n"
            "한국어로 답변하며, 문서에 없는 내용은 솔직하게 '문서에서 찾을 수 없습니다'라고 말합니다.\n"
            "이전 대화 내용도 참고하여 자연스러운 대화를 이어갑니다.\n\n"
            f"[참고 문서]\n{context}"
        )

    # ── 생성: 스트리밍 응답 ───────────────────────────────────

    def chat_stream(
        self,
        user_message: str,
        top_k: int = 3,
        threshold: float = 0.0,
    ):
        """
        RAG + 대화 히스토리 기반 스트리밍 답변 생성

        Streamlit의 st.write_stream()에서 사용하도록 설계됨

        Yields:
            str: 텍스트 청크 (스트리밍 중)
            마지막으로 (None, hits, usage) 튜플을 별도 채널로 전달
            → stream_generator() 래퍼를 통해 hits와 usage를 캡처

        흐름:
            1. 질문 관련 청크 검색
            2. 시스템 프롬프트 + 대화 히스토리 구성
            3. OpenAI Streaming API 호출
            4. 텍스트 조각 yield
            5. 대화 히스토리에 응답 추가
        """
        # 1. 검색
        hits = self.search(user_message, top_k=top_k, threshold=threshold)

        # 2. 프롬프트 + 히스토리 구성
        system_content = self._build_system_prompt(hits)
        self.conversation.append({"role": "user", "content": user_message})
        self._trim_conversation()
        messages = [{"role": "system", "content": system_content}] + self.conversation

        # 3. 스트리밍 API 호출
        stream = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
        )

        # 4. 텍스트 yield
        full_response = ""
        input_tokens = 0
        output_tokens = 0

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_response += text
                yield text
            if hasattr(chunk, "usage") and chunk.usage:
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens

        # 5. 대화 히스토리에 추가
        self.conversation.append({"role": "assistant", "content": full_response})

        # 메타데이터를 인스턴스 변수에 저장 (app.py에서 스트림 종료 후 읽음)
        self._last_hits = hits
        self._last_usage = {"input": input_tokens, "output": output_tokens}

    # ── 대화 관리 ─────────────────────────────────────────────

    def _trim_conversation(self):
        """대화 히스토리를 MAX_HISTORY 쌍(user+assistant)으로 제한"""
        max_messages = MAX_HISTORY * 2
        if len(self.conversation) > max_messages:
            self.conversation = self.conversation[-max_messages:]

    def reset_conversation(self):
        """대화 히스토리 초기화"""
        self.conversation.clear()

    # ── 문서 관리 ─────────────────────────────────────────────

    def get_indexed_sources(self) -> list[dict]:
        """
        인덱싱된 문서 목록 반환

        Returns:
            [{"source": str, "chunks": int}, ...]
        """
        source_counts: dict[str, int] = {}
        for meta in self.db["metadatas"]:
            src = meta["source"]
            source_counts[src] = source_counts.get(src, 0) + 1
        return [{"source": src, "chunks": cnt} for src, cnt in source_counts.items()]

    def _remove_source_from_db(self, source: str):
        """특정 소스의 모든 청크를 메모리 내 DB에서 제거 (저장 안 함)"""
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

    def delete_source(self, source: str) -> bool:
        """
        문서를 벡터DB에서 삭제

        Returns:
            True if 삭제 성공, False if 해당 소스 없음
        """
        before = len(self.db["chunks"])
        self._remove_source_from_db(source)
        self._save_db()
        return len(self.db["chunks"]) < before

    def get_stats(self) -> dict:
        """현재 벡터DB 통계 반환"""
        sources = self.get_indexed_sources()
        return {
            "total_chunks": len(self.db["chunks"]),
            "total_documents": len(sources),
            "embedding_model": EMBEDDING_MODEL,
            "chat_model": CHAT_MODEL,
        }
