
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
  
  - 
    - 
    - 
    - 
    - 
    - 

  - 
    - 
    - 
    - 
    
  - 브라우저 접속
    - 

## WHY (의사결정 기록)
1. **Q**: 왜 OOO 방식을 선택했는가?
   **A**: 
2. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**:
   
## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 |  |  |  |  |
| 2 |  |  |  |  |

## 회고
- 이번 주 배운 점: 
- 다음 주 준비할 것: 
