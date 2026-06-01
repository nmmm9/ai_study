
# 1주차: LLM API 연동 - 현주

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| 백엔드 | FastAPI | Flask, Spring Boot | 비동기 처리와 API 서버 구축이 쉽고 Streaming 구현에 유리 |
| 프론트엔드 | HTML/CSS/JavaScript | React | 초기 학습 단계에서 구조 이해에 집중하기 위해 선택 |
| LLM API | OpenAI API | Gemini API, Claude API | 문서가 잘 정리되어 있고 예제가 많아 학습하기 적합 |
| 데이터 형식 | JSON | XML | 가볍고 가독성이 좋으며 REST API에서 가장 많이 사용 |
|환경변수 관리 | .env | 코드 내 직접 작성 | API Key 보안 및 GitHub 업로드 방지 목적 |
| 통신 방식 | REST API | GraphQL, WebSocket | 구조가 직관적이고 API 학습 입문에 적합 |
| 응답 방식 | Streaming | 일반 응답 | ChatGPT처럼 실시간 출력 구현 가능 |

## 핵심 구현
- 주요 로직 설명:
   - 사용자가 브라우저에서 질문 입력
   - JavaScript가 질문 데이터를 FastAPI 서버로 전달
   - FastAPI 서버가 .env 파일에서 API Key를 읽음
   - 서버가 OpenAI LLM API에 POST 요청 전송
   - 요청 시 JSON 형식으로 model/messages 데이터 구성
   - Authorization Header에 API Key 포함
   - OpenAI 서버가 질문 처리 후 응답 반환
   - Streaming 방식으로 응답 데이터를 실시간 수신
   - 프론트엔드에서 응답 내용을 순차적으로 출력
   - 채팅 기록(history)을 유지하여 이전 대화 문맥 일부 유지
   - MAX_HISTORY를 통해 토큰 사용량 관리
   - API Key 보안을 위해 프론트엔드에는 Key를 노출하지 않음

- 코드 실행 방법:
  
  - 가상환경 생성 및 실행
    - python -m venv .venv
  - 가상환경 활성화
    - windows: .venv\Scripts\activate
    - Mac/Linux: source .venv/bin/activate
  - 패키지 설치
    -  pip install fastapi uvicorn openai python-dotenv jinja2
  - .env 파일 생성 
    - OPENAI_API_KEY=본인_API_KEY
  - FastAPI 서버 실행
    - uvicorn main:app --reload
  - 브라우저 접속
    - http://127.0.0.1:8000
    
## WHY (의사결정 기록)
1. **Q**: 왜 REST API 방식을 선택했는가?<br>
   **A**:
    - 가장 많이 사용되는 API 구조이며 학습 자료가 풍부함
    - HTTP Method(GET/POST) 기반 구조를 이해하기 쉬움
    - LLM API 대부분이 REST API 기반으로 동작함
    - URL + Method + JSON 구조를 통해 API 동작 원리를 명확히 이해 가능


3. **Q**: 왜 .env 방식으로 API Key를 관리했는가?<br>
   **A**:
     - 프론트엔드에 API Key를 직접 작성하면 브라우저에서 노출될 수 있음
     - API Key는 사용량 추적 및 과금과 연결되므로 보안이 중요함
     - .env 파일을 통해 환경변수로 관리하면 코드와 분리 가능
     - .gitignore에 등록하여 GitHub 업로드 방지 가능


4. **Q**: 왜 Streaming 응답을 사용했는가?<br>
   **A**:
     - 일반 응답은 답변 생성이 끝난 후 한 번에 출력됨
     - Streaming은 생성되는 내용을 실시간으로 출력 가능
     - ChatGPT와 유사한 사용자 경험 제공 가능
     - 긴 답변에서도 응답 대기 시간이 짧게 느껴짐

     
5. **Q**: 다르게 구현한다면 어떻게 했을까?<br>
   **A**:<br> 현재는 REST API 기반의 FastAPI 구조로 구현하였지만,<br>
   실시간 양방향 통신 강화를 위해 WebSocket 기반 채팅 구조로 구현하거나,<br>
   프론트엔드를 React로 구성하여 컴포넌트 기반 UI와 상태 관리를 적용할 수도 있었을 것이다.
   
## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | API Key 노출 위험 | 없음 | 프론트엔드 코드에 직접 Key 작성 시도 | .env 환경변수 방식으로 변경 |
| 2 | 응답이 한 번에 출력됨 | Streaming 미동작 | 일반 응답 방식 사용 | Streaming 방식으로 응답 처리 수정 |
| 3 | 템플릿 실행 오류 | 404 Template Not Found | templates 폴더 경로 문제 | Jinja2 템플릿 구조 수정 |
| 4 | 서버 변경사항 미반영 | 코드 수정 후 미출력 | 서버 재실행 누락 | --reload 옵션 사용 |
| 5 | JSON 구조 이해 어려움 | 요청 Body 오류 | API 요청 형식 미숙 | JSON 구조 및 REST API 흐름 학습 |

## 회고
- 이번 주 배운 점: REST API와 JSON 기반의 LLM API 동작 구조를 이해하고, <br>
                  FastAPI를 활용한 1:1 채팅 시스템 연동 흐름을 학습하였다.
- 다음 주 준비할 것: Chunking 개념과, 이를 활용한 검색 기반 AI 구조(RAG)의 기초를 학습할 예정이다.
