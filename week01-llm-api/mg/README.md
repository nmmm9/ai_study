# 1주차: LLM API 연동 - mg

## 개요
- 이번 주 목표: OpenAI / Anthropic API를 활용한 웹 기반 실시간 채팅 구현
- 사용한 도메인 데이터: 없음 (범용 대화)

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| Frontend | Next.js 15 (App Router) | React CRA, Vite | 풀스택 프레임워크, App Router 구조 학습 |
| CSS | Tailwind CSS | CSS Modules, styled-components | 유틸리티 퍼스트, 빠른 UI 개발 |
| Backend | Python FastAPI | Flask, Django | 비동기 지원, SSE 스트리밍, 이후 LangChain 연계 |
| LLM SDK | openai, anthropic (Python) | LangChain | 1주차는 직접 SDK로 원리 이해 |
| 통신 | SSE (Server-Sent Events) | WebSocket, Polling | 단방향 스트리밍에 적합, 구현 간단 |

## 핵심 구현
- 주요 로직 설명:
  - **Backend**: FastAPI에서 OpenAI/Anthropic SDK를 비동기로 호출, SSE(StreamingResponse)로 chunk 단위 응답 전달
  - **Frontend**: fetch + ReadableStream으로 SSE 파싱, React 상태로 실시간 UI 업데이트
  - **모델 선택**: 드롭다운으로 GPT-4o / GPT-4o Mini / Claude Sonnet 4.5 전환 가능
  - **토큰 표시**: 각 응답 완료 시 prompt/completion/total 토큰 수 표시

- 코드 실행 방법:
```bash
# 1. Backend 실행
cd week01-llm-api/mg/backend
pip install -r requirements.txt
# .env에 OPENAI_API_KEY, ANTHROPIC_API_KEY 설정
uvicorn main:app --reload --port 8000

# 2. Frontend 실행
cd week01-llm-api/mg/frontend
npm install
npm run dev
# http://localhost:3000 접속
```

## 시스템 구조
```
Browser (localhost:3000)  →  Next.js Frontend  →  FastAPI Backend (localhost:8000)  →  OpenAI/Anthropic API
                                                        ↓ SSE
                          ←  실시간 스트리밍 응답  ←
```

## WHY (의사결정 기록)
1. **Q**: 왜 Next.js + FastAPI 분리 구조를 선택했는가?
   **A**: Frontend(React/Next.js)는 모던 웹 UI 구축에 적합하고, Backend(Python FastAPI)는 이후 2주차부터 LangChain/LangGraph(Python) 연계가 자연스럽기 때문. Streamlit은 6주차에서 별도로 사용 예정이라 차별화.

2. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**: Next.js API Route에서 직접 LLM API를 호출하는 단일 프레임워크 방식도 가능. 하지만 그러면 JS SDK를 써야 하고, 이후 Python 기반 스터디 과제와 코드 재활용이 어려움.

3. **Q**: SSE vs WebSocket?
   **A**: LLM 응답은 서버→클라이언트 단방향 스트림이라 SSE가 적합. WebSocket은 양방향이 필요할 때 쓰는 게 맞음.

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | 프론트에서 백엔드 API 호출 시 차단 | CORS policy 에러 | 도메인이 다른 localhost:3000 → 8000 | FastAPI CORSMiddleware에 allow_origins 추가 |
| 2 | Anthropic 스트리밍 후 usage가 안 옴 | - | stream 컨텍스트 매니저 밖에서 final_message 호출 필요 | async with 블록 후 get_final_message() 호출 |

## 회고
- 이번 주 배운 점: OpenAI vs Anthropic API 구조 차이 (system 프롬프트 위치, max_tokens 필수 여부), SSE 스트리밍 구현 패턴
- 다음 주 준비할 것: Chunking을 위한 도메인 데이터 준비, LangChain 기본 사용법 복습
