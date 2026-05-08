# 2주차: Chunking - mg

## 프로젝트 개요

**"Why Chunking?"** - 청킹의 필요성을 직접 비교 체험할 수 있는 인터랙티브 데모.
동일한 문서와 질문에 대해 "청킹 없이(Raw)" vs "청킹 적용(Chunked)" 두 방식의 결과를 나란히 비교하여, 토큰 사용량/비용/응답시간 차이를 시각적으로 보여준다.

## 기술 스택

| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| Frontend | Next.js 16 (App Router) | Vite + React | 1주차와 동일한 스택 유지, SSR 지원 |
| Styling | Tailwind CSS v4 | styled-components | 유틸리티 기반으로 빠른 UI 개발 |
| Backend | FastAPI (Python) | Express.js | OpenAI SDK + LangChain 생태계 활용 |
| Chunking | LangChain RecursiveCharacterTextSplitter | 직접 구현 | 검증된 라이브러리, 다양한 구분자 우선순위 지원 |
| Embedding | OpenAI text-embedding-3-small | sentence-transformers | API 호출로 간편, 별도 GPU 불필요 |
| Vector Search | numpy cosine similarity (인메모리) | ChromaDB, Pinecone | 데모 목적으로 외부 DB 없이 단순하게 구현 |
| LLM | GPT-4o / GPT-4o-mini | Claude, Gemini | 1주차 연장선, 비용 계산 용이 |
| Token Counter | tiktoken | 수동 계산 | OpenAI 공식 토크나이저, 정확한 토큰 수 |

## 핵심 구현

### 아키텍처

```
Frontend (Next.js :3000)
  ├─ DocumentInput  ─── 샘플 선택 탭 / 직접 입력 탭
  ├─ QuestionInput  ─── 질문 + "비교 시작" 버튼
  ├─ StatsBar       ─── 바 차트로 토큰/시간/비용 비교
  ├─ ComparePanel   ─── Side-by-Side 답변 비교
  │   ├─ AnswerCard (Raw)     ─── 청킹 없이 결과
  │   └─ AnswerCard (Chunked) ─── 청킹 적용 결과
  └─ ChunkViewer    ─── 청크 블록 시각화 + 골드 하이라이트
          │
          │  POST /api/ask-raw    POST /api/ask-chunked
          ▼
Backend (FastAPI :8000)
  ├─ chunking_service  ─── RecursiveCharacterTextSplitter
  ├─ embedding_service ─── text-embedding-3-small + cosine similarity
  └─ llm_service       ─── GPT 호출 + 비용/시간 측정
```

### 주요 로직

1. **Raw 방식**: 전체 문서를 LLM 컨텍스트에 그대로 넣어 질문 → 토큰 많이 소모, 비용 높음
2. **Chunked 방식**: 문서를 500자 단위로 분할 → 임베딩 → 질문과 유사도 검색 → 상위 3개 청크만 LLM에 전달 → 토큰 절감
3. **동시 비교**: `Promise.all`로 두 API를 동시 호출하여 결과를 나란히 표시

### 코드 실행 방법

**사전 요구사항**: Python 3.10+, Node.js 18+, OpenAI API Key

```bash
# 1. Backend
cd week02-chunking/mg/backend
pip install -r requirements.txt
# .env 파일에 OPENAI_API_KEY 설정
uvicorn main:app --reload --port 8000

# 2. Frontend (새 터미널)
cd week02-chunking/mg/frontend
npm install
npm run dev
# http://localhost:3000 접속
```

## WHY (의사결정 기록)

1. **Q**: 왜 벡터 DB(ChromaDB 등) 대신 numpy 인메모리 검색을 선택했는가?
   **A**: 2주차 과제의 목적은 "청킹의 필요성 이해"이다. 외부 의존성을 최소화하여 청킹 → 임베딩 → 검색 → LLM의 흐름 자체에 집중하도록 했다. 매 요청마다 임베딩을 새로 생성하므로 영속 저장이 불필요하다.

2. **Q**: 왜 스트리밍 대신 비스트리밍 방식을 사용했는가?
   **A**: 두 결과를 동시에 비교해야 하므로, 완료된 응답의 토큰/시간/비용 통계를 정확히 계산한 뒤 한번에 보여주는 것이 비교 목적에 적합하다.

3. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**: 청크 크기(chunk_size)와 오버랩(chunk_overlap)을 사용자가 슬라이더로 조절할 수 있게 하면 청킹 파라미터의 영향을 더 직관적으로 체험할 수 있을 것이다. 또한 임베딩 모델 비교(small vs large)도 흥미로운 확장이 될 수 있다.

## 트러블슈팅 로그

| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | Windows에서 pip 명령어 미인식 | `pip: command not found` | Python Scripts 폴더가 PATH에 없음 | `py -m pip install` 사용 |
| 2 | Tailwind v4에서 테마 설정 | `tailwind.config.ts` 미동작 | v4는 CSS 기반 `@theme inline` 사용 | `globals.css`에서 `@theme inline {}` 블록으로 색상/폰트 정의 |
| 3 | 긴 문서 토큰 초과 | `maximum context length exceeded` | 전체 문서를 컨텍스트에 넣으면 모델 한도 초과 | try-except로 에러 캐치 후 토큰 초과 안내 메시지 반환 (이것이 청킹이 필요한 이유) |

## 회고

- **이번 주 배운 점**: 청킹 없이 전체 문서를 LLM에 넣으면 토큰 낭비가 심하고, 관련 없는 내용까지 포함되어 답변 품질도 떨어질 수 있다. RecursiveCharacterTextSplitter의 구분자 우선순위 개념, 임베딩 기반 유사도 검색의 원리, 그리고 이 과정이 RAG의 기초가 된다는 점을 체감했다.
- **다음 주 준비할 것**: 벡터 DB(ChromaDB, Pinecone 등)를 활용한 영속적 임베딩 저장, 검색 품질 개선(리랭킹, 하이브리드 검색) 등 RAG 파이프라인 고도화.
