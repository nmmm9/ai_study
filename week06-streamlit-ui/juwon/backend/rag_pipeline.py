"""
5주차: Advanced RAG
4주차(기본 RAG) 업그레이드:

1. Multi-Query      - 질문을 GPT로 여러 변형으로 확장 → 검색 커버리지 향상
2. Hybrid Search    - BM25(키워드) + Vector(의미) → RRF(Reciprocal Rank Fusion)로 결합
3. Metadata Filtering - 회사명 자동 감지 → ChromaDB 필터 적용
4. Parent-Child Chunking - 소형 청크(200자) 검색 + 대형 청크(600자) 컨텍스트 전달
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv
from openai import OpenAI

# 현재 폴더 .env → 없으면 week04 폴더 .env 순서로 탐색
_env = Path(__file__).resolve().parent / ".env"
if not _env.exists():
    _env = Path(__file__).resolve().parent.parent.parent / "week04-rag-pipeline" / "juwon" / ".env"
load_dotenv(_env)


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
    separator  - 구분자 기반 재귀 분할
    paragraph  - 빈 줄 기준 단락 분할 (취업공고에 적합)
    """

    STRATEGIES = ("fixed", "separator", "paragraph")

    def __init__(self, strategy: str = "paragraph", chunk_size: int = 200, overlap: int = 50):
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
# 3. 청크 메타데이터 (5주차: parent_text 추가)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ChunkWithMeta:
    """청크 텍스트 + 출처 정보 + 부모 청크 텍스트"""
    text: str
    source: str
    company: str
    section: str
    chunk_id: int
    parent_text: str = ""   # Parent-Child: 검색은 text(200자), 컨텍스트는 parent_text(600자)


def extract_metadata_with_parents(
    text: str,
    source_path: str,
    child_size: int = 200,
    parent_size: int = 600,
) -> list[ChunkWithMeta]:
    """
    Parent-Child Chunking:
    1. text를 parent_size(600자) 단락으로 분할 → parent 청크
    2. 각 parent를 child_size(200자)로 재분할 → child 청크
    3. 각 child에 parent_text 저장 → GPT에게 더 넓은 맥락 전달

    취업공고 메타데이터 추출:
      ## 공고 N: 회사명 — 직함  →  회사 구분
      ### 섹션명               →  섹션 구분
    """
    source = Path(source_path).name
    result = []
    chunk_id = 0
    current_company = ""
    current_section = ""

    parent_chunker = TextChunker(strategy="paragraph", chunk_size=parent_size)
    child_chunker = TextChunker(strategy="paragraph", chunk_size=child_size)

    parents = parent_chunker.chunk(text)

    for parent_text in parents:
        # parent 텍스트에서 회사명/섹션 갱신
        c_match = re.search(r"##\s+공고\s+\d+:\s+(.+?)\s+[—\-]", parent_text)
        s_match = re.search(r"###\s+(.+?)(?:\n|$)", parent_text)
        if c_match:
            current_company = c_match.group(1).strip()
        if s_match:
            current_section = s_match.group(1).strip()

        children = child_chunker.chunk(parent_text)
        for child_text in children:
            # child 텍스트에서도 회사명/섹션 갱신
            cc_match = re.search(r"##\s+공고\s+\d+:\s+(.+?)\s+[—\-]", child_text)
            cs_match = re.search(r"###\s+(.+?)(?:\n|$)", child_text)
            if cc_match:
                current_company = cc_match.group(1).strip()
            if cs_match:
                current_section = cs_match.group(1).strip()

            result.append(ChunkWithMeta(
                text=child_text,
                source=source,
                company=current_company,
                section=current_section,
                chunk_id=chunk_id,
                parent_text=parent_text,
            ))
            chunk_id += 1

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 벡터 저장소: ChromaDB + BM25 Hybrid Search (5주차 핵심)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import chromadb
from chromadb.utils import embedding_functions

EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CHROMA_DIR = None  # 메모리 모드 (배포 환경 호환 - @st.cache_resource로 유지)


class VectorStore:
    """
    Hybrid Search 벡터 저장소.

    [검색 방식]
    - Vector Search: ChromaDB 코사인 유사도 (의미 기반)
    - BM25 Search:   키워드 빈도 기반 (정확한 단어 매칭)
    - Hybrid:        두 결과를 RRF(Reciprocal Rank Fusion)로 결합

    [Metadata Filtering]
    - 쿼리에서 회사명 자동 감지
    - 감지 시 해당 회사 청크만 검색 → 정밀도 향상
    """

    COLLECTION_NAME = "job_postings_v2"

    def __init__(self, persist_dir: str = None):
        self.client = chromadb.EphemeralClient()  # 메모리 모드 (배포 환경 호환)
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )
        self._bm25 = None
        self._bm25_docs: list[tuple] = []  # (chunk_id_str, doc_text, metadata)
        self._companies: set[str] = set()

    @property
    def is_built(self) -> bool:
        return self.collection.count() > 0

    # ── 인덱스 구축 ────────────────────────────────────────────

    def build(self, chunks_meta: list[ChunkWithMeta]) -> None:
        """청크를 임베딩하여 ChromaDB에 저장 + BM25 인덱스 구축"""
        self.client.delete_collection(self.COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )

        batch_size = 50
        for i in range(0, len(chunks_meta), batch_size):
            batch = chunks_meta[i:i + batch_size]
            # 회사명 + 섹션 접두어 붙여서 임베딩 품질 향상
            docs = [
                f"{c.company} - {c.section}:\n{c.text}" if c.company else c.text
                for c in batch
            ]
            self.collection.add(
                documents=docs,
                metadatas=[{
                    "company": c.company,
                    "section": c.section,
                    "source": c.source,
                    "parent_text": c.parent_text,
                } for c in batch],
                ids=[f"chunk_{c.chunk_id}" for c in batch],
            )

        print(f"  [ChromaDB] {self.collection.count()}개 청크 저장 완료 (메모리)")
        self._load_bm25_from_db()

    def add_chunks(self, chunks_meta: list[ChunkWithMeta]) -> None:
        """기존 인덱스에 청크 추가 (전체 재빌드 없이 빠르게)"""
        if not chunks_meta:
            return
        # 기존 chunk_id와 겹치지 않게 offset 계산
        existing_count = self.collection.count()
        batch_size = 50
        for i in range(0, len(chunks_meta), batch_size):
            batch = chunks_meta[i:i + batch_size]
            docs = [
                f"{c.company} - {c.section}:\n{c.text}" if c.company else c.text
                for c in batch
            ]
            self.collection.add(
                documents=docs,
                metadatas=[{
                    "company": c.company,
                    "section": c.section,
                    "source": c.source,
                    "parent_text": c.parent_text,
                } for c in batch],
                ids=[f"chunk_{existing_count + c.chunk_id}" for c in batch],
            )
        print(f"  [ChromaDB] {len(chunks_meta)}개 청크 추가 완료 (총 {self.collection.count()}개)")
        self._load_bm25_from_db()  # BM25 재구축 (빠름)

    def _load_bm25_from_db(self) -> None:
        """ChromaDB에 저장된 문서로 BM25 인덱스 (재)구축"""
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            print("  [BM25] rank_bm25 미설치 → pip install rank-bm25")
            return

        result = self.collection.get(include=["documents", "metadatas"])
        self._bm25_docs = list(zip(result["ids"], result["documents"], result["metadatas"]))
        self._companies = {m.get("company", "") for m in result["metadatas"] if m.get("company")}

        tokenized = [doc.split() for _, doc, _ in self._bm25_docs]
        self._bm25 = BM25Okapi(tokenized)
        print(f"  [BM25] 인덱스 구축 완료 ({len(self._bm25_docs)}개 문서, 회사: {len(self._companies)}개)")

    # ── 회사명 감지 (Metadata Filtering) ───────────────────────

    def detect_company(self, query: str) -> str | None:
        """쿼리에서 회사명 자동 감지"""
        for company in self._companies:
            if company and company in query:
                return company
        return None

    # ── 개별 검색 ──────────────────────────────────────────────

    def _vector_search(
        self, query: str, top_k: int = 20, company_filter: str | None = None
    ) -> list[tuple[float, ChunkWithMeta]]:
        """ChromaDB 벡터 검색 (코사인 유사도)"""
        if not self.is_built:
            return []

        k = min(top_k, self.collection.count())
        kwargs: dict = {
            "query_texts": [query],
            "n_results": k,
            "include": ["documents", "metadatas", "distances"],
        }
        if company_filter:
            kwargs["where"] = {"company": {"$eq": company_filter}}

        results = self.collection.query(**kwargs)

        output = []
        for doc, meta, dist, cid in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
            results["ids"][0],
        ):
            cm = ChunkWithMeta(
                text=doc,
                source=meta.get("source", ""),
                company=meta.get("company", ""),
                section=meta.get("section", ""),
                chunk_id=int(cid.split("_")[1]),
                parent_text=meta.get("parent_text", ""),
            )
            output.append((1.0 - dist, cm))
        return output

    def _bm25_search(
        self, query: str, top_k: int = 20, company_filter: str | None = None
    ) -> list[tuple[float, ChunkWithMeta]]:
        """BM25 키워드 검색"""
        if self._bm25 is None:
            return []

        scores = self._bm25.get_scores(query.split())
        indexed = list(enumerate(scores))

        if company_filter:
            indexed = [
                (i, s) for i, s in indexed
                if i < len(self._bm25_docs) and self._bm25_docs[i][2].get("company") == company_filter
            ]

        ranked = sorted(indexed, key=lambda x: x[1], reverse=True)[:top_k]

        output = []
        for idx, score in ranked:
            cid, doc, meta = self._bm25_docs[idx]
            cm = ChunkWithMeta(
                text=doc,
                source=meta.get("source", ""),
                company=meta.get("company", ""),
                section=meta.get("section", ""),
                chunk_id=int(cid.split("_")[1]),
                parent_text=meta.get("parent_text", ""),
            )
            output.append((float(score), cm))
        return output

    # ── Hybrid Search (RRF) ────────────────────────────────────

    def search_hybrid(
        self,
        query: str,
        top_k: int = 10,
        company_filter: str | None = None,
    ) -> list[tuple[float, ChunkWithMeta]]:
        """
        Hybrid Search: BM25 + Vector 결합 (RRF)

        RRF (Reciprocal Rank Fusion):
          score(doc) = Σ 1 / (K + rank)
          각 검색 방법의 순위를 점수로 변환하여 합산.
          K=60은 표준 파라미터 (상위권 문서에 가중치 집중).
        """
        vector_results = self._vector_search(query, top_k=20, company_filter=company_filter)
        bm25_results = self._bm25_search(query, top_k=20, company_filter=company_filter)

        K = 60
        rrf_scores: dict[int, float] = {}
        chunk_map: dict[int, ChunkWithMeta] = {}

        for rank, (_, cm) in enumerate(vector_results):
            rrf_scores[cm.chunk_id] = rrf_scores.get(cm.chunk_id, 0) + 1 / (K + rank + 1)
            chunk_map[cm.chunk_id] = cm

        for rank, (_, cm) in enumerate(bm25_results):
            rrf_scores[cm.chunk_id] = rrf_scores.get(cm.chunk_id, 0) + 1 / (K + rank + 1)
            if cm.chunk_id not in chunk_map:
                chunk_map[cm.chunk_id] = cm

        ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(score, chunk_map[cid]) for cid, score in ranked]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. Multi-Query Expander (5주차 신규)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MultiQueryExpander:
    """
    GPT를 활용한 쿼리 확장.

    하나의 질문을 여러 표현으로 확장하여 검색 커버리지를 높임.
    예) "카카오 자격요건" →
        "카카오 백엔드 개발자 필수 기술"
        "카카오 채용 지원 조건"
        "카카오 개발자 기술 스택 요구사항"
    """

    _SYSTEM = (
        "당신은 검색 쿼리 확장 전문가입니다.\n"
        "주어진 질문을 다른 표현으로 변형하여 더 다양한 검색 결과를 얻을 수 있게 합니다.\n"
        "반드시 JSON 배열로만 응답하세요. 예: [\"쿼리1\", \"쿼리2\", \"쿼리3\"]"
    )

    def __init__(self, client: OpenAI):
        self.client = client

    def expand(self, query: str, n: int = 3) -> list[str]:
        """
        질문을 n개 변형으로 확장.
        GPT 호출 실패 시 원본 쿼리만 반환.
        """
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=200,
                messages=[
                    {"role": "system", "content": self._SYSTEM},
                    {
                        "role": "user",
                        "content": f"질문: {query}\n위 질문을 {n}가지 다른 표현으로 변형해주세요.",
                    },
                ],
            )
            raw = resp.choices[0].message.content or "[]"
            queries = json.loads(raw)
            expanded = [q for q in queries if isinstance(q, str)][:n]
            return [query] + expanded  # 원본 + 확장 쿼리
        except Exception:
            return [query]  # 실패 시 원본만


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. Re-ranker (4주차)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Reranker:
    """
    Cross-Encoder 기반 2단계 재정렬.

    Bi-Encoder(ChromaDB)는 질문과 청크를 따로 임베딩하기 때문에
    문맥 상호작용이 없어 정밀도가 떨어질 수 있습니다.
    Cross-Encoder는 질문 + 청크를 한 번에 입력하여 직접 관련성 점수를 계산합니다.

    [검색 흐름]
    1단계: Hybrid Search → top-10 후보 빠르게 추출
    2단계: Cross-Encoder → top-10에서 top-3 정밀 선정
    """

    def __init__(self):
        self._model = None
        try:
            from sentence_transformers import CrossEncoder
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
# 7. Guardrails (4주차)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Guardrail:
    """
    입력/출력 가드레일.
    취업 외 질문 차단 + 출력 품질 검증.
    """

    _CLASSIFY_SYSTEM = (
        "당신은 메시지가 '취업/채용/커리어' 관련 질문인지 판단하는 분류기입니다.\n"
        "판단 기준:\n"
        "- 취업, 이직, 채용공고, 자격요건, 연봉, 복리후생, 면접, 직무, 회사, 경력, "
        "  스택, 기술, 지원, 전형, 우대사항, 계약, 인턴, 승무원, 항공, 서비스직, "
        "  공고, 지원자격, 모집, 신입, 공채 → 관련(true)\n"
        "- 연애, 음식, 스포츠, 날씨, 정치, 일상 잡담, 영화, 음악 → 무관(false)\n"
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
            return True

    def check_output(self, answer: str) -> tuple[bool, str]:
        if len(answer.strip()) < 10:
            return False, "답변이 너무 짧습니다. 다시 질문해 주세요."
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
# 8. Advanced RAG 파이프라인 (5주차 핵심)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYSTEM_PROMPT = """당신은 취업 상담 전문 AI 어시스턴트입니다.

[역할]
제공된 취업공고 데이터를 기반으로 구직자에게 정확한 취업 정보를 제공합니다.
IT 개발직, 승무원, 서비스직 등 직종에 관계없이 공고 내용을 기반으로 답변합니다.

[답변 규칙]
1. 반드시 아래에 제공된 [참조 문서] 내용만 근거로 답변하세요.
2. 문서에 없는 내용은 "해당 정보는 제공된 공고에서 확인되지 않습니다"라고 말하세요.
3. 답변 마지막에 참조한 출처를 반드시 표시하세요.
   형식: [출처: 회사명 - 섹션명]
4. 여러 공고를 비교할 때는 각 회사를 명확히 구분하여 설명하세요.
5. 한국어로 답변하세요.

[출처 표시 예시]
대한항공은 영어 회화 능통자(토익 550점 이상)를 요구합니다.
[출처: 대한항공 - 자격 요건]"""


class AdvancedRAGPipeline:
    """
    Advanced RAG 파이프라인 (5주차).

    [4주차 대비 개선사항]
    ┌─────────────────────────────────────────────────────────────┐
    │  4주차                  →  5주차                           │
    │  Vector Search only     →  BM25 + Vector (Hybrid, RRF)    │
    │  단일 쿼리               →  Multi-Query (GPT 확장, 3개)    │
    │  전체 검색               →  Metadata Filtering (회사명)    │
    │  200자 청크 컨텍스트     →  600자 Parent 청크 컨텍스트     │
    └─────────────────────────────────────────────────────────────┘

    [전체 흐름]
    사용자 질문
      ↓
    [Guardrail] 취업 관련 질문인지 GPT로 분류
      ↓ (허용된 경우)
    [Metadata Filtering] 쿼리에서 회사명 감지
      ↓
    [Multi-Query] GPT로 질문 3개 확장
      ↓
    [Hybrid Search] 각 쿼리 BM25+Vector 검색 → RRF 결합
      ↓
    [Re-ranker] Cross-Encoder로 top-3 정밀 선정
      ↓
    [Prompt] 시스템 + Parent 청크 컨텍스트 + 대화 히스토리
      ↓
    [Generator] GPT-4o-mini 스트리밍 답변 생성
      ↓
    [Output Guard] 출력 검증
      ↓
    최종 답변 + [출처: 회사명 - 섹션명]
    """

    MODEL = "gpt-4o-mini"
    MAX_HISTORY_TURNS = 10
    MAX_RESPONSE_TOKENS = 1024

    def __init__(self):
        self.client = OpenAI()
        self.store = VectorStore()
        self.expander = MultiQueryExpander(self.client)
        self.reranker = Reranker()
        self.guardrail = Guardrail(self.client)
        self.history: list[dict] = []
        self.token_usage = {"input": 0, "output": 0}
        self._last_citations: list[str] = []
        self._last_queries: list[str] = []      # 확장된 쿼리 목록
        self._last_company_filter: str | None = None

    # ── 문서 로드 ────────────────────────────────────────────────

    def load_document(
        self,
        path: str,
        child_size: int = 200,
        parent_size: int = 600,
    ) -> int:
        """문서 로드 → Parent-Child 청킹 → 임베딩 인덱스 구축"""
        raw = DocumentLoader.load(path)
        chunks_meta = extract_metadata_with_parents(
            raw, path, child_size=child_size, parent_size=parent_size
        )
        print(f"  [로드] {Path(path).name} | child={child_size}자 / parent={parent_size}자 | 청크: {len(chunks_meta)}개")
        print("  [ChromaDB] 벡터 인덱스 구축 중...")
        self.store.build(chunks_meta)
        return len(chunks_meta)

    # ── 검색 (Hybrid + Multi-Query + Metadata Filtering) ─────────

    def _retrieve(self, query: str) -> list[tuple[float, ChunkWithMeta]]:
        """
        1. 회사명 감지 (Metadata Filtering)
        2. Multi-Query 확장
        3. 각 쿼리 Hybrid Search (BM25 + Vector)
        4. 결과 합산 후 Re-ranking
        """
        # Metadata Filtering: 회사명 감지
        company_filter = self.store.detect_company(query)
        self._last_company_filter = company_filter

        # Multi-Query 확장
        queries = self.expander.expand(query, n=3)
        self._last_queries = queries

        if company_filter:
            print(f"  [필터] 회사명 감지: {company_filter}")
        print(f"  [Multi-Query] 쿼리 {len(queries)}개: {queries}")

        # 각 쿼리로 Hybrid Search → RRF로 결과 합산
        K = 60
        rrf_scores: dict[int, float] = {}
        chunk_map: dict[int, ChunkWithMeta] = {}

        for q_rank, q in enumerate(queries):
            results = self.store.search_hybrid(q, top_k=10, company_filter=company_filter)
            for doc_rank, (_, cm) in enumerate(results):
                # 쿼리 순서 가중치: 원본 쿼리(q_rank=0)에 더 높은 가중치
                weight = 1.0 / (q_rank + 1)
                rrf_score = weight / (K + doc_rank + 1)
                rrf_scores[cm.chunk_id] = rrf_scores.get(cm.chunk_id, 0) + rrf_score
                chunk_map[cm.chunk_id] = cm

        # 중복 제거 후 상위 10개 추출
        ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        candidates = [(rrf_scores[cid], chunk_map[cid]) for cid, _ in ranked]

        # Re-ranking: top-10 → top-3
        return self.reranker.rerank(query, candidates, top_k=3)

    # ── 컨텍스트 구성 (Parent-Child: 600자 parent 사용) ───────────

    def _build_context(self, results: list[tuple[float, ChunkWithMeta]]) -> str:
        """
        Parent-Child Chunking:
        - 검색: child 청크(200자)로 정밀하게 찾음
        - 컨텍스트: parent 청크(600자)를 GPT에게 전달 → 더 넓은 맥락
        """
        if not results:
            return ""

        self._last_citations = []
        parts = []

        for i, (score, meta) in enumerate(results, 1):
            citation = f"{meta.company} - {meta.section}" if meta.company else meta.source
            self._last_citations.append(citation)
            # Parent-Child: parent_text가 있으면 parent 사용, 없으면 child text 사용
            context_text = meta.parent_text if meta.parent_text else meta.text
            parts.append(
                f"[참조 {i}] 출처: {citation} (점수: {score:.3f})\n{context_text}"
            )

        return "[참조 문서]\n\n" + "\n\n---\n\n".join(parts)

    def _build_messages(self, context: str = "") -> list[dict]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "system", "content": context})
        max_msgs = self.MAX_HISTORY_TURNS * 2
        messages.extend(self.history[-max_msgs:])
        return messages

    # ── Streamlit용 스트리밍 제너레이터 ──────────────────────────

    def ask_stream(self, user_input: str):
        """
        Streamlit용 Advanced RAG 파이프라인 (제너레이터 방식).

        yield 타입:
          {"type": "status",   "text": "..."}
          {"type": "blocked",  "text": "..."}
          {"type": "queries",  "queries": [...], "company_filter": ...}
          {"type": "citations","citations": [...]}
          {"type": "text",     "text": "..."}
          {"type": "done",     "tokens": {...}}
        """
        # ① 입력 가드레일
        yield {"type": "status", "text": "입력 검증 중..."}
        if not self.guardrail.check_input(user_input):
            yield {"type": "blocked", "text": self.guardrail.OFF_TOPIC_MSG}
            return

        # ② Metadata Filtering + Multi-Query + Hybrid Search + Re-ranking
        yield {"type": "status", "text": "쿼리 확장 및 검색 중..."}
        results = self._retrieve(user_input)
        yield {
            "type": "queries",
            "queries": self._last_queries,
            "company_filter": self._last_company_filter,
        }

        # ③ 컨텍스트 구성 (Parent-Child)
        context = self._build_context(results)
        yield {"type": "citations", "citations": list(self._last_citations)}

        # ④ 히스토리 추가
        self.history.append({"role": "user", "content": user_input})

        # ⑤ 스트리밍 생성
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

        # ⑥ 출력 가드레일
        valid, warning = self.guardrail.check_output(reply)

        # ⑦ 저장
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

    def print_pipeline_info(self):
        reranker_status = "Cross-Encoder (mmarco-mMiniLMv2)" if self.reranker._model else "미사용"
        bm25_status = "BM25Okapi" if self.store._bm25 else "미설치 (rank_bm25 필요)"
        print("\n━━━━ Advanced RAG 파이프라인 (5주차) ━━━━")
        print(f"  LLM 모델:         {self.MODEL}")
        print(f"  임베딩:           {EMBED_MODEL}")
        print(f"  Vector DB:        ChromaDB (메모리 모드)")
        print(f"  BM25:             {bm25_status}")
        print(f"  Hybrid Search:    BM25 + Vector (RRF K=60)")
        print(f"  Multi-Query:      GPT 쿼리 확장 (원본 + 3개)")
        print(f"  Metadata Filter:  회사명 자동 감지")
        print(f"  Parent-Child:     child=200자 검색 / parent=600자 컨텍스트")
        print(f"  Re-ranker:        {reranker_status}")
        print(f"  가드레일:         입력(취업 분류) + 출력(길이/표현 검증)")
        print(f"  회사 수:          {len(self.store._companies)}개")
        print()
