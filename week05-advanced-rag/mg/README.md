# 5주차: Advanced RAG - mg

## 프로젝트 개요

**9가지 RAG 파이프라인 비교 데모** - 동일한 질문에 대해 9가지 RAG 기법을 자유롭게 선택하여 나란히 비교하는 데모. Basic RAG부터 HyDE, Reranking, Hybrid Search, Multi-Query, Self-RAG, CRAG, Adaptive RAG까지 2025~2026년 주요 Advanced RAG 기법을 모두 구현하고, 답변 품질, 소스 선택, 소요 시간, 비용을 실시간으로 비교한다.

## 기술 스택

| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| Backend | FastAPI (Python) | Flask, Express | async 지원, week04와 동일 스택 유지 |
| Frontend | Next.js 16 (App Router) + Tailwind v4 | Vite + React | week04와 동일 스택, SSR 지원 |
| Vector DB | ChromaDB (PersistentClient) | Pinecone, Weaviate | week03~04에서 검증 완료, 로컬 파일 기반 |
| Embedding | OpenAI text-embedding-3-small | text-embedding-3-large | 1536차원으로 데모에 충분, 비용 효율적 |
| LLM | GPT-4o-mini (기본) / GPT-4o | Claude, Gemini | 비용 효율적, 모든 기법에 동일 모델 사용 |
| HyDE | LLM 기반 가상 문서 생성 | 직접 키워드 추출 | 질문-문서 의미 격차를 자연어로 메움 |
| Reranker | LLM 기반 관련성 점수 (0-10) | Cross-Encoder, Cohere API | 외부 모델 의존 제거, 일관된 GPT 스택 |
| BM25 | rank-bm25 라이브러리 | Elasticsearch | 로컬 키워드 검색, 별도 서버 불필요 |
| Chunking | LangChain RecursiveCharacterTextSplitter | 직접 구현 | week02에서 검증된 라이브러리 |

## 핵심 구현

### 아키텍처

```
Frontend (Next.js :3000)
  ├─ DocumentInput     ─── 샘플 선택 / 직접 입력
  ├─ CollectionPanel   ─── 임베딩 저장 + 컬렉션 관리
  ├─ QuestionInput     ─── 질문 입력
  ├─ ModeSelector      ─── Left / Right 모드 선택 (9가지 중 2개)
  └─ CompareView       ─── 선택한 두 모드 나란히 비교
      ├─ PipelineViz   ─── 파이프라인 단계별 시각화 (14가지 색상)
      └─ AnswerCard    ─── 답변 + 모드별 미리보기 (HyDE/Multi-Query/Self-Eval/CRAG/Adaptive)
              │
              │  POST /api/compare (mode_a, mode_b — asyncio.gather 동시 실행)
              ▼
Backend (FastAPI :8000)
  ├─ basic_pipeline      ─── Embed → Search → Generate
  ├─ advanced_pipeline   ─── HyDE / Rerank / Advanced (HyDE+Rerank)
  ├─ hybrid_search       ─── 벡터 + BM25 + RRF 병합
  ├─ multi_query_service ─── 질문 변형 + 다중 검색
  ├─ self_rag_pipeline   ─── 자체 평가 + 재생성
  ├─ crag_pipeline       ─── 검색 품질 교정 + 재검색
  ├─ adaptive_pipeline   ─── 복잡도 분류 → 파이프라인 라우팅
  ├─ hyde_service        ─── 가상 문서 생성
  ├─ reranker_service    ─── LLM 리랭킹 (JSON 점수)
  ├─ vector_store        ─── ChromaDB PersistentClient
  └─ llm_service         ─── GPT 호출 + ask_json, ask_short
```

### 주요 로직 — 9가지 파이프라인

**1. Basic RAG** (기준선)

```
질문 → [Embed] → [Search] top_k=5 → [Generate]
```

**2. HyDE RAG** (의미 격차 해소)

```
질문 → [HyDE 생성] 가상 답변 → [Embed] 가상 문서 임베딩 → [Search] → [Generate]
```

- LLM이 가상 답변(2-3문장)을 생성 → 서술문 형태 벡터로 검색 → 문서와 의미적으로 가까움

**3. Rerank RAG** (정밀도 향상)

```
질문 → [Embed] → [Wide Search] top_k×4=20 → [LLM Rerank] 0-10점 → top_k=5 → [Generate]
```

**4. Advanced RAG** (HyDE + Rerank 결합)

```
질문 → [HyDE] → [Embed] → [Wide Search] ×4 → [Rerank] → [Generate]
```

**5. Hybrid Search** (벡터 + 키워드)

```
질문 → [Embed] + [BM25] 동시 검색 → [RRF 병합] → [Generate]
```

- 벡터 검색(의미)과 BM25 키워드 검색을 결합, Reciprocal Rank Fusion으로 순위 병합
- 의미적으로 유사한 것 + 키워드가 일치하는 것 모두 포착

**6. Multi-Query RAG** (검색 다양성)

```
질문 → [Multi-Query] 3개 변형 생성 → [Embed] 4개 질문 → [Search] 4회 → 중복 제거 → [Generate]
```

- LLM이 원래 질문을 3가지 다른 관점에서 재작성
- 원본 + 변형 4개 각각 검색 → 고유 청크 합산 → 더 다양한 소스 확보

**7. Self-RAG** (자체 평가)

```
질문 → [Judge] 검색 필요성 판단 → [Embed] → [Search] → [Generate] → [Evaluate] 자체 평가 → ([Regenerate])
```

- LLM이 검색 필요 여부를 먼저 판단
- 답변 생성 후 품질 자체 평가 (점수/근거여부/피드백)
- 점수 < 6 또는 근거 부족 시 피드백 반영하여 재생성

**8. CRAG (Corrective RAG)** (검색 품질 교정)

```
질문 → [Embed] → [Search] → [Evaluate] 문서 품질 판단 → (AMBIGUOUS/INCORRECT 시 [Refine] → [Re-search]) → [Generate]
```

- 검색된 문서의 품질을 CORRECT/AMBIGUOUS/INCORRECT로 평가
- 품질 부족 시 쿼리를 수정하여 재검색, 원본+재검색 결과 병합

**9. Adaptive RAG** (자동 라우팅)

```
질문 → [Classify] 복잡도 분류 → 선택된 파이프라인 실행
  SIMPLE → Basic RAG
  MODERATE → Rerank RAG
  COMPLEX → Advanced RAG (HyDE + Rerank)
```

- LLM이 질문 복잡도를 분류하여 적절한 파이프라인을 자동 선택
- 간단한 질문에 불필요한 비용을 절감

### 코드 실행 방법

**사전 요구사항**: Python 3.10+, Node.js 18+, OpenAI API Key

```bash
# 1. Backend
cd week05-advanced-rag/mg/backend
pip install -r requirements.txt
# .env 파일에 OPENAI_API_KEY 설정
py -m uvicorn main:app --reload --port 8000

# 2. Frontend (새 터미널)
cd week05-advanced-rag/mg/frontend
npm install
npm run dev
# http://localhost:3000 접속
```

### 프로젝트 구조

```
mg/
├── backend/
│   ├── main.py                          # FastAPI 엔드포인트 + 9가지 모드 라우팅
│   ├── requirements.txt                 # rank-bm25 추가
│   ├── .env                             # OPENAI_API_KEY
│   ├── data/
│   │   └── samples.py                   # 샘플 문서 2종
│   ├── models/
│   │   └── schemas.py                   # Pydantic 스키마 (mode_a/mode_b, 확장 필드)
│   └── services/
│       ├── basic_pipeline.py            # Basic RAG (3단계)
│       ├── advanced_pipeline.py         # HyDE / Rerank / Advanced (3가지)
│       ├── hybrid_search.py            # 벡터 + BM25 + RRF 병합
│       ├── multi_query_service.py      # 질문 변형 + 다중 검색
│       ├── self_rag_pipeline.py        # 자체 평가 + 재생성
│       ├── crag_pipeline.py            # 검색 품질 교정 + 재검색
│       ├── adaptive_pipeline.py        # 복잡도 분류 → 라우팅
│       ├── hyde_service.py              # 가상 문서 생성
│       ├── reranker_service.py          # LLM 리랭킹 (0-10 점수)
│       ├── llm_service.py              # GPT 호출 + ask_json, ask_short
│       ├── embedding_service.py         # OpenAI 임베딩
│       ├── chunking_service.py          # 텍스트 청킹
│       └── vector_store.py             # ChromaDB 래퍼
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── globals.css              # Midnight Gold 테마
│       │   ├── layout.tsx
│       │   └── page.tsx                 # 메인 (모드 선택 + 비교)
│       ├── types/
│       │   └── rag.ts                   # 9가지 RAG_MODES, 확장 필드
│       ├── hooks/
│       │   └── useAdvancedRag.ts        # modeA/modeB 상태 + compare
│       └── components/
│           ├── DocumentInput.tsx         # 문서 입력/샘플 선택
│           ├── CollectionPanel.tsx       # 임베딩 + 컬렉션 관리
│           ├── QuestionInput.tsx         # 질문 입력
│           ├── CompareView.tsx          # Left vs Right 비교
│           ├── PipelineViz.tsx          # 파이프라인 시각화 (14가지 단계 색상)
│           └── AnswerCard.tsx           # 답변 + 모드별 미리보기
├── README.md
└── presentation.html                    # 발표자료 (21+슬라이드)
```

### API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/samples` | 샘플 문서 목록 |
| GET | `/api/samples/{id}` | 샘플 문서 내용 |
| POST | `/api/embed` | 문서 → 청킹 → 임베딩 → ChromaDB 저장 |
| GET | `/api/collections` | 저장된 컬렉션 목록 |
| DELETE | `/api/collections/{name}` | 컬렉션 삭제 |
| POST | `/api/rag` (mode=basic) | Basic RAG |
| POST | `/api/rag` (mode=hyde) | HyDE RAG |
| POST | `/api/rag` (mode=rerank) | Rerank RAG |
| POST | `/api/rag` (mode=advanced) | Advanced RAG (HyDE + Rerank) |
| POST | `/api/rag` (mode=hybrid) | Hybrid Search (벡터 + BM25) |
| POST | `/api/rag` (mode=multi_query) | Multi-Query RAG |
| POST | `/api/rag` (mode=self_rag) | Self-RAG |
| POST | `/api/rag` (mode=crag) | Corrective RAG |
| POST | `/api/rag` (mode=adaptive) | Adaptive RAG |
| POST | `/api/compare` | 두 모드 동시 실행 비교 (mode_a, mode_b) |

## WHY (의사결정 기록)

1. **Q**: 왜 HyDE를 선택했는가?
   **A**: 질문("Transformer란 무엇인가?")과 문서("Transformer는 2017년 구글이 발표한...")는 문장 형태가 다르다. 질문을 그대로 임베딩하면 의문문 벡터가 되어 서술문 문서와 거리가 멀다. HyDE는 LLM이 가상의 답변을 생성하여 서술문 형태의 벡터로 검색하므로, 문서와 의미적으로 더 가까운 검색이 가능하다.

2. **Q**: 왜 Cross-Encoder나 Cohere API 대신 LLM 리랭커를 사용했는가?
   **A**: 외부 모델이나 API 의존을 줄이기 위해 이미 사용 중인 GPT-4o-mini로 리랭킹을 수행했다. `response_format: json_object`로 구조화된 점수를 받아 파싱이 간결하고, 전체 시스템이 하나의 LLM 스택으로 통일된다.

3. **Q**: 왜 9가지 모드를 모두 구현했는가?
   **A**: 2025~2026년 주요 Advanced RAG 기법을 한 곳에서 비교할 수 있는 데모가 목표다. 각 기법의 장단점(품질/시간/비용)을 동일 조건에서 비교해야 어떤 상황에 어떤 기법이 적합한지 판단할 수 있다. 특히 Self-RAG와 CRAG는 "검색 결과를 평가하고 교정한다"는 2세대 RAG의 핵심 개념을, Adaptive RAG는 "용도에 맞게 자동 선택한다"는 실용적 패턴을 보여준다.

4. **Q**: 왜 Compare 엔드포인트에 mode_a/mode_b를 추가했는가?
   **A**: 기존에는 basic vs advanced 고정이었지만, 9가지 모드 중 아무 2개를 비교할 수 있어야 한다. 예를 들어 HyDE vs Hybrid, Self-RAG vs CRAG 등 다양한 조합의 비교가 가능하다. `asyncio.gather()`로 두 모드를 동시 실행한다.

5. **Q**: 왜 BM25에 rank-bm25 라이브러리를 사용했는가?
   **A**: Elasticsearch 같은 외부 서버 없이 순수 Python으로 BM25 검색을 구현하기 위해서다. ChromaDB에 저장된 문서를 가져와 메모리에서 BM25 인덱싱하므로 별도 인프라가 불필요하다. 데모 규모에서는 충분한 성능이다.

## 트러블슈팅 로그

| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | ChromaDB에서 top_k보다 적은 청크가 있을 때 에러 | `ValueError: n_results > collection count` | 컬렉션에 5개 미만의 청크가 있는데 top_k=5로 검색 | `min(top_k, collection.count())`로 요청 수 제한 |
| 2 | Reranker JSON 파싱 실패 | `json.JSONDecodeError` | LLM이 가끔 JSON 외 텍스트를 포함 | `response_format: json_object` 지정 + fallback으로 원본 순서 유지 |
| 3 | RagResponse에 신규 필드 누락 | 프론트에 self_eval, generated_queries 등 미전달 | Pydantic response_model이 선언되지 않은 필드를 제거 | schemas.py RagResponse에 7개 optional 필드 추가 |

## 회고

- 이번 주 배운 점:
  - HyDE의 핵심은 "질문을 문서처럼 변환"하는 것이다. 질문 임베딩이 아닌 가상 답변 임베딩으로 검색하면 의미 격차가 줄어든다
  - Reranker는 이미 검색된 결과만 재정렬할 수 있다. 초기 검색에서 빠진 좋은 청크는 복구 불가능하므로, 넓은 초기 검색(×4)이 중요하다
  - Self-RAG와 CRAG의 핵심 차이: Self-RAG는 "답변 품질"을 평가하고, CRAG는 "검색된 문서 품질"을 평가한다. 평가 대상이 다르다
  - Adaptive RAG는 모든 질문에 최고급 파이프라인을 돌릴 필요 없다는 실용적 교훈을 준다. 간단한 질문에는 Basic이면 충분하다
  - Hybrid Search의 RRF(Reciprocal Rank Fusion)는 두 검색 방식의 순위를 수학적으로 합산하는 간결한 알고리즘이다
  - asyncio.gather()로 독립적인 파이프라인을 병렬 실행하면 사용자 대기 시간을 줄일 수 있다
- 다음 주 준비할 것:
  - Streamlit을 활용한 인터랙티브 UI 구축
  - 기존 RAG 파이프라인을 Streamlit으로 래핑하는 방법 학습
