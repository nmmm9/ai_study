"""
4주차 과제: RAG 파이프라인 오케스트레이터

[관심사 분리]
  이 파일: services를 조합하는 RagPipeline 클래스 (흐름 제어만 담당)
  services/document_service.py:  문서 로딩 (md/txt/pdf → 텍스트)
  services/chunking_service.py:  텍스트 청킹 (Recursive Splitting)
  services/embedding_service.py: 임베딩 (텍스트 → 벡터)
  services/vector_store.py:      벡터 DB (저장/검색/관리)
  services/llm_service.py:       LLM 스트리밍 호출 + 대화 관리

[파이프라인 흐름]
  인덱싱: 문서 로딩 → 청킹 → 임베딩 → 벡터DB 저장
  검색+생성: 질문 임베딩 → 유사도 검색 → 프롬프트 구성 → LLM 스트리밍
"""

import os

from dotenv import load_dotenv

from services.document_service import load_document
from services.chunking_service import split_text, CHUNK_SIZE, CHUNK_OVERLAP
from services.embedding_service import embed_texts, EMBEDDING_MODEL
from services.vector_store import VectorStore
from services.llm_service import stream_response, CHAT_MODEL, MAX_HISTORY


load_dotenv()

# ── 경로 설정 ──────────────────────────────────────────────────
DB_PATH  = os.path.join(os.path.dirname(__file__), "chroma_db")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ── 시스템 프롬프트 프리셋 ────────────────────────────────────
_BASE_RULES = """
## 답변 규칙
1. 반드시 아래 [참고 문서]에 있는 내용만 근거로 사용하세요.
2. 각 정보 뒤에 반드시 **[출처: 파일명]** 형식으로 출처를 표시하세요.
3. 문서에 없는 내용은 "해당 정보는 보유 문서에서 찾을 수 없습니다"라고 안내하세요.
4. 금액·나이·기간 등 수치 정보는 문서 내용을 정확하게 전달하세요.
5. 이전 대화 내용도 참고하여 자연스러운 대화를 이어가세요.

## 참고 문서
{context}
"""

PROMPT_PRESETS: dict[str, str] = {
    "default": (
        "당신은 청년 정책 전문 AI 상담사 '청년도우미'입니다.\n"
        "청년을 위한 정부 지원 정책(주거·취업·금융·교육·복지)을 아래 참고 문서에 기반해 정확하고 친절하게 안내합니다.\n\n"
        "## 답변 방식\n"
        "- 사용자의 상황을 파악해 관련 정책을 먼저 제시하고, 자격 조건 → 지원 내용 → 신청 방법 순으로 구체적으로 설명하세요.\n"
        "- '어떤 분야가 필요하세요?'처럼 되묻지 마세요. 맥락에서 파악되면 바로 관련 정책을 안내하세요.\n"
        "- 참고 문서에 관련 정책이 여러 개라면 모두 나열해 비교해주세요.\n"
        "- 이전 대화 내용을 반드시 참고해 자연스럽게 이어서 답변하세요.\n"
        + _BASE_RULES
    ),
    "friendly": (
        "당신은 친근하고 따뜻한 AI 상담사입니다.\n"
        "청년 정책을 쉽고 친절한 말투로 설명해주세요. 예시와 비유를 적극 활용하고, 공감하는 표현을 사용하세요."
        + _BASE_RULES
    ),
    "concise": (
        "당신은 간결한 AI 상담사입니다.\n"
        "핵심만 3~5줄 이내로 답변하세요. 불필요한 설명은 모두 생략합니다."
        + _BASE_RULES
    ),
    "simple": (
        "당신은 쉬운 말로 설명하는 AI 상담사입니다.\n"
        "중학생도 이해할 수 있게 어려운 용어를 풀어서 설명하고, 일상적인 비유를 활용하세요."
        + _BASE_RULES
    ),
    "expert": (
        "당신은 청년 정책 전문가 AI입니다.\n"
        "법령 근거, 세부 조건, 유사 정책 비교까지 전문가 수준으로 심층 분석해 답변하세요."
        + _BASE_RULES
    ),
}

SYSTEM_PROMPT_NO_DOC = """당신은 청년 정책 전문 AI 상담사 '청년도우미'입니다.
현재 인덱싱된 문서에서 관련 내용을 찾지 못했습니다.
일반적인 지식으로 최선을 다해 답변하되, 정확한 정보를 위해 공식 기관 확인을 권장해주세요.
한국어로 답변합니다."""

# 하위 호환용 (get_pipeline_info에서 사용)
SYSTEM_PROMPT_TEMPLATE = PROMPT_PRESETS["default"]


class RagPipeline:
    """
    RAG 파이프라인 오케스트레이터

    각 services를 조합해 인덱싱·검색·생성 흐름을 관리한다.
    비즈니스 로직은 services에 위임하고, 이 클래스는 흐름 제어만 담당.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.store = VectorStore(db_path)
        self.conversation: list[dict] = []
        self._last_hits: list[dict] = []
        self._last_usage: dict = {"input": 0, "output": 0}

    # ── 인덱싱 ────────────────────────────────────────────────

    def auto_index_data_dir(self) -> list[dict]:
        """data/ 폴더의 모든 .md/.txt 파일을 자동 인덱싱 (이미 인덱싱된 파일 건너뜀)"""
        if not os.path.exists(DATA_DIR):
            return []

        indexed_sources = {s["source"] for s in self.store.get_sources()}
        results = []

        for fname in sorted(os.listdir(DATA_DIR)):
            if not fname.endswith((".md", ".txt")):
                continue
            if fname in indexed_sources:
                continue
            fpath = os.path.join(DATA_DIR, fname)
            result = self.index_document(fpath, source_name=fname)
            results.append(result)

        return results

    def index_document(self, file_path: str, source_name: str | None = None) -> dict:
        """
        문서를 RAG 파이프라인에 인덱싱

        로딩 → 청킹 → 임베딩 → 벡터DB 저장 (같은 소스는 덮어쓰기)
        """
        source = source_name or os.path.basename(file_path)
        self.store.remove_source(source)

        text = load_document(file_path)
        chunks = [c for c in split_text(text) if c.strip()]
        if not chunks:
            return {"source": source, "chunks": 0, "chars": len(text)}
        vectors = embed_texts(chunks)

        metadatas = [
            {"source": source, "chunk_index": i, "total_chunks": len(chunks)}
            for i in range(len(chunks))
        ]
        self.store.add(chunks, vectors, metadatas)

        return {"source": source, "chunks": len(chunks), "chars": len(text)}

    # ── 검색 ──────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.2,
        max_per_source: int = 2,
    ) -> list[dict]:
        """질문을 벡터로 변환 후 유사도 검색"""
        query_vector = embed_texts([query])[0]
        return self.store.search(query_vector, top_k, threshold, max_per_source)

    # ── 프롬프트 구성 ─────────────────────────────────────────

    def _build_context(self, hits: list[dict]) -> str:
        """검색된 청크를 출처 포함 컨텍스트 문자열로 변환"""
        parts = []
        for i, hit in enumerate(hits):
            source = hit["metadata"]["source"]
            sim    = hit["similarity"]
            parts.append(
                f"[문서 {i+1}] 출처: {source} (유사도: {sim:.1%})\n"
                f"{hit['content']}"
            )
        return "\n\n---\n\n".join(parts)

    def _build_system_prompt(self, hits: list[dict], preset: str = "default") -> str:
        """출처 포함 컨텍스트를 주입한 시스템 프롬프트 생성"""
        if not hits:
            return SYSTEM_PROMPT_NO_DOC
        template = PROMPT_PRESETS.get(preset, PROMPT_PRESETS["default"])
        return template.format(context=self._build_context(hits))

    # ── 생성 (스트리밍) ───────────────────────────────────────

    def chat_stream(
        self,
        user_message: str,
        top_k: int = 5,
        threshold: float = 0.2,
        max_per_source: int = 2,
        preset: str = "default",
    ):
        """
        RAG + 대화 히스토리 기반 스트리밍 답변 생성

        Yields:
            str: 텍스트 청크
        """
        # 1. 검색
        hits = self.search(user_message, top_k, threshold, max_per_source)
        self._last_hits = hits

        # 2. 프롬프트 구성
        system_content = self._build_system_prompt(hits, preset=preset)

        # 3. LLM 스트리밍 호출 (대화 히스토리 in-place 수정)
        yield from stream_response(system_content, self.conversation, user_message)

        # 4. 사용량 저장 (app.py에서 스트림 종료 후 읽음)
        self._last_usage = getattr(stream_response, "_last_usage", {"input": 0, "output": 0})

    # ── 대화 관리 ─────────────────────────────────────────────

    def reset_conversation(self):
        self.conversation.clear()

    # ── 문서 관리 ─────────────────────────────────────────────

    def get_indexed_sources(self) -> list[dict]:
        return self.store.get_sources()

    def delete_source(self, source: str) -> bool:
        before = self.store.total_chunks()
        self.store.remove_source(source)
        return self.store.total_chunks() < before

    def get_stats(self) -> dict:
        return {
            "total_chunks":    self.store.total_chunks(),
            "total_documents": len(self.store.get_sources()),
            "embedding_model": EMBEDDING_MODEL,
            "chat_model":      CHAT_MODEL,
        }

    # ── 파이프라인 설명 ───────────────────────────────────────

    def get_pipeline_info(self) -> dict:
        """UI의 '동작 방식 보기' 탭에 사용할 파이프라인 설명"""
        return {
            "steps": [
                {
                    "step": "1. 인덱싱 (오프라인)",
                    "desc": "문서를 청크로 분할 → OpenAI 임베딩 모델로 벡터 변환 → JSON 파일에 저장",
                    "detail": f"청킹: Recursive Character Splitting (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})\n임베딩 모델: {EMBEDDING_MODEL}",
                },
                {
                    "step": "2. 검색 (Retrieval)",
                    "desc": "사용자 질문을 벡터로 변환 → 저장된 모든 벡터와 코사인 유사도 계산 → 상위 k개 반환",
                    "detail": "소스 다양성 보장: 동일 문서에서 최대 2개만 선택\n유사도 임계값: 0.2 이상만 포함",
                },
                {
                    "step": "3. 프롬프트 구성 (Augmentation)",
                    "desc": "검색된 청크를 [출처: 파일명] 형식으로 포맷 → 시스템 프롬프트에 주입",
                    "detail": "LLM에게 출처 표시 규칙, 답변 형식, 역할을 명시적으로 지시",
                },
                {
                    "step": "4. 생성 (Generation)",
                    "desc": "시스템 프롬프트 + 대화 히스토리 → GPT-4o-mini로 스트리밍 답변 생성",
                    "detail": f"모델: {CHAT_MODEL}\n대화 히스토리: 최근 {MAX_HISTORY}쌍 유지 (Sliding Window)",
                },
            ],
            "system_prompt_preview": SYSTEM_PROMPT_TEMPLATE[:300] + "...",
        }
