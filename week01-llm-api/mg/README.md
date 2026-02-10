# 1주차: LLM API 연동 - mg

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| LLM (메인) | GPT-4o | Claude Sonnet 4.5 | 가격 대비 성능, 128K 컨텍스트 |
| LLM (비교) | Claude Sonnet 4.5 | - | Anthropic API 비교 학습용 |
| API Key 관리 | python-dotenv | 환경변수 직접 설정 | .env 파일로 관리가 편리 |
| 패키지 관리 | pip + venv | conda | 가볍고 표준적 |

## 핵심 구현
- 주요 로직 설명:
  - `main.py` — OpenAI GPT-4o 기반 터미널 챗봇 (Streaming, 대화 기록 유지)
  - `anthropic_chat.py` — Anthropic Claude 기반 터미널 챗봇 (Streaming, 대화 기록 유지)
  - 두 파일 모두 `.env`에서 API Key를 불러오고, 스트리밍 응답을 실시간 출력
- 코드 실행 방법:
  ```bash
  # 1. 가상환경 생성 및 활성화
  python -m venv .venv
  .venv\Scripts\activate  # Windows

  # 2. 패키지 설치
  pip install -r requirements.txt

  # 3. API Key 설정
  cp .env.example .env
  # .env 파일에 본인 API Key 입력

  # 4. 실행
  python main.py            # OpenAI 챗봇
  python anthropic_chat.py  # Anthropic 챗봇
  ```

## WHY (의사결정 기록)
1. **Q**: 왜 이 방식을 선택했는가?
   **A**: OpenAI와 Anthropic 두 API를 모두 구현해서 차이점을 직접 체감하기 위해 분리. Streaming을 기본으로 적용해 실제 서비스와 유사한 UX 구현.
2. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**: LangChain의 ChatOpenAI/ChatAnthropic으로 통합 인터페이스를 사용하면 모델 교체가 더 쉬움. 2주차부터 LangChain 기반으로 전환 예정.

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | | | | |

## 회고
- 이번 주 배운 점:
- 다음 주 준비할 것:
