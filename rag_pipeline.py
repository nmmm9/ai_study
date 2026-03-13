"""
1주차: OpenAI GPT API 연동 - 터미널 챗봇
2주차: PDF/Markdown 로드 및 텍스트 청킹 전략
3주차: Embedding & Vector DB (sentence-transformers + ChromaDB)
4주차: 완전한 RAG 파이프라인
       - Retriever + Prompt + Generator 결합
       - 문맥 참고 답변 프롬프트 설계
       - Citation (출처 표시)
       - 출력 검증
       - Re-ranker (Cross-Encoder 기반 2단계 검색)
       - Guardrails (취업 외 질문 차단)
       - Vector DB: ChromaDB (디스크에 영구 저장)
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent / ".env")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 문서 로더 (2주차)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DocumentLoader:
    """PDF / Markdown 파일에서 텍스트 추출"""

    @staticmethod
    def load(path: str) -> str:
        ext = Path(path).suffix.lower()
        if ext == ".md":
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == ".pdf":
            try:
                import pypdf
            except ImportError:
                raise ImportError("PDF 로드에는 pypdf가 필요합니다: pip install pypdf")
            reader = pypdf.PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            raise ValueError(f"지원하지 않는 형식: {ext}  (.md, .pdf 만 지원)")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 텍스트 청커 (2주차)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TextChunker:
    """
    텍스트 분할 전략 3가지:

    fixed      - 글자 수 기준 고정 크기 분할 + overlap
    separator  - 구분자(\n\n → \n → '. ' → ' ') 기반 재귀 분할
    paragraph  - 빈 줄 기준 단락 분할 (취업공고처럼 항목이 나뉜 문서에 적합)
    """

    STRATEGIES = ("fixed", "separator", "paragraph")

    def __init__(self, strategy: str = "paragraph", chunk_size: int = 400, overlap: int = 50):
        if strategy not in self.STRATEGIES:
            raise ValueError(f"전략은 {self.STRATEGIES} 중 하나여야 합니다.")
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        dispatch = {
            "fixed":     self._fixed,
            "separator": self._separator,
            "paragraph": self._paragraph,
        }
        return dispatch[self.strategy](text)

    def _fixed(self, text: str) -> list[str]:
        """
        글자 수 기준으로 chunk_size만큼 자르되,
        overlap만큼 이전 청크와 겹쳐서 문맥 단절을 줄임.
        예) chunk_size=400, overlap=50 → 0~400 / 350~750 / 700~1100 ...
        """
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            piece = text[start:end].strip()
            if piece:
                chunks.append(piece)
            if end == len(text):
                break
            start += self.chunk_size - self.overlap
        return chunks

    def _separator(self, text: str) -> list[str]:
        """
        구분자 우선순위: \n\n → \n → '. ' → ' '
        chunk_size 이하가 될 때까지 더 작은 구분자로 재귀 분할.
        langchain RecursiveCharacterTextSplitter와 같은 원리.
        """
        return self._recursive_split(text.strip(), ["\n\n", "\n", ". ", " "])

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]
        sep = separators[0]
        next_seps = separators[1:]
        parts = text.split(sep)
        chunks = []
        current = ""
        for part in parts:
            candidate = current + (sep if current else "") + part
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    if len(current) > self.chunk_size and next_seps:
                        chunks.extend(self._recursive_split(current, next_seps))
                    else:
                        chunks.append(current.strip())
                current = part
        if current:
            if len(current) > self.chunk_size and next_seps:
                chunks.extend(self._recursive_split(current, next_seps))
            else:
                chunks.append(current.strip())
        return [c for c in chunks if c]

    def _paragraph(self, text: str) -> list[str]:
        """
        빈 줄(\n\n)을 기준으로 단락을 모으되,
        chunk_size를 넘으면 새 청크를 시작.
        취업공고의 '주요업무', '자격요건' 같은 항목 단위가 자연스럽게 유지됨.
        """
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        chunks = []
        current = ""
        for para in paras:
            candidate = current + ("\n\n" if current else "") + para
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = para
        if current:
            chunks.append(current)
        return chunks


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 청크 메타데이터 (4주차: Citation용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ChunkWithMeta:
    """청크 텍스트 + 출처 정보 (Citation에 사용)"""
    text: str
    source: str       # 파일명
    company: str      # 회사명 (예: 카카오)
    section: str      # 섹션명 (예: 자격 요건)
    chunk_id: int


def extract_metadata(chunks: list[str], source_path: str) -> list[ChunkWithMeta]:
    """
    청크에서 회사명과 섹션명을 추출하여 메타데이터 생성.

    취업공고 형식:
      ## 공고 N: 회사명 — 직함  →  회사 구분
      ### 섹션명               →  섹션 구분
    """
    source = Path(source_path).name
    result = []
    current_company = ""
    current_section = ""

    for i, chunk in enumerate(chunks):
        company_match = re.search(r"##\s+공고\s+\d+:\s+(.+?)\s+[—\-]", chunk)
        section_match = re.search(r"###\s+(.+?)(?:\n|$)", chunk)
        if company_match:
            current_company = company_match.group(1).strip()
        if section_match:
            current_section = section_match.group(1).strip()
        result.append(ChunkWithMeta(
            text=chunk,
            source=source,
            company=current_company,
            section=current_section,
            chunk_id=i,
        ))
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 벡터 저장소: ChromaDB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import chromadb
from chromadb.utils import embedding_functions

EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CHROMA_DIR = str(Path(__file__).parent / "chroma_db")


class VectorStore:
    """
    ChromaDB 기반 벡터 저장소.

    - sentence-transformers로 청크를 벡터로 변환
    - ChromaDB 컬렉션에 문서 + 메타데이터(회사명, 섹션명) 함께 저장
    - 디스크(chroma_db/ 폴더)에 영구 저장 → 다음 실행 시 재계산 없이 사용
    - 코사인 유사도로 관련 청크 검색
    """

    COLLECTION_NAME = "job_postings"

    def __init__(self, persist_dir: str = CHROMA_DIR):
        # PersistentClient: 데이터를 persist_dir 폴더에 파일로 저장
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},  # 코사인 유사도 사용
        )

    @property
    def is_built(self) -> bool:
        return self.collection.count() > 0

    def build(self, chunks_meta: list[ChunkWithMeta]) -> None:
        """
        청크를 임베딩하여 ChromaDB 컬렉션에 저장.
        기존 데이터는 삭제 후 재구축.
        """
        # 기존 컬렉션 초기화 후 재생성
        self.client.delete_collection(self.COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )

        # 배치 단위로 저장 (ChromaDB 권장 방식)
        batch_size = 50
        for i in range(0, len(chunks_meta), batch_size):
            batch = chunks_meta[i:i + batch_size]
            # 회사명 + 섹션을 청크 앞에 붙여 임베딩 품질 향상
            docs = [
                f"{c.company} - {c.section}:\n{c.text}" if c.company else c.text
                for c in batch
            ]
            self.collection.add(
                documents=docs,
                metadatas=[
                    {"company": c.company, "section": c.section, "source": c.source}
                    for c in batch
                ],
                ids=[f"chunk_{c.chunk_id}" for c in batch],
            )
        print(f"  [ChromaDB] {self.collection.count()}개 청크 저장 완료 → {CHROMA_DIR}")

    def search(self, query: str, top_k: int = 10) -> list[tuple[float, ChunkWithMeta]]:
        """
        질문과 가장 유사한 청크를 (유사도, 메타데이터) 형태로 반환.
        ChromaDB cosine space는 거리(distance)를 반환하므로
        유사도 = 1 - distance 로 변환.
        """
        if not self.is_built:
            return []

        k = min(top_k, self.collection.count())
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]
        ids = results["ids"][0]

        output = []
        for doc, meta, dist, chunk_id in zip(docs, metas, distances, ids):
            similarity = 1.0 - dist  # cosine distance → similarity 변환
            cm = ChunkWithMeta(
                text=doc,
                source=meta.get("source", ""),
                company=meta.get("company", ""),
                section=meta.get("section", ""),
                chunk_id=int(chunk_id.split("_")[1]),
            )
            output.append((similarity, cm))
        return output


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. Re-ranker (4주차 신규)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Reranker:
    """
    Cross-Encoder 기반 2단계 재정렬.

    Bi-Encoder(ChromaDB)는 질문과 청크를 따로 임베딩하기 때문에
    문맥 상호작용이 없어 정밀도가 떨어질 수 있습니다.
    Cross-Encoder는 질문 + 청크를 한 번에 입력하여 직접 관련성 점수를 계산합니다.

    [2단계 검색 흐름]
    1단계: ChromaDB Bi-Encoder → top-10 후보 빠르게 추출
    2단계: Cross-Encoder       → top-10에서 top-3 정밀 선정
    """

    def __init__(self):
        self._model = None
        try:
            from sentence_transformers import CrossEncoder
            # 다국어 지원 Cross-Encoder (한국어 포함)
            self._model = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
            print("  [Re-ranker] Cross-Encoder 로드 완료")
        except Exception as e:
            print(f"  [Re-ranker] Cross-Encoder 미사용 → 임베딩 스코어 유지 ({e})")

    def rerank(
        self,
        query: str,
        candidates: list[tuple[float, ChunkWithMeta]],
        top_k: int = 3,
    ) -> list[tuple[float, ChunkWithMeta]]:
        """
        후보 청크를 Cross-Encoder로 재정렬하여 상위 top_k 반환.
        Cross-Encoder 미설치 시 기존 임베딩 스코어 순위 유지.
        """
        if self._model is None or not candidates:
            return candidates[:top_k]

        pairs = [(query, c.text) for _, c in candidates]
        scores = self._model.predict(pairs)
        ranked = sorted(
            zip(scores.tolist(), [c for _, c in candidates]),
            key=lambda x: x[0],
            reverse=True,
        )
        return [(float(s), c) for s, c in ranked[:top_k]]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. Guardrails (4주차 신규)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Guardrail:
    """
    입력/출력 가드레일.

    [목적]
    이 챗봇은 '취업 상담' 전용입니다.
    연애, 게임, 날씨 같은 무관한 질문을 차단하여
    챗봇이 의도된 목적 외로 사용되는 것을 방지합니다.

    [입력 가드레일]
    GPT-4o-mini에게 취업 관련 여부를 JSON으로 분류 요청.
    취업과 무관하면 안내 메시지 반환.

    [출력 가드레일]
    - 답변 길이 검증 (너무 짧으면 경고)
    - 단정적 표현 패턴 탐지 (환각 방지)
    """

    _CLASSIFY_SYSTEM = (
        "당신은 메시지가 '취업/채용/커리어' 관련 질문인지 판단하는 분류기입니다.\n"
        "판단 기준:\n"
        "- 취업, 이직, 채용공고, 자격요건, 연봉, 복리후생, 면접, 직무, 회사, 경력, "
        "  스택, 기술, 지원, 전형, 우대사항, 계약, 인턴 → 관련(true)\n"
        "- 연애, 음식, 게임, 스포츠, 날씨, 정치, 일상 잡담, 영화, 음악 → 무관(false)\n"
        "반드시 JSON 형식으로만 응답하세요: {\"related\": true} 또는 {\"related\": false}"
    )

    OFF_TOPIC_MSG = (
        "⚠️ 저는 취업 상담 전용 AI입니다.\n"
        "취업, 채용공고, 직무, 자격요건, 연봉, 면접 등\n"
        "취업 관련 질문을 입력해 주세요."
    )

    def __init__(self, client: OpenAI):
        self.client = client

    def check_input(self, user_input: str) -> bool:
        """
        입력 검증: 취업 관련 질문이면 True, 아니면 False.
        GPT 호출 실패 시 허용(True) 처리 → false negative 방지.
        """
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=20,
                temperature=0,
                messages=[
                    {"role": "system", "content": self._CLASSIFY_SYSTEM},
                    {"role": "user", "content": user_input},
                ],
            )
            raw = resp.choices[0].message.content or "{}"
            data = json.loads(raw)
            return bool(data.get("related", True))
        except Exception:
            return True  # 분류 실패 시 허용

    def check_output(self, answer: str) -> tuple[bool, str]:
        """
        출력 검증.
        Returns: (valid, warning_message)
        """
        if len(answer.strip()) < 10:
            return False, "답변이 너무 짧습니다. 다시 질문해 주세요."

        # 단정적 표현 패턴 감지 (간단한 환각 방지)
        hallucination_patterns = [
            r"반드시\s+합격",
            r"100%\s+취업",
            r"절대적으로\s+보장",
        ]
        for pattern in hallucination_patterns:
            if re.search(pattern, answer):
                return False, "불확실한 단정 표현이 감지되었습니다."

        return True, ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. RAG 파이프라인 (4주차 핵심)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 프롬프트 설계 (Prompt Engineering) ──────────────────────────
# [시스템 프롬프트 설계 원칙]
# 1. 역할 명시: 취업 상담 전문 AI임을 명확히 정의
# 2. 출처 기반 답변 강제: 제공된 문서 외 정보 사용 금지
# 3. 불확실성 인정: 모르는 내용은 솔직히 말하도록 지시
# 4. Citation 형식 지정: [출처: 회사명 - 섹션명] 형식 통일
# 5. 언어 고정: 한국어로만 답변

SYSTEM_PROMPT = """당신은 취업 상담 전문 AI 어시스턴트입니다.

[역할]
제공된 취업공고 데이터를 기반으로 구직자에게 정확한 취업 정보를 제공합니다.

[답변 규칙]
1. 반드시 아래에 제공된 [참조 문서] 내용만 근거로 답변하세요.
2. 문서에 없는 내용은 "해당 정보는 제공된 공고에서 확인되지 않습니다"라고 말하세요.
3. 답변 마지막에 참조한 출처를 반드시 표시하세요.
   형식: [출처: 회사명 - 섹션명]
4. 여러 공고를 비교할 때는 각 회사를 명확히 구분하여 설명하세요.
5. 한국어로 답변하세요.

[출처 표시 예시]
카카오는 Java/Kotlin 기반 백엔드 개발 경험 3년 이상을 요구합니다.
[출처: 카카오 - 자격 요건]"""


class RAGPipeline:
    """
    완전한 RAG 파이프라인.

    [LLM이 돌아가는 방식]
    ┌─────────────────────────────────────────────────────────┐
    │  사용자 질문                                            │
    │       ↓                                                 │
    │  [Guardrail] 취업 관련 질문인지 GPT로 분류              │
    │       ↓ (허용된 경우)                                   │
    │  [Retriever] ChromaDB 벡터 검색 (Bi-Encoder, top-10)   │
    │       ↓                                                 │
    │  [Re-ranker] Cross-Encoder로 정밀 재정렬 (top-3)        │
    │       ↓                                                 │
    │  [Prompt] 시스템 + 출처 포함 컨텍스트 + 대화 히스토리  │
    │       ↓                                                 │
    │  [Generator] GPT-4o-mini 스트리밍 답변 생성            │
    │       ↓                                                 │
    │  [Output Guard] 출력 검증 (길이, 단정 표현 탐지)        │
    │       ↓                                                 │
    │  최종 답변 + [출처: 회사명 - 섹션명]                    │
    └─────────────────────────────────────────────────────────┘
    """

    MODEL = "gpt-4o-mini"
    MAX_HISTORY_TURNS = 10
    MAX_RESPONSE_TOKENS = 1024

    def __init__(self):
        self.client = OpenAI()
        self.store = VectorStore()
        self.reranker = Reranker()
        self.guardrail = Guardrail(self.client)
        self.history: list[dict] = []
        self.token_usage = {"input": 0, "output": 0}
        self._last_citations: list[str] = []

    # ── 문서 로드 ────────────────────────────────────────────────

    def load_document(
        self, path: str, strategy: str = "paragraph", chunk_size: int = 200
    ) -> int:
        """문서 로드 → 청킹 → 메타데이터 추출 → 임베딩 인덱스 구축"""
        raw = DocumentLoader.load(path)
        chunker = TextChunker(strategy=strategy, chunk_size=chunk_size)
        chunks = chunker.chunk(raw)
        chunks_meta = extract_metadata(chunks, path)

        print(f"  [로드] {Path(path).name} | 전략: {strategy} | 청크: {len(chunks)}개")
        print("  [ChromaDB] 벡터 인덱스 구축 중...")
        self.store.build(chunks_meta)
        return len(chunks)

    # ── 검색 (Retrieval) ─────────────────────────────────────────

    def _retrieve(self, query: str) -> list[tuple[float, ChunkWithMeta]]:
        """
        1단계: ChromaDB 벡터 검색 (Bi-Encoder, top-10 후보 추출)
        2단계: Cross-Encoder Re-ranking (top-3 정밀 선정)
        """
        candidates = self.store.search(query, top_k=10)
        # Re-ranking: top-10 → top-3
        return self.reranker.rerank(query, candidates, top_k=3)

    # ── 프롬프트 구성 ────────────────────────────────────────────

    def _build_context(self, results: list[tuple[float, ChunkWithMeta]]) -> str:
        """
        검색된 청크를 컨텍스트 문자열로 변환.
        각 청크에 [참조 N] + 출처 정보를 포함하여 GPT가 Citation을 표시할 수 있게 함.
        """
        if not results:
            return ""

        self._last_citations = []
        parts = []

        for i, (score, meta) in enumerate(results, 1):
            citation = f"{meta.company} - {meta.section}" if meta.company else meta.source
            self._last_citations.append(citation)
            parts.append(
                f"[참조 {i}] 출처: {citation} (유사도: {score:.3f})\n{meta.text}"
            )

        return "[참조 문서]\n\n" + "\n\n---\n\n".join(parts)

    def _build_messages(self, context: str = "") -> list[dict]:
        """시스템 프롬프트 + 컨텍스트 + 대화 히스토리 조합"""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "system", "content": context})
        # 히스토리 최대 N턴 유지 (토큰 절약)
        max_msgs = self.MAX_HISTORY_TURNS * 2
        messages.extend(self.history[-max_msgs:])
        return messages

    # ── 스트리밍 생성 (Generator) ─────────────────────────────────

    def _stream(self, messages: list[dict]) -> tuple[str, int, int]:
        """스트리밍 API 호출 → (응답 텍스트, 입력토큰, 출력토큰)"""
        reply = ""
        input_tokens = output_tokens = 0

        stream = self.client.chat.completions.create(
            model=self.MODEL,
            max_tokens=self.MAX_RESPONSE_TOKENS,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                print(text, end="", flush=True)
                reply += text
            if chunk.usage:
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens

        print()
        return reply, input_tokens, output_tokens

    # ── 메인 질의응답 (전체 RAG 흐름) ────────────────────────────

    def ask(self, user_input: str) -> str:
        """
        완전한 RAG 파이프라인 실행:
        Guardrail 입력 검증 → 검색 → 리랭킹 → 프롬프트 → 생성 → Guardrail 출력 검증
        """
        # ① 입력 가드레일
        print("  [가드레일] 입력 검증 중...", end="\r")
        if not self.guardrail.check_input(user_input):
            print("                              ")
            print(f"\nAI: {self.guardrail.OFF_TOPIC_MSG}\n")
            return self.guardrail.OFF_TOPIC_MSG
        print("  [가드레일] ✓ 취업 관련 질문   ")

        # ② 검색 + 리랭킹 (Retrieval)
        results = self._retrieve(user_input)
        if results:
            src_preview = ", ".join(self._last_citations[:2])
            print(f"  [검색] {len(results)}개 청크 검색됨 | {src_preview}...")

        # ③ 컨텍스트 구성
        context = self._build_context(results)

        # ④ 히스토리에 사용자 질문 추가
        self.history.append({"role": "user", "content": user_input})

        # ⑤ 생성 (스트리밍)
        print("\nAI: ", end="")
        messages = self._build_messages(context)
        reply, in_tok, out_tok = self._stream(messages)

        # ⑥ 출력 가드레일 (검증)
        valid, warning = self.guardrail.check_output(reply)
        if not valid:
            print(f"  [출력 검증] ⚠️  {warning}")

        # ⑦ 토큰 누적 + 히스토리 저장
        self.token_usage["input"] += in_tok
        self.token_usage["output"] += out_tok
        print(f"  [토큰] 입력 {in_tok} / 출력 {out_tok}")
        self.history.append({"role": "assistant", "content": reply})

        return reply

    # ── Streamlit용 스트리밍 제너레이터 ──────────────────────────

    def ask_stream(self, user_input: str):
        """
        Streamlit용 RAG 파이프라인 (제너레이터 방식).
        터미널 print 대신 dict를 yield하여 UI에서 자유롭게 표시 가능.

        yield 타입:
          {"type": "status",   "text": "..."}         ← 진행 상태
          {"type": "blocked",  "text": "..."}         ← 가드레일 차단
          {"type": "citations","citations": [...]}    ← 출처 목록
          {"type": "text",     "text": "..."}         ← 답변 텍스트 조각
          {"type": "done",     "tokens": {...}}       ← 완료 + 토큰 정보
        """
        # ① 입력 가드레일
        yield {"type": "status", "text": "입력 검증 중..."}
        if not self.guardrail.check_input(user_input):
            yield {"type": "blocked", "text": self.guardrail.OFF_TOPIC_MSG}
            return

        # ② 검색 + 리랭킹
        yield {"type": "status", "text": "관련 공고 검색 중..."}
        results = self._retrieve(user_input)
        context = self._build_context(results)
        yield {"type": "citations", "citations": list(self._last_citations)}

        # ③ 히스토리 추가
        self.history.append({"role": "user", "content": user_input})

        # ④ 스트리밍 생성
        yield {"type": "status", "text": "답변 생성 중..."}
        messages = self._build_messages(context)
        reply = ""
        input_tokens = output_tokens = 0

        stream = self.client.chat.completions.create(
            model=self.MODEL,
            max_tokens=self.MAX_RESPONSE_TOKENS,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                reply += text
                yield {"type": "text", "text": text}
            if chunk.usage:
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens

        # ⑤ 출력 가드레일
        valid, warning = self.guardrail.check_output(reply)

        # ⑥ 저장
        self.token_usage["input"] += input_tokens
        self.token_usage["output"] += output_tokens
        self.history.append({"role": "assistant", "content": reply})

        yield {
            "type": "done",
            "tokens": {"input": input_tokens, "output": output_tokens},
            "output_warning": warning if not valid else "",
        }

    # ── 유틸리티 ────────────────────────────────────────────────

    def reset(self):
        self.history.clear()
        print("  대화 히스토리를 초기화했습니다.\n")

    def print_usage(self):
        total = self.token_usage["input"] + self.token_usage["output"]
        print(f"\n── 누적 토큰 사용량 ──")
        print(f"  입력:  {self.token_usage['input']} 토큰")
        print(f"  출력:  {self.token_usage['output']} 토큰")
        print(f"  합계:  {total} 토큰")
        print(f"  대화:  {len(self.history) // 2}턴\n")

    def print_pipeline_info(self):
        """RAG 파이프라인 구성 및 동작 방식 출력"""
        print("\n━━━━ RAG 파이프라인 구성 ━━━━")
        reranker_status = "Cross-Encoder (mmarco-mMiniLMv2)" if self.reranker._model else "미사용"
        print(f"  LLM 모델:   {self.MODEL}")
        print(f"  임베딩:     {EMBED_MODEL}")
        print(f"  Vector DB:  ChromaDB (디스크 저장 → {CHROMA_DIR})")
        print(f"  Re-ranker:  {reranker_status}")
        print(f"  가드레일:   입력(취업 분류) + 출력(길이/표현 검증)")
        print(f"  검색 방식:  ChromaDB top-10 → Re-ranker top-3")
        print(f"  출처 표시:  [출처: 회사명 - 섹션명]")
        print(f"\n  [동작 흐름]")
        print(f"  질문 → 가드레일 → ChromaDB 검색 → Re-ranking → 프롬프트 주입 → GPT 생성 → 출력 검증")
        print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인 루프
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    pipeline = RAGPipeline()

    print("┌──────────────────────────────────────────────────────┐")
    print("│      RAG 파이프라인 취업 챗봇 (4주차) - juwon       │")
    print("├──────────────────────────────────────────────────────┤")
    print("│  load <경로> [전략] [청크크기]  → 문서 로드         │")
    print("│  info                           → 파이프라인 정보   │")
    print("│  reset / usage / quit                                │")
    print("└──────────────────────────────────────────────────────┘\n")

    # 기본 문서 자동 로드
    default_doc = Path(__file__).parent / "job_postings.md"
    if default_doc.exists():
        count = pipeline.load_document(str(default_doc), strategy="paragraph", chunk_size=400)
        print(f"\n  기본 문서 로드 완료: {default_doc.name} ({count}개 청크)\n")

    while True:
        try:
            user_input = input("나: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            pipeline.print_usage()
            break

        if not user_input:
            continue

        tokens = user_input.split()
        cmd = tokens[0].lower()

        if cmd == "quit":
            pipeline.print_usage()
            print("종료합니다.")
            break

        elif cmd == "reset":
            pipeline.reset()

        elif cmd == "usage":
            pipeline.print_usage()

        elif cmd == "info":
            pipeline.print_pipeline_info()

        elif cmd == "load":
            if len(tokens) < 2:
                print("  사용법: load <파일경로> [fixed|separator|paragraph] [청크크기]\n")
                continue
            path = tokens[1]
            if not Path(path).exists():
                alt = Path(__file__).parent / path
                if alt.exists():
                    path = str(alt)
            strategy = tokens[2].lower() if len(tokens) >= 3 else "paragraph"
            chunk_size = int(tokens[3]) if len(tokens) >= 4 else 400
            try:
                count = pipeline.load_document(path, strategy, chunk_size)
                print(f"  로드 완료: {Path(path).name} | {count}개 청크\n")
            except Exception as e:
                print(f"  오류: {e}\n")

        else:
            print()
            pipeline.ask(user_input)
            print()


if __name__ == "__main__":
    main()
