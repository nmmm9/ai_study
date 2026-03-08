# 3주차: Embedding & Vector DB - mg

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| Vector DB | ChromaDB (PersistentClient) | Pinecone, Weaviate, Qdrant | 로컬 파일 기반 영속성, pip 설치만으로 사용 가능, 별도 서버 불필요 |
| 임베딩 모델 | OpenAI text-embedding-3-small | text-embedding-3-large, Sentence-BERT | 1536차원으로 충분한 성능, 비용 효율적 |
| 차원 축소 | sklearn t-SNE | UMAP, PCA | sklearn에 내장되어 추가 설치 불필요, 비선형 관계 시각화에 적합 |
| 시각화 | SVG 직접 렌더링 | Chart.js, D3.js, Recharts | 외부 라이브러리 없이 가볍게 구현, 커스텀 자유도 높음 |
| Backend | FastAPI | Flask, Express | week02와 동일, async 지원, 자동 API 문서 |
| Frontend | Next.js 16 + Tailwind v4 | Vite + React | week02와 동일 스택 유지 |

## 핵심 구현

### 주요 로직 설명

**"Why Vector DB?"** — 같은 질문에 대해 인메모리 임베딩 검색과 ChromaDB 벡터 검색을 동시에 실행하고, 속도·비용·정확도를 Side-by-Side로 비교하는 데모.

**2단계 플로우:**
1. **임베딩 저장** — 문서 → 청킹 → OpenAI 임베딩 → ChromaDB에 영구 저장
2. **검색 비교** — 질문 입력 시 인메모리/VectorDB 두 방식을 `Promise.all`로 동시 실행

**인메모리 vs VectorDB 차이:**
| | 인메모리 | VectorDB (ChromaDB) |
|---|---------|-------------------|
| 임베딩 | 매 검색마다 모든 청크 재생성 | 사전 저장, 질문만 임베딩 |
| 검색 | numpy cosine similarity | ChromaDB HNSW 인덱스 |
| 속도 | 느림 (청크 수에 비례) | 빠름 (질문 임베딩만 필요) |
| 비용 | 높음 (전체 재임베딩) | 낮음 (질문 1회만) |
| 영속성 | 없음 | 디스크 저장, 서버 재시작 후 유지 |

### 코드 실행 방법

```bash
# 1. 백엔드
cd week03-embedding/mg/backend
pip install -r requirements.txt
# .env 파일에 OPENAI_API_KEY 설정 필요
py -m uvicorn main:app --reload --port 8000

# 2. 프론트엔드 (새 터미널)
cd week03-embedding/mg/frontend
npm install
npm run dev
# http://localhost:3000 에서 확인
```

### 프로젝트 구조
```
mg/
├── backend/
│   ├── main.py                    # FastAPI 8개 엔드포인트
│   ├── requirements.txt
│   ├── .env                       # OPENAI_API_KEY
│   ├── data/
│   │   └── samples.py             # 샘플 문서 3종
│   ├── models/
│   │   └── schemas.py             # Pydantic 스키마
│   └── services/
│       ├── chunking_service.py    # 텍스트 청킹 (week02 재활용)
│       ├── llm_service.py         # GPT 호출 (week02 재활용)
│       ├── embedding_service.py   # OpenAI 임베딩 호출
│       ├── memory_search.py       # 인메모리 cosine similarity 검색
│       ├── vector_store.py        # ChromaDB 래퍼
│       └── viz_service.py         # t-SNE 2D 차원축소
└── frontend/
    └── src/
        ├── app/
        │   ├── globals.css        # Midnight Gold 테마
        │   ├── layout.tsx
        │   └── page.tsx           # 메인 페이지
        ├── types/
        │   └── vector.ts          # TypeScript 타입 정의
        ├── hooks/
        │   └── useVectorSearch.ts # 상태 관리 훅
        └── components/
            ├── DocumentInput.tsx   # 문서 입력/샘플 선택
            ├── EmbeddingPanel.tsx  # 임베딩 저장 버튼 + 통계
            ├── QuestionInput.tsx   # 질문 입력
            ├── AnswerCard.tsx      # 답변 카드 (memory/vectordb)
            ├── ComparePanel.tsx    # 인메모리 vs VectorDB 비교
            ├── StatsBar.tsx        # 시간/비용 비교 막대 그래프
            ├── VectorViz.tsx       # t-SNE 2D 산점도 시각화
            └── CollectionInfo.tsx  # 컬렉션 목록/삭제
```

### API 엔드포인트
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/samples` | 샘플 문서 목록 |
| GET | `/api/samples/{id}` | 샘플 문서 내용 |
| POST | `/api/embed` | 문서 → 청킹 → 임베딩 → ChromaDB 저장 |
| POST | `/api/search/vectordb` | ChromaDB 벡터 검색 → LLM 답변 |
| POST | `/api/search/memory` | 인메모리 임베딩 검색 → LLM 답변 |
| GET | `/api/visualize/{name}` | t-SNE 2D 시각화 좌표 |
| GET | `/api/collections` | 저장된 컬렉션 목록 |
| DELETE | `/api/collections/{name}` | 컬렉션 삭제 |

## WHY (의사결정 기록)
1. **Q**: 왜 ChromaDB를 선택했는가?
   **A**: PersistentClient 모드로 별도 서버 없이 `pip install chromadb`만으로 사용 가능. 로컬 파일 기반이라 데모 환경에 적합하고, cosine distance + HNSW 인덱스를 기본 지원한다. Pinecone은 클라우드 의존성이 있고, FAISS는 메타데이터 관리가 불편하다.

2. **Q**: 왜 인메모리 검색을 매번 전체 재임베딩하도록 만들었는가?
   **A**: "Vector DB가 왜 필요한가?"를 극적으로 보여주기 위해 의도적으로 비효율적인 방식을 사용. 인메모리는 매 질문마다 모든 청크를 다시 임베딩하고, VectorDB는 질문만 임베딩한다. 이 차이가 속도와 비용 격차로 직관적으로 드러난다.

3. **Q**: 왜 t-SNE를 사용했는가?
   **A**: UMAP이 더 빠르지만 별도 `umap-learn` 패키지가 필요하다. t-SNE는 scikit-learn에 내장되어 있어 추가 의존성 없이 사용 가능. 시각화 용도로는 충분한 품질을 제공한다.

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | 프론트엔드 빌드 실패 | `Module not found: @/types/compare` | week02에서 복사한 DocumentInput.tsx가 week02 타입 경로를 참조 | import를 `@/types/vector`로 수정 |
| 2 | 프론트엔드 콘솔 에러 | `Failed to fetch` at fetchCollections | `/api/collections` 엔드포인트가 500 에러 반환 | ChromaDB `list_collections()`가 Collection 객체를 반환하는데 문자열로 처리하던 버그 수정 |
| 3 | 페이지 로드 시 fetch 에러 | `Failed to fetch` at fetchSamples | 백엔드 서버 미실행 상태에서 프론트엔드 접속 | 백엔드 서버를 먼저 실행 후 프론트 접속 |

## 회고
- 이번 주 배운 점:
  - Vector DB(ChromaDB)의 핵심 가치: 임베딩을 한 번만 생성·저장하면 이후 검색은 질문만 임베딩하면 되므로 속도와 비용이 크게 절감된다
  - cosine distance vs cosine similarity: ChromaDB는 distance(0~2)를 반환하므로 `1 - distance`로 similarity 변환 필요
  - t-SNE의 perplexity 파라미터는 데이터 포인트 수보다 작아야 해서, 적은 청크 수에 대한 엣지 케이스 처리가 필요했다
  - ChromaDB 버전별 API 차이: `list_collections()`가 문자열 리스트가 아닌 Collection 객체 리스트를 반환하는 변경사항 대응
- 다음 주 준비할 것:
  - RAG 파이프라인 전체 흐름 학습 (Retrieval → Augmentation → Generation)
  - LangChain/LlamaIndex 등 RAG 프레임워크 비교 조사
