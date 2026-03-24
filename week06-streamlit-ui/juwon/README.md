# 6주차: Streamlit UI (1차 시연) - juwon

## 기술 스택

| 항목        | 선택                            | 대안                         | 선택 이유                                                                                      |
| --------- | ----------------------------- | -------------------------- | ------------------------------------------------------------------------------------------ |
| 백엔드 프레임워크 | FastAPI                       | Streamlit                  | Vercel은 서버리스 환경이라 상태 유지가 필요한 Streamlit 구조와 맞지 않음. FastAPI로 REST API 서버를 분리하여 장기 실행 가능      |
| 프론트엔드     | Next.js (Pages Router)        | Streamlit, React (CRA)     | Vercel이 Next.js를 공식 지원하여 빌드 및 배포 자동화가 가장 간편                                                |
| 임베딩 모델    | OpenAI text-embedding-3-small | sentence-transformers      | sentence-transformers는 torch 의존으로 Docker 이미지가 5.8GB까지 증가 → 배포 제한 초과. OpenAI 사용 시 약 1GB로 감소 |
| 벡터 DB     | ChromaDB (EphemeralClient)    | PersistentClient, Pinecone | 배포 환경에서 디스크 경로 고정이 어려워 메모리 기반으로 구성, 서버 시작 시 문서 재빌드                                         |
| 인증        | Supabase Auth                 | Firebase Auth, 자체 JWT      | 기존 프로젝트에서 이미 사용 중이라 추가 설정 최소화                                                              |
| 실시간 스트리밍  | SSE                           | WebSocket                  | 단방향 스트리밍에 적합하며 HTTP 기반이라 구현이 단순                                                            |
| 백엔드 배포    | Railway                       | Render, Fly.io, EC2        | 장기 실행 서버 지원, GitHub 연동 간편, 무료 플랜 제공                                                        |
| 프론트엔드 배포  | Vercel                        | Netlify, GitHub Pages      | Next.js 공식 배포 플랫폼, 환경 변수 및 CDN 자동 처리                                                       |

---

## 핵심 구현

### 주요 로직 설명:

* **RAG 파이프라인**
  사용자 질문 → Multi-Query 변형 → BM25 + Vector Hybrid Search → RRF로 점수 결합 → GPT-4o-mini로 최종 답변 생성
  청크 전략은 Parent-Child 구조를 사용하여

  * 검색: 200자 (정확도)
  * 응답 컨텍스트: 600자 (정보량 확보)

* **SSE 스트리밍**
  FastAPI에서 `StreamingResponse`를 사용하여 토큰 단위로 전송
  Next.js에서는 `ReadableStream`으로 수신하여 실시간 출력

* **파일 업로드 인덱싱**
  업로드된 파일은 `add_chunks()`로 기존 벡터 DB에 추가
  삭제 시 전체 재빌드 방식으로 일관성 유지

* **인증 미들웨어**
  모든 API에 `Depends(get_user_id)` 적용
  Supabase JWT 검증 후 만료 시 401 반환
  프론트에서는 자동 로그아웃 처리

---

### 코드 실행 방법:

```bash
# 백엔드 실행
cd backend
uvicorn main:app --reload --port 8000

# 프론트엔드 실행
cd frontend
npm run dev
```

* 배포 URL: [https://frontend-eta-ruddy-15.vercel.app](https://frontend-eta-ruddy-15.vercel.app)

---

## WHY (의사결정 기록)

1. **Q: 왜 이 방식을 선택했는가?**
   **A:**
   Vercel은 서버리스 환경으로 요청마다 새로운 프로세스가 생성된다.
   Streamlit은 세션 상태를 유지해야 하는 구조라 서버리스와 맞지 않으며,
   RAG 또한 초기화 후 메모리에 유지해야 하기 때문에 장기 실행 서버가 필요하다.
   따라서 FastAPI를 Railway에 배포하고, UI는 Next.js로 분리하여 Vercel에 배포하는 구조를 선택했다.

2. **Q: 다르게 구현한다면 어떻게 했을까?**
   **A:**
   외부 벡터 DB(Pinecone, Weaviate)를 사용하면 모든 구조를 서버리스 환경으로 통합할 수 있다.
   또한 인증을 NextAuth.js로 구현하면 프론트엔드 중심으로 인증을 통합 관리할 수 있다.
   하지만 이번 프로젝트에서는 비용과 복잡도를 고려해 현재 구조가 더 실용적이었다.

---

## 트러블슈팅 로그

| # | 문제 상황            | 에러 메시지                     | 원인 (Root Cause)                                        | 해결 방법                                 |
| - | ---------------- | -------------------------- | ------------------------------------------------------ | ------------------------------------- |
| 1 | Railway 빌드 실패    | Image size exceeded 4GB    | sentence-transformers 설치 시 torch 포함 → Docker 이미지 5.8GB | OpenAI Embeddings로 변경하여 이미지 약 1GB로 감소 |
| 2 | 프론트 API 호출 실패    | Unexpected token '<' / 404 | .env.local이 UTF-16으로 저장되어 환경 변수 로딩 실패                  | UTF-8로 재생성                            |
| 3 | 특정 질문 차단         | 관련 없는 질문 처리                | 가드레일 키워드 부족                                            | 승무원, 항공 등 키워드 추가                      |
| 4 | 업로드 파일 반영 안됨     | 답변에 반영 안됨                  | 절대 경로 저장 → 재시작 시 경로 불일치                                | 파일명만 저장 후 런타임에 경로 조합                  |
| 5 | 401 에러 발생        | Unauthorized               | JWT 토큰 만료                                              | 401 시 자동 로그아웃 처리                      |
| 6 | node_modules 커밋됨 | git status에 수천 파일          | .gitignore 없음                                          | .gitignore 추가 후 캐시 제거                 |

---

## 회고

### 이번 주 배운 점:

* 서버리스와 장기 실행 서버의 구조적 차이를 이해했다.
* Docker 이미지 크기가 배포의 중요한 제약 요소임을 경험했다.
* SSE를 활용한 실시간 스트리밍 구현 방법을 익혔다.
* 환경 변수를 로컬, 배포 환경별로 분리 관리하는 방법을 학습했다.
