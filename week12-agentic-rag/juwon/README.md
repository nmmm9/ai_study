# 12주차: Agentic RAG — juwon

## 개요

11주차 Multi-Agent Debate 시스템에 Agentic RAG를 통합.
RAG를 고정 파이프라인이 아닌 에이전트 도구(tool)로 만들어,
LLM이 스스로 판단해서 필요할 때 과거 분석을 검색함.

## 기술 스택

| 항목 | 선택 | 이유 |
|------|------|------|
| LLM | GPT-4o-mini | 11주차와 동일 |
| Agent Framework | LangGraph ReAct | 11주차 LangGraph 연장 |
| Vector DB | Supabase pgvector | 6주차에서 사용, 히스토리 DB와 통합 |
| 차트 | Recharts | Next.js 친화적 |
| 배포 (BE) | Railway | FastAPI 무료 |
| 배포 (FE) | Vercel | Next.js 공식 |

## week11 대비 추가된 것

### A. 전문가 에이전트 RAG 강화 (graph.py)
- AI/ML, 웹/앱, 보안 전문가 에이전트가 분석 전 과거 데이터 조회
- "이번 주 vs 지난 분석" 비교 관점 자동 포함

### B. Agentic RAG 채팅 (agentic_chat.py)
- 기존: 고정 컨텍스트 → LLM 한 번 호출
- 변경: LLM이 판단 → RAG 도구 호출 → 재검색 or 답변
- 프론트에서 에이전트 도구 호출 과정이 실시간 표시됨

### C. 히스토리 저장소 교체 (storage.py)
- history.json → Supabase PostgreSQL + pgvector
- 분석 결과 임베딩해서 시맨틱 검색 가능

### 추가 기능
- 트렌드 차트: 언어별 등장 빈도 시계열 (Recharts)
- 히스토리 브라우저: 날짜 클릭해서 과거 분석 확인
- 키워드 구독: 등록 키워드가 트렌딩에 뜨면 이메일 알림

## 실행 방법

### 1. Supabase 설정
1. supabase.com 에서 새 프로젝트 생성
2. SQL Editor에서 supabase/schema.sql 전체 실행

### 2. 백엔드
```
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. 프론트엔드
```
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

## 배포

### 백엔드 (Railway)
1. Railway 프로젝트 생성 → GitHub 연결
2. 환경변수 설정 (.env.example 참고)
3. Start command: uvicorn main:app --host 0.0.0.0 --port $PORT

### 프론트엔드 (Vercel)
1. Vercel 프로젝트 생성 → GitHub 연결
2. NEXT_PUBLIC_API_URL = Railway 배포 URL

## WHY (의사결정 기록)

1. Q: 왜 Qdrant Cloud가 아닌 Supabase pgvector?
   A: 6주차에서 이미 Supabase를 사용했고, pgvector로 벡터 DB와 히스토리 DB를 하나로 통합. 서비스 수가 줄어 배포 복잡도 감소.

2. Q: 왜 ChromaDB EphemeralClient를 안 쓰나?
   A: 메모리 모드는 서버 재시작 시 초기화됨. 히스토리를 영구 보존해야 과거 비교 분석이 의미 있음.

3. Q: 왜 create_react_agent를 사용?
   A: LangGraph 생태계 안에서 ReAct 패턴을 가장 간결하게 구현. 11주차 StateGraph와 같은 프레임워크.
