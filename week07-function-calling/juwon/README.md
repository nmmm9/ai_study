# 7주차: Function Calling - juwon

## 기술 스택

| 항목      | 선택                 | 대안             | 선택 이유                                   |
| ------- | ------------------ | -------------- | --------------------------------------- |
| 언어      | Python 3.13        | JavaScript     | 데이터 처리 및 AI 라이브러리 생태계가 풍부               |
| LLM API | OpenAI GPT-4o-mini | Claude, Gemini | 기존 보유 API 키 활용, Function Calling 지원 안정적 |
| 날씨 API  | Open-Meteo         | OpenWeatherMap | 완전 무료, API 키 불필요                        |
| 환경변수 관리 | python-dotenv      | 직접 환경변수 설정     | .env 파일로 키 관리 간편, .gitignore로 보안 유지     |

---

## 핵심 구현

* **주요 로직 설명**:

  * `tools.py`: 여행 관련 함수 4개 구현 + 각 함수의 JSON 스키마 정의

    * `get_weather` : Open-Meteo API로 실시간 날씨 조회
    * `search_attractions` : 도시별 관광지/맛집 검색 (샘플 DB)
    * `calculate_budget` : 숙박/식비/교통/활동비 항목별 예산 계산
    * `get_best_season` : 도시별 여행 최적 시기 안내

  * `agent.py`:
    OpenAI API에 함수 목록(TOOLS)을 전달 →
    AI가 질문 의도에 맞는 함수 선택 →
    함수 실행 → 결과를 다시 AI에게 전달 →
    최종 자연어 답변 생성

  * `main.py`: 터미널 기반 대화 인터페이스, 대화 히스토리 유지

---

* **코드 실행 방법**:

```bash
# 1. 라이브러리 설치
pip install -r requirements.txt

# 2. .env 파일에 OpenAI API 키 입력
# OPENAI_API_KEY=sk-...

# 3. 실행
python main.py
```

---

## WHY (의사결정 기록)

1. **Q**: 왜 이 방식을 선택했는가?
   **A**:
   Function Calling 구조를 통해 AI가 단순 응답 생성이 아니라, 사용자 질문 의도를 분석하고 적절한 외부 함수를 선택하여 실행하도록 하기 위함이다. 이를 통해 더 정확하고 신뢰성 있는 결과를 제공할 수 있으며, AI와 실제 로직(함수)의 역할을 분리하는 구조를 이해하는 데 목적이 있다. 또한 함수 수를 4개로 제한하여 각 기능의 역할을 명확히 하고, AI가 혼동 없이 적절한 함수를 선택할 수 있도록 설계하였다.

2. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**:
   실제 서비스 수준으로 확장한다면 항공권 및 숙소 정보를 제공하기 위해 Amadeus API나 Google Places API를 연동할 수 있다. 또한 현재는 터미널 기반 인터페이스를 사용하고 있지만, Streamlit이나 웹 프레임워크를 활용하여 사용자 친화적인 UI를 구축할 수 있다.

---

## 트러블슈팅 로그

| # | 문제 상황              | 에러 메시지                                                      | 원인 (Root Cause)                         | 해결 방법                             |
| - | ------------------ | ----------------------------------------------------------- | --------------------------------------- | --------------------------------- |
| 1 | API 호출 시 인코딩 오류 발생 | `UnicodeEncodeError: 'ascii' codec can't encode characters` | .env 파일에 API 키 대신 한글 placeholder가 남아있었음 | .env에 실제 OpenAI API 키 입력          |
| 2 | git push 거절        | `[rejected] juwon -> juwon (fetch first)`                   | 원격 브랜치에 다른 팀원이 먼저 push한 커밋이 존재          | `git pull origin juwon` 후 다시 push |

---

## 회고

* **이번 주 배운 점**:
  Function Calling은 AI가 모든 작업을 수행하는 것이 아니라, 상황에 따라 적절한 함수를 선택하고 실행을 위임하는 구조라는 점을 이해하였다. 특히 JSON 스키마의 description을 명확하게 작성하는 것이 함수 선택 정확도에 큰 영향을 준다는 점을 알게 되었다.

* **다음 주 준비할 것**:
  ReAct / Plan-and-Execute 프레임워크를 학습하여, AI가 단일 함수 호출을 넘어 여러 단계를 계획하고 순차적으로 실행하는 구조를 구현할 예정이다.
