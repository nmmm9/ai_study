# 1주차: LLM API 연동 - juwon

## 기술 스택

| 항목        | 선택                        | 대안                          | 선택 이유                                      |
| --------- | ------------------------- | --------------------------- | ------------------------------------------ |
| LLM 호출 방식 | OpenAI Python SDK         | HTTP 직접 호출 (requests, curl) | Streaming 및 usage 수집 구현이 간단하고 구조 설계에 집중 가능 |
| 아키텍처 구조   | OOP 기반 터미널 챗봇             | 단일 함수형 스크립트                 | 확장성과 유지보수를 고려한 구조 설계                       |
| 모델        | gpt-4o-mini               | gpt-4.1 / gpt-4.1-mini      | 학습 및 테스트에 적합한 경량 모델                        |
| 응답 처리     | Streaming + 실제 usage 수집   | Non-streaming 응답            | 실시간 출력 및 정확한 토큰 사용량 추적 목적                  |
| 히스토리 관리   | 최근 N턴 유지 (Sliding Window) | 전체 대화 유지                    | 토큰 폭증 방지 및 맥락 유지 균형                        |
| 프록시 확장    | base_url 기반 프록시 전환 구조     | OpenAI 직접 연결 고정             | LiteLLM, Azure, OpenRouter 등 실무 확장 가능성 확보  |

---

## 핵심 구현

* 주요 로직 설명:

  * `ChatBot` 클래스를 중심으로 OOP 구조로 설계하였다.
  * `self.history`에 대화 기록을 저장하고 `_trim_history()`를 통해 최근 10턴(user+assistant 쌍)만 유지하도록 설계하였다.
  * `client.chat.completions.create()` 호출 시 `stream=True` 옵션을 사용하여 Streaming 응답을 구현하였다.
  * `stream_options={"include_usage": True}`를 사용하여 마지막 chunk에서 실제 토큰 사용량(prompt_tokens, completion_tokens)을 수집하였다.
  * 입력/출력 토큰을 누적하여 `print_usage()`에서 총 사용량을 확인할 수 있도록 구현하였다.
  * `match-case` 문을 활용하여 `quit`, `reset`, `usage` 명령어를 처리하였다.
  * 프록시 버전에서는 `base_url`과 `api_key`를 환경변수 기반으로 설정하여 다양한 OpenAI 호환 API(LiteLLM, Azure, OpenRouter 등)로 전환 가능하도록 설계하였다.

* 코드 실행 방법:

  1. 가상환경 생성 (선택)

     ```
     python -m venv venv
     venv\Scripts\activate
     ```
  2. 패키지 설치

     ```
     pip install openai python-dotenv
     ```
  3. `.env` 파일 생성

     ```
     OPENAI_API_KEY=sk-본인키입력
     ```

     (프록시 사용 시)

     ```
     PROXY_BASE_URL=프록시주소
     PROXY_API_KEY=프록시키
     ```
  4. 실행

     ```
     python main.py
     ```

---

## WHY (의사결정 기록)

1. **Q**: 왜 이 방식을 선택했는가?
   **A**:
   1주차의 목표는 LLM API의 구조를 이해하고 직접 연동해보는 것이었다.
   OpenAI Python SDK는 HTTP 헤더 설정, 인증 처리, 응답 파싱 등을 내부적으로 처리해주기 때문에 API 구조 이해에 집중할 수 있다.
   또한 Streaming 응답과 실제 토큰 usage 수집을 비교적 간단하게 구현할 수 있어 학습 목적에 적합하다고 판단하였다.
   더 나아가 클래스 기반 구조로 설계하여 이후 RAG 및 서버 구조 확장 시 재사용 가능하도록 고려하였다.

2. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**:
   첫 번째 대안은 HTTP 직접 호출 방식(requests 활용)이다. 이 방식은 API 요청 구조를 더 깊게 이해할 수 있지만 코드 복잡도가 증가한다.
   두 번째 대안은 FastAPI 서버 프록시 구조로 완전히 분리하는 방식이다. 클라이언트 → 서버 → OpenAI 구조로 설계하면 API 키 보호, 요청 로깅, 비용 제어가 가능하다.
   현재 구현에서는 base_url 전환 구조를 미리 설계하여 실무 환경으로 확장 가능성을 확보하였다.

---

## 트러블슈팅 로그

| # | 문제 상황             | 에러 메시지           | 원인 (Root Cause)     | 해결 방법                                     |
| - | ----------------- | ---------------- | ------------------- | ----------------------------------------- |
| 1 | API 호출 실패         | 401 Unauthorized | 환경변수 API 키 미설정      | .env 파일 확인 및 load_dotenv() 적용             |
| 2 | 토큰 usage가 0으로 표시됨 | 없음               | include_usage 옵션 누락 | stream_options={"include_usage": True} 추가 |
| 3 | 대화가 길어질수록 응답 지연   | 없음               | 히스토리 무제한 증가         | MAX_HISTORY_TURNS 제한 적용                   |

---

## 회고

* 이번 주 배운 점:

  * OpenAI ChatCompletion API 구조 이해
  * Streaming 응답 처리 방식 학습
  * 실제 토큰 usage 수집 방법 이해
  * 대화 히스토리 관리의 중요성 체감
  * OOP 구조 설계의 확장성 경험
  * base_url 전환을 통한 프록시 구조 이해

* 다음 주 준비할 것:

  * Chunking: PDF/Markdown 로드 및 텍스트 분할 전략 학습
  * 도메인 데이터를 의미 단위로 분할하는 방법 연구
  * 고정 길이 분할 vs 의미 기반 분할 방식 비교
  * Overlap 전략 이해
  * RAG 파이프라인 구조(임베딩 → 벡터 저장 → 검색 → LLM 입력 흐름) 사전 학습
