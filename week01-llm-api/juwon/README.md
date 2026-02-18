# 1주차: LLM API 연동 - juwon

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| LLM API | OpenAI GPT-4o-mini | Claude, Gemini | 비용 효율적이며 API 사용이 간편함 |
| 언어 | Python | JavaScript, Go | LLM API 연동에 가장 널리 사용되는 언어 |
| 환경 관리 | python-dotenv | 직접 환경변수 설정 | API 키 보안 관리 용이 |

## 핵심 구현
- **주요 로직**: OpenAI GPT-4o-mini를 활용한 1:1 대화 터미널 챗봇
  - **클래스 기반 설계**: `ChatBot` 클래스로 상태(히스토리, 토큰)를 캡슐화
  - **Streaming 응답**: `chat.completions.stream()` 컨텍스트 매니저로 실시간 출력
  - **정확한 토큰 측정**: `stream.get_final_completion().usage`로 실제 토큰 수 기록 (근사치 아님)
  - **대화 히스토리 관리**: 최근 10턴(user+assistant 쌍) 기준으로 유지

- **코드 실행 방법**:
```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 챗봇 실행
python chat.py
```

## WHY (의사결정 기록)

### 1. **Q**: 왜 Streaming 방식을 선택했는가?
   **A**:
   - 사용자 경험 향상: 전체 응답을 기다리지 않고 실시간으로 확인 가능
   - 긴 응답의 경우 체감 대기 시간 단축

### 2. **Q**: 왜 토큰 사용량을 정확하게 측정하는가?
   **A**:
   - `chat.completions.stream()` 컨텍스트 매니저는 스트림 종료 후 `get_final_completion()`으로 실제 usage를 제공
   - 근사치 계산 없이 `prompt_tokens`, `completion_tokens`를 그대로 사용

### 3. **Q**: 왜 히스토리를 글자 수가 아닌 턴 수로 관리하는가?
   **A**:
   - 글자 수 기준은 메시지가 짧을 경우 실제 대화 맥락이 너무 빨리 잘릴 수 있음
   - 10턴(user+assistant 20개 메시지) 기준이 맥락 유지 측면에서 더 직관적

### 4. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**:
   - **정확한 토큰 계산**: `tiktoken` 라이브러리로 정확한 토큰 수 계산
   - **대화 요약**: 오래된 대화를 제거하는 대신 요약하여 장기 컨텍스트 유지
   - **멀티모달**: 이미지나 파일을 입력으로 받아 처리

## 프로젝트 구조
```
juwon/
├── .env                        # API 키 설정
├── requirements.txt            # 의존성 패키지
├── chat.py                     # 챗봇 메인 코드
├── 스터디_1주차_rag의_개념.pdf  # RAG 학습 자료
└── README.md                   # 본 문서
```

## 주요 기능

### 명령어
- `quit`: 프로그램 종료 및 토큰 사용량 출력
- `reset`: 대화 히스토리 초기화
- `usage`: 현재까지 누적 토큰 사용량 확인

### 대화 흐름
1. 사용자 입력 받기
2. `history`에 user 메시지 추가
3. 10턴 초과 시 오래된 메시지 제거
4. `system + history`를 GPT API에 전송 (Streaming)
5. 실시간 응답 출력
6. 스트림 종료 후 실제 토큰 수 기록
7. `history`에 assistant 응답 추가

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| - | (향후 추가 예정) | - | - | - |

## 회고
- **이번 주 배운 점**:
  - OpenAI API의 기본 사용법
  - Streaming 방식 응답 처리
  - 토큰 관리와 비용 최적화의 중요성
  - 대화 히스토리 관리 전략

- **다음 주 준비할 것**:
  - RAG 시스템 구현 (문서 기반 질의응답)
  - 정확한 토큰 계산 (tiktoken)
  - 대화 요약 기능 추가
