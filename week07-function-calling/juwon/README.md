# 7주차: Function Calling - juwon

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| 언어 | Python 3.13 | JavaScript | 데이터 처리 및 AI 라이브러리 생태계가 풍부 |
| LLM API | OpenAI GPT-4o-mini | Claude, Gemini | 기존 보유 API 키 활용, Function Calling 지원 안정적 |
| 날씨 API | Open-Meteo | OpenWeatherMap | 완전 무료, API 키 불필요 |
| 환경변수 관리 | python-dotenv | 직접 환경변수 설정 | .env 파일로 키 관리 간편, .gitignore로 보안 유지 |

## 핵심 구현
- **주요 로직 설명**:
  - `tools.py`: 여행 관련 함수 4개 구현 + 각 함수의 JSON 스키마 정의
    - `get_weather` : Open-Meteo API로 실시간 날씨 조회
    - `search_attractions` : 도시별 관광지/맛집 검색 (샘플 DB)
    - `calculate_budget` : 숙박/식비/교통/활동비 항목별 예산 계산
    - `get_best_season` : 도시별 여행 최적 시기 안내
  - `agent.py`: OpenAI API에 함수 목록(TOOLS)을 전달 → AI가 질문 의도에 맞는 함수를 선택 → 함수 실행 → 결과를 다시 AI에게 전달 → 최종 자연어 답변 생성
  - `main.py`: 터미널 기반 대화 인터페이스, 대화 히스토리 유지

- **코드 실행 방법**:
  ```bash
  # 1. 라이브러리 설치
  pip install -r requirements.txt

  # 2. .env 파일에 OpenAI API 키 입력
  # OPENAI_API_KEY=sk-...

  # 3. 실행
  python main.py
  ```

## WHY (의사결정 기록)
1. **Q**: 왜 함수를 4개로 제한했는가?
   **A**: 함수 수가 많을수록 AI가 어떤 함수를 써야 할지 혼동할 수 있음. 7주차는 Function Calling 구조 이해가 목표이므로 역할이 명확한 4개로 집중. 각 함수의 description을 구체적으로 작성해 AI가 정확히 선택하도록 설계.

2. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**: 항공권/숙소 실시간 데이터가 필요하면 Amadeus API(테스트 환경 무료)나 Google Places API를 연동할 수 있음. 또한 Streamlit으로 웹 UI를 붙이면 터미널 없이도 사용 가능한 서비스로 발전 가능.

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | API 호출 시 인코딩 오류 발생 | `UnicodeEncodeError: 'ascii' codec can't encode characters` | .env 파일에 API 키 대신 한글 placeholder가 그대로 남아있었음 | .env에 실제 OpenAI API 키 입력 |
| 2 | git push 거절 | `[rejected] juwon -> juwon (fetch first)` | 원격 브랜치에 다른 팀원이 먼저 push한 커밋이 존재 | `git pull origin juwon` 후 다시 push |

## 회고
- **이번 주 배운 점**: Function Calling은 AI가 모든 걸 혼자 하는 게 아니라, 사람이 만든 함수를 AI가 상황에 맞게 선택해서 호출하는 구조. AI는 "판단"을 하고 실제 "실행"은 Python 함수가 담당한다는 역할 분리가 핵심. JSON 스키마의 description을 얼마나 명확하게 쓰느냐가 AI의 함수 선택 정확도에 직결됨.
- **다음 주 준비할 것**: ReAct / Plan-and-Execute 프레임워크 - AI가 단순히 함수를 1번 호출하는 것을 넘어, 목표를 달성하기 위해 스스로 계획하고 여러 함수를 순서대로 호출하는 방식 학습 예정.
