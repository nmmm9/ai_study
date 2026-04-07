# 7주차: Function Calling 기반 AI Agent 챗봇

## 개요


| 항목 | 6주차 | 7주차 |
|------|-------|-------|
| 검색 방식 | RAG 파이프라인 직접 호출 | LLM이 Function Calling으로 도구 선택 |
| 라우팅 | 싱글/멀티홉 분류기 | LLM 자동 지능형 라우팅 |
| 자가 보정 | 없음 | 유사도 낮으면 쿼리 재작성 후 재시도 |
| 비교 검색 | 멀티쿼리로 처리 | `compare_policies` 도구 분리 |
| UI | Streamlit | FastAPI + React |



## 아키텍처

```
사용자 질문
    ↓
FastAPI (server.py)
    ↓
PolicyAgent (agent.py)
    ↓
LLM (GPT-4o-mini) ── Function Calling ──▶ 도구 선택
                                              ↓
                              ┌───────────────────────────────┐
                              │  search_policy                │  단순 검색
                              │  search_and_validate          │  자가 보정 검색
                              │  compare_policies             │  두 정책 비교
                              │  list_policies                │  목록 조회
                              └───────────────────────────────┘
                                              ↓
                              ChromaDB + BM25 (week06 재사용)
                                              ↓
                              도구 결과 → LLM → 최종 답변 (SSE 스트리밍)
                                              ↓
                              React 프론트엔드 (index.html)
```

---

## 구현 기능

### 1. 지능형 쿼리 라우팅
LLM이 사용자 질문을 분석하여 적합한 도구를 자동 선택합니다.

| 질문 유형 | 선택 도구 |
|----------|----------|
| 단순 사실 조회 | `search_policy` |
| 복잡하거나 정확성이 중요한 질문 | `search_and_validate` |
| "A랑 B 중 뭐가 나아?" 비교 | `compare_policies` |
| 어떤 정책이 있는지 | `list_policies` |

### 2. 자가 보정 검색 (Self-Correction)
`search_and_validate` 도구는 검색 후 유사도를 자동 검증합니다.

```
검색 실행
    ↓
유사도 ≥ 0.3 ? ──▶ 결과 반환
    ↓ (낮음)
LLM으로 쿼리 재작성
    ↓
재검색 (최대 3회 반복)
```

---

## 파일 구조

```
week07-function-calling/minseon/
├── backend/
│   ├── server.py        # FastAPI 서버 (세션 관리 + SSE 스트리밍)
│   ├── agent.py         # AI Agent (Function Calling 루프)
│   ├── tools.py         # 도구 정의 및 구현
│   └── requirements.txt
└── frontend/
    └── index.html       # React UI (CDN)
```

> 데이터(chroma_db, data/)는 week06-streamlit-ui/minseon/ 을 공유합니다.

---

## 실행 방법

### 1. 패키지 설치

```bash
cd c:\Users\user\ai_study\week07-function-calling\minseon\backend
pip install -r requirements.txt
```

### 2. 환경변수 설정

`backend/` 폴더에 `.env` 파일 생성:

```
OPENAI_API_KEY=sk-...
```

### 3. 백엔드 실행

```bash
uvicorn server:app --reload
```

### 4. 프론트엔드 실행

`frontend/index.html` 파일을 브라우저에서 열기

---

## 사용 가능한 도구 (Function Calling)

### `search_policy`
청년 정책 문서에서 키워드 기반 하이브리드 검색

```json
{ "query": "청년도약계좌 가입 조건", "top_k": 5 }
```

### `search_and_validate`
검색 + 자동 품질 검증 + 쿼리 재작성 재시도

```json
{ "query": "소득 200만원 지원 가능한 정책", "min_similarity": 0.3 }
```

### `compare_policies`
두 정책 동시 검색 후 비교용 결과 반환

```json
{ "policy_a": "청년도약계좌", "policy_b": "청년희망적금" }
```

### `list_policies`
현재 DB에 인덱싱된 전체 정책 목록 조회

```json
{}
```
