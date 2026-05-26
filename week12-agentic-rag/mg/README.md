# Week 12 — Agentic RAG

11주차 Plan-and-Execute 그래프에 **문서 검색 도메인 (`documents`)** 과
**Retriever 에이전트** 를 추가해, LLM 이 직접 검색을 운영하는
**Agentic RAG** 시스템을 만듭니다.

## 아키텍처

```
[START] → Planner → Executor(step N) → Replanner ─┐
              │       ▲                             │
              │       │  ┌─ continue ───────────────┤
              │       │  ├─ revise ─────────────────┘
              │       │  └─ finish ──┐
              │       │               ▼
              │       │            Writer ⇄ Critic
              │       │                       │
              │       │             [pass] ──→ END
              │       └─ (advance to next step)
              ▼
        ┌───────────────────────────────────────┐
        │  domain agents (9개)                  │
        │  shopping / lifestyle / sports / news │
        │  finance / government / education /   │
        │  info / ★ documents                   │
        └───────────────────────────────────────┘
                          │
                          ▼ (domain=documents 일 때)
            ┌──────────────────────────┐
            │ Retriever (자기 루프)     │
            │  Query Rewrite            │
            │   ↓                       │
            │  Vector Search (ChromaDB) │
            │   ↓                       │
            │  Self-Eval (1~5점)        │
            │   ↓ score < 3             │
            │  Re-search (최대 2회)     │
            └──────────────────────────┘
```

| 노드 | 역할 | 출처 |
|------|------|------|
| Planner / Executor / Replanner | step 분해 + 실행 + 재계획 | 11주차 |
| Writer / Critic | 답변 작성 + 채점 + 재작성 | 10주차 |
| 8 도메인 에이전트 | 도구 호출 | 9주차 |
| **★ Retriever** | 검색 + 자기 평가 + 쿼리 재작성 | **12주차 신규** |

## Retriever 동작 (Self-RAG 패턴)

```
질문 → Query Rewrite (대명사 제거, 키워드 추출)
       ↓
       Vector Search (ChromaDB, cosine)
       ↓
       Self-Eval: 검색 결과가 답변에 충분한가? 1~5점
       ↓
       [score ≥ 3]: 통과 → chunks 반환
       [score < 3]: alternative_query 로 재검색 (최대 2회)
```

설정값 (`agents/retriever.py`):
- `MAX_RETRIEVAL_ROUNDS = 2`
- `RELEVANCE_THRESHOLD = 3` (5점 만점)

## 문서 인덱싱 파이프라인

```
PDF / TXT / MD 업로드
   ↓
파일 파싱 (pypdf for PDF, plain read for TXT/MD)
   ↓
청킹 (paragraph-aware, ~600 token, 100 overlap)
   ↓
임베딩 (OpenAI text-embedding-3-small, 1536d)
   ↓
ChromaDB 영속 저장 (./chroma_data/)
```

## 신규 API

| 엔드포인트 | 설명 |
|------------|------|
| `GET /api/documents` | 업로드된 문서 목록 + chunk 수 |
| `POST /api/documents/upload` | 멀티파트 파일 업로드 → 인덱싱 |
| `POST /api/documents/text` | 평문 텍스트 인덱싱 (테스트용) |
| `DELETE /api/documents/{doc_id}` | 문서 삭제 |

## 신규 SSE 이벤트

| 이벤트 | 데이터 |
|--------|------|
| `retrieval_round` | `{round, query, top_k}` — 검색 시작 |
| `retrieval_result` | `{round, chunks: [{doc_name, page, score, text_snippet}]}` |
| `retrieval_eval` | `{round, score, reasoning, alternative_query}` |

기존 이벤트(plan_*, step_*, critic_score, token 등) 모두 유지.

## 신규 도메인 / 도구

- **`documents` 도메인**: 8 → **9 도메인**
- **도구 2개 추가** (총 52 → 54):
  - `document_search(query, top_k)` — 단발 검색
  - `list_uploaded_documents()` — 인덱스 상태 조회
- **Executor 분기**: step 의 domain 이 `documents` 면 일반 도메인 에이전트 대신 **Retriever 에이전트** 가 호출됨 (자기 루프 포함)

## 실행

```bash
# 백엔드
cd backend
py -m pip install -r requirements.txt   # chromadb, pypdf, python-multipart 추가
py -m uvicorn main:app --reload --port 8000

# 프론트엔드
cd frontend
npm install
npm run dev
```

브라우저에서 좌측 Documents 패널에 파일 업로드 → 채팅에서 질문.

## 11주차 → 12주차 변화

| 항목 | 11주차 | 12주차 |
|------|------|------|
| 도메인 | 8개 | **9개 (+ documents)** |
| 검색 능력 | 외부 API 도구만 | **+ 사용자 업로드 문서 RAG** |
| 검색 자기 검증 | 없음 | **Self-RAG (1~5점 자기 평가)** |
| 쿼리 재작성 | 없음 | **자동 (대명사 해소, 키워드 추출)** |
| 답변 인용 | 없음 | **`[1]`, `[2]` 인용 마커** |
| 새 인프라 | — | **ChromaDB + 임베딩 + 청킹** |

## 검증 (실측)

```
Q: "업로드한 문서에서 LangGraph 에 대해 뭐라고 했는지 알려줘"

  plan step 1 [documents]: 업로드된 문서에서 LangGraph 정보 검색
  retrieval round 1: query='LangGraph 정보 검색'
  retrieval eval: score=5/5 — 명확하게 정보 있음
  critic: 9/10
  done: {final_score: 9, iterations: 1, plan_steps: 1}
```

## 핵심 학습 포인트

1. **Agentic RAG** — 검색 자체를 LLM 이 운영. 단발 RAG 와 다름
2. **Query Rewriting** — 사용자 질문 → 검색 친화적 쿼리로 변환
3. **Self-Eval** — 검색 결과를 LLM 이 1~5점 채점, 부족 시 재검색
4. **Citation 강제** — Writer system prompt 에 인용 규칙 추가 → 환각 방지
5. **그래프 통합** — Plan-and-Execute 의 한 step 으로 RAG 가 자연스럽게 들어감
