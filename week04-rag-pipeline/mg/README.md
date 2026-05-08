# 4주차: RAG Pipeline - mg

## 프로젝트 개요

**기본 RAG 파이프라인 & 문서 기반 챗봇** - 문서를 청킹/임베딩하여 ChromaDB에 저장하고, 질문 시 벡터 검색 후 LLM이 답변을 생성하는 기본 RAG(Retrieval-Augmented Generation) 파이프라인 데모. 단일 Q&A와 멀티턴 챗봇 두 가지 인터페이스를 제공한다.

## 기술 스택

| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| Backend | FastAPI (Python) | Flask, Express | async 지원, 자동 API 문서, week02/03과 동일 스택 |
| Frontend | Next.js 16 (App Router) + Tailwind v4 | Vite + React | week02/03과 동일 스택 유지, SSR 지원 |
| Vector DB | ChromaDB (PersistentClient) | Pinecone, Weaviate | week03에서 검증 완료, 로컬 파일 기반, 별도 서버 불필요 |
| Embedding | OpenAI text-embedding-3-small | text-embedding-3-large | 1536차원으로 데모에 충분, 비용 효율적 ($0.02/1M tokens) |
| LLM | GPT-4o-mini (기본) / GPT-4o | Claude, Gemini | 비용 효율적 ($0.15/$0.60 per 1M tokens), 충분한 성능 |
| Chunking | LangChain RecursiveCharacterTextSplitter | 직접 구현 | week02에서 검증된 라이브러리, 구분자 우선순위 지원 |
| Token Counter | tiktoken | 수동 계산 | OpenAI 공식 토크나이저, 정확한 토큰/비용 계산 |

## 핵심 구현

### 아키텍처

```
Frontend (Next.js :3000)
  ├─ DocumentInput    ─── 샘플 선택 / 직접 입력
  ├─ CollectionPanel  ─── 임베딩 저장 + 컬렉션 관리
  ├─ QuestionInput    ─── 단일 질문 입력
  ├─ PipelineViz      ─── 파이프라인 3단계 시각화
  ├─ AnswerCard       ─── 답변 + 소스 + 비용/시간
  └─ ChatPanel        ─── 멀티턴 RAG 챗봇
          │
          │  POST /api/rag (단일 Q&A)
          │  POST /api/chat (멀티턴 챗봇)
          ▼
Backend (FastAPI :8000)
  ├─ rag_pipeline     ─── RAG 오케스트레이션 (run_rag, run_chat_rag)
  ├─ embedding_service ── text-embedding-3-small
  ├─ vector_store     ─── ChromaDB PersistentClient
  ├─ chunking_service ─── RecursiveCharacterTextSplitter
  └─ llm_service      ─── GPT 호출 + 비용/시간 측정
```

### 주요 로직

**1. 기본 RAG Pipeline (단일 Q&A)**

```
질문 → [1. Embed] 질문 임베딩 → [2. Search] ChromaDB 벡터 검색 (top_k) → [3. Generate] LLM 답변 생성
```

- 질문을 임베딩하여 ChromaDB에서 유사한 청크를 검색
- 검색된 청크를 컨텍스트로 LLM에 전달하여 답변 생성
- 각 단계의 소요 시간, 비용, 토큰 수를 측정하여 반환

**2. RAG 챗봇 (멀티턴)**

- 기본 RAG와 동일한 검색 파이프라인 사용
- 추가로 대화 히스토리(최근 10턴)를 LLM 프롬프트에 포함
- `ask_with_messages()`로 이전 대화 맥락을 유지하며 답변 생성
- 시스템 프롬프트에 검색된 문서 컨텍스트를 삽입

**3. 문서 임베딩 저장**

- 문서 → 청킹(500자, 50자 오버랩) → OpenAI 임베딩 → ChromaDB 영구 저장
- 컬렉션명: `{sample_id}-{chunk_size}-{overlap}` 또는 `custom-{hash}-{chunk_size}-{overlap}`
- 이미 존재하는 컬렉션은 재임베딩하지 않고 기존 데이터 반환

### 코드 실행 방법

**사전 요구사항**: Python 3.10+, Node.js 18+, OpenAI API Key

```bash
# 1. Backend
cd week04-rag-pipeline/mg/backend
pip install -r requirements.txt
# .env 파일에 OPENAI_API_KEY 설정
py -m uvicorn main:app --reload --port 8000

# 2. Frontend (새 터미널)
cd week04-rag-pipeline/mg/frontend
npm install
npm run dev
# http://localhost:3000 접속
```

### 프로젝트 구조

```
mg/
├── backend/
│   ├── main.py                    # FastAPI 7개 엔드포인트
│   ├── requirements.txt
│   ├── .env                       # OPENAI_API_KEY
│   ├── chroma_data/               # ChromaDB 영구 저장소
│   ├── data/
│   │   └── samples.py             # 샘플 문서 2종 (AI 개론, Python 가이드)
│   ├── models/
│   │   └── schemas.py             # Pydantic 요청/응답 스키마
│   └── services/
│       ├── chunking_service.py    # 텍스트 청킹 (week02 재활용)
│       ├── embedding_service.py   # OpenAI 임베딩 호출
│       ├── llm_service.py         # GPT 호출 + 비용 계산
│       ├── rag_pipeline.py        # RAG 오케스트레이션 (단일 Q&A + 챗봇)
│       └── vector_store.py        # ChromaDB 래퍼
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── globals.css        # Midnight Gold 테마 (Tailwind v4)
│       │   ├── layout.tsx
│       │   └── page.tsx           # 메인 페이지
│       ├── types/
│       │   └── rag.ts             # TypeScript 타입 정의
│       ├── hooks/
│       │   └── useRagPipeline.ts  # 상태 관리 훅
│       └── components/
│           ├── DocumentInput.tsx   # 문서 입력/샘플 선택
│           ├── CollectionPanel.tsx # 임베딩 저장 + 컬렉션 관리
│           ├── QuestionInput.tsx   # 단일 질문 입력
│           ├── PipelineViz.tsx     # 파이프라인 단계 시각화
│           ├── AnswerCard.tsx      # 답변 + 소스 + 타이밍
│           └── ChatPanel.tsx       # 멀티턴 RAG 챗봇
└── presentation.html               # 발표자료 (18슬라이드)
```

### API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/samples` | 샘플 문서 목록 |
| GET | `/api/samples/{id}` | 샘플 문서 내용 |
| POST | `/api/embed` | 문서 → 청킹 → 임베딩 → ChromaDB 저장 |
| GET | `/api/collections` | 저장된 컬렉션 목록 |
| DELETE | `/api/collections/{name}` | 컬렉션 삭제 |
| POST | `/api/rag` | 단일 RAG Q&A (질문 → 검색 → 답변) |
| POST | `/api/chat` | 멀티턴 RAG 챗봇 (대화 히스토리 포함) |

## WHY (의사결정 기록)

1. **Q**: 왜 Advanced RAG(HyDE, Reranking)를 포함하지 않았는가?
   **A**: 4주차의 목적은 "기본 RAG 파이프라인의 전체 흐름 이해"이다. Embed → Search → Generate의 기본 흐름을 먼저 확실히 이해한 뒤, 5주차에서 HyDE, Reranking, GraphRAG 등 고급 기법을 다룬다. 한번에 모든 것을 넣으면 핵심 개념이 흐려진다.

2. **Q**: 왜 단일 Q&A와 챗봇을 둘 다 구현했는가?
   **A**: 단일 Q&A로 RAG 파이프라인의 기본 흐름(embed → search → generate)을 명확히 보여주고, 챗봇으로 RAG의 실제 활용 형태를 체험할 수 있게 했다. 챗봇은 대화 히스토리를 LLM 프롬프트에 추가하는 것뿐이므로 RAG 파이프라인 자체는 동일하다.

3. **Q**: 왜 대화 히스토리를 10턴으로 제한했는가?
   **A**: LLM의 컨텍스트 윈도우 한도와 비용을 고려했다. 검색된 문서 컨텍스트 + 대화 히스토리 + 현재 질문이 모두 프롬프트에 들어가므로, 히스토리가 너무 길면 토큰 초과 위험이 있다. 10턴이면 대부분의 대화에서 충분한 맥락을 유지할 수 있다.

4. **Q**: 왜 `ask_with_context()`와 `ask_with_messages()`를 분리했는가?
   **A**: 단일 Q&A는 시스템 프롬프트 + 사용자 질문만 필요하므로 `ask_with_context()`가 간결하다. 챗봇은 이전 대화 히스토리를 messages 배열로 구성해야 하므로 `ask_with_messages()`가 필요하다. 두 함수를 분리하여 각 용도에 맞게 사용한다.

## 트러블슈팅 로그

| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | 챗봇 엔드포인트 500 에러 | `ask_with_messages is not defined` | llm_service.py에 `ask_with_messages()` 함수가 없었음 | 기존 `ask_with_context()`를 참고하여 messages 배열을 직접 받는 새 함수 추가 |
| 2 | 프론트엔드 빌드 실패 | `Module not found: ComparePanel` | week03에서 복사한 page.tsx가 삭제된 컴포넌트를 import | 불필요한 import 제거, 새 구조에 맞게 page.tsx 재작성 |
| 3 | 발표자료 슬라이드 전환 어색 | CSS transition 미적용 | `display: none` ↔ `display: flex` 토글 시 opacity transition 무시됨 | 모든 슬라이드를 항상 `display: flex`로 유지하고 `opacity + pointer-events`로 전환 |

## 회고

- 이번 주 배운 점:
  - RAG 파이프라인의 핵심은 단 3단계(Embed → Search → Generate)로 구성되며, 각 단계가 명확히 분리되어야 유지보수와 확장이 용이하다
  - 멀티턴 챗봇은 RAG 파이프라인 자체를 변경하지 않고, LLM 호출 시 대화 히스토리를 프롬프트에 추가하는 것만으로 구현 가능하다
  - 시스템 프롬프트에 "문서에 없는 내용은 답하지 말라"는 지시를 명시하면 할루시네이션을 줄일 수 있다
  - 비용/시간 측정을 파이프라인 각 단계에 넣으면 병목 지점을 쉽게 파악할 수 있다
- 다음 주 준비할 것:
  - Advanced RAG 기법 학습: HyDE(가상 문서 임베딩), Reranking(검색 결과 재정렬), Query Decomposition(질문 분해)
  - 검색 품질 평가 방법 (Hit Rate, MRR, NDCG 등)
