# 1주차: LLM API 연동 - ys

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| Frontend | React + Vite | React + CRA, Next.js | 채팅 메시지, 입력창, 토큰 정보 영역을 컴포넌트로 나누기 쉽고, Vite는 실행 속도가 빨라 개발 확인이 편하다. |
| CSS | Tailwind CSS | CSS Modules, styled-components | 별도 CSS를 길게 작성하지 않고도 박스형 채팅 UI와 반응형 레이아웃을 빠르게 만들 수 있어서 선택했다. |
| Backend | FastAPI | Flask, Django | Python으로 OpenAI SDK를 바로 사용할 수 있고, StreamingResponse로 SSE 응답을 구현하기 쉽다. |
| LLM SDK | OpenAI Python SDK | LangChain, 직접 HTTP 요청 | OpenAI API 호출과 Streaming 처리를 공식 SDK 문법으로 간단하게 구현할 수 있다. |
| 통신 방식 | SSE(Server-Sent Events) | WebSocket, 일반 HTTP 요청 | AI 답변은 서버에서 클라이언트로 한 방향으로 계속 전달하면 되기 때문에 SSE를 선택했다. |
| 응답 방식 | Streaming 응답 | 일반 응답 | 답변 전체가 완성될 때까지 기다리지 않고 생성되는 내용을 바로 화면에 보여줄 수 있어서 사용자가 기다리는 걸 지루하게 느끼지 않을 수 있다. |
| 토큰 관리 전략 | 자동 요약 메모리 방식 | 최근 N개 대화 유지, 전체 대화 전송 | 기준 토큰을 넘으면 오래된 대화를 요약해서 긴 대화의 핵심 맥락은 유지하고 토큰 사용량은 줄일 수 있다. |

## 핵심 구현
- 주요 로직 설명:
  - useState를 사용해 사용자 메시지, AI 메시지, 입력값, 토큰 정보, 요약 메모리 상태 관리
  - fetch()와 ReadableStream을 사용해 Backend의 SSE Streaming 응답 처리
  - TextDecoder로 Streaming 응답 조각을 문자열로 변환
  - SSE 이벤트를 meta, message, done, error로 구분하여 처리
  - message 이벤트가 올 때마다 마지막 AI 메시지에 응답 조각을 이어 붙임
  - FastAPI StreamingResponse를 사용해 text/event-stream 형식으로 응답 전송
  - OpenAI Python SDK의 stream=True 옵션으로 LLM 응답을 조각 단위로 수신
  - 예상 토큰 수가 500 이상이면 오래된 대화를 요약하는 자동 요약 메모리 로직 구현
  - 요약 발생 시 오래된 원문 대화는 제거하고 요약 메모리와 최근 대화만 유지
- 코드 실행 방법:
  
  - Backend 실행
    - cd backend
    - copy .env.example .env #OPENAI_API_KEY=본인 API 키 작성
    - .\venv\Scripts\Activate.ps1
    - pip install -r requirements.txt
    - uvicorn main:app --reload --port 8000

  - Frontend 실행
    - cd frontend
    - npm install
    - npm run dev
    
  - 브라우저 접속
    - http:\\localhost:5173

## WHY (의사결정 기록)
1. **Q**: 왜 FastAPI 방식을 선택했는가?
   **A**: FastAPI는 Python 기반 Backend 서버이기 때문에 OpenAI Python SDK와 연결하기 쉽고, StreamingResponse를 지원하여 SSE 방식의 실시간 응답을 구현하기 적합하다. 또한 message, history, summary 같은 요청 데이터를 구조화해서 다룰 수 있어 채팅 기록, 요약 메모리, 토큰 정보 관리가 편리하다. 이 프로젝트에서는 누적 토큰이 기준치를 넘으면 이전 대화를 요약해서 저장하는 방식을 사용하므로, 이러한 데이터를 명확하게 분리하고 관리할 수 있는 FastAPI를 선택하였다.
2. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**: Next.js의 API Route를 사용해서 Frontend와 Backend 기능을 하나의 프로젝트에서 처리할 수 있게 할 것이다. 또한 토큰 관리는 자동 요약 방식 대신 RAG 방식으로 구현하여, 긴 대화에서 필요한 과거 내용만 검색해 사용하는 구조로 만들 것이다.

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | Frontend에서 Backend Streaming 응답을 받지 못함 | Failed to fetch | Backend 서버가 실행되지 않았거나 Frontend 요청 주소와 Backend 포트가 일치하지 않음 | Backend를 8000 포트로 실행하고 Frontend의 요청 주소를 http://127.0.0.1:8000으로 통일함 |
| 2 | 브라우저에서 Backend API 요청이 차단됨 | CORS policy 오류 | React 개발 서버 주소가 FastAPI CORS 허용 목록에 없었음 | FastAPI에 CORSMiddleware를 추가하고 http://localhost:5173을 허용함 |

## 회고
- 이번 주 배운 점: Frontend와 Backend가 API로 데이터를 주고받는 전체 흐름, .env를 사용한 API Key 관리의 중요성, (LLM 호출, Backend, Frontend, 통신) 방식들을 배웠다.
- 다음 주 준비할 것: Chunking 개념 숙지, 도메인 데이터를 의미 단위로 분할하는 방법
