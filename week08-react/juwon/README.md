# 8주차: ReAct / Plan-and-Execute - juwon

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| LLM API | OpenAI gpt-4o-mini | Claude, Gemini | 7주차와 동일한 환경 유지 |
| Agent 패턴 | ReAct + Plan-and-Execute | ReAct 단독 | 계획적 실행 + 유연한 반복을 동시에 구현 |
| UI | Streamlit | 터미널, Flask | 채팅 UI와 결과물을 한 화면에 통합 |
| 결과 출력 | HTML 보고서 | 텍스트 출력 | 시각적으로 완성도 높은 여행 계획서 생성 |
| 날씨 API | Open-Meteo | OpenWeather | 무료, API 키 불필요 |

## 핵심 구현

### 주요 로직 설명

**전체 흐름: Plan → Execute → Output**

```
사용자 질문
    ↓
Phase 1. plan_phase()       ← Plan-and-Execute
  AI가 JSON 실행 계획 수립
  {"city": "제주", "days": 4, "steps": [...]}
    ↓
Phase 2. react_execute()    ← ReAct 루프
  while 반복:
    Thought: 다음에 뭘 할지 AI가 판단
    Action:  도구 호출 (10개 중 선택)
    Observe: 결과 확인 → 다음 반복
  완료 판단 시 루프 종료
    ↓
Phase 3. generate_html()    ← 보고서 생성
  수집된 모든 데이터 → HTML 여행 계획서
```

**7주차와 핵심 차이: while 루프 하나**
```python
# 7주차: 1번 호출로 끝
response = client.chat(messages, tools=TOOLS)

# 8주차: 루프로 여러 번 반복
while iteration < 25:
    response = client.chat(messages, tools=TOOLS)
    if tool_calls:
        result = execute_tool()
        messages.append(result)  # 결과 누적 후 재판단
    else:
        break  # AI가 완료 판단
```

**사용 도구 (10개)**
| 함수 | 역할 |
|------|------|
| get_weather | 실시간 날씨 조회 (Open-Meteo API) |
| search_attractions | 관광지 검색 |
| search_restaurants | 맛집 검색 |
| search_accommodation | 숙소 추천 |
| get_transportation | 교통편 정보 |
| calculate_budget | 예산 계산 |
| get_best_season | 여행 최적 시기 |
| get_festivals | 축제/행사 정보 |
| get_local_tips | 여행 꿀팁 |
| create_itinerary | 날짜별 일정표 생성 |

### 코드 실행 방법

```bash
# 1. 폴더 이동
cd "c:\윤주원\ai study\ai_study\week08-react\juwon"

# 2. .env 파일에 OpenAI 키 입력
# OPENAI_API_KEY=sk-proj-...

# 3. Streamlit 실행
streamlit run app.py
```

## WHY (의사결정 기록)

1. **Q**: 왜 ReAct와 Plan-and-Execute를 둘 다 사용했는가?
   **A**: Plan-and-Execute만 쓰면 계획대로만 실행해 유연성이 부족하고, ReAct만 쓰면 복잡한 질문에서 방향을 잃을 수 있다. 두 패턴을 결합하면 Plan-and-Execute가 큰 틀을 잡고, ReAct가 각 단계를 유연하게 실행하므로 완성도가 높아진다.

2. **Q**: 터미널 대신 Streamlit을 선택한 이유는?
   **A**: 터미널은 채팅과 결과물이 분리되어 사용성이 떨어진다. Streamlit을 사용하면 채팅 UI, ReAct 실행 로그, HTML 여행 계획서를 한 화면에서 확인할 수 있어 사용자 경험이 크게 개선된다.

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | API 호출 실패 | UnicodeEncodeError: 'ascii' codec can't encode characters | .env 파일이 UTF-8 BOM으로 저장되어 API 키 앞에 \ufeff 문자가 붙음 | api_key.strip('\ufeff')로 BOM 문자 제거 |

## 회고
- 이번 주 배운 점: Function Calling(7주차)은 함수를 1번 호출하는 것이고, ReAct는 while 루프로 AI가 스스로 판단하며 여러 번 반복 호출하는 것임을 코드로 직접 확인했다. Plan-and-Execute로 전체 계획을 먼저 세우면 AI가 더 체계적으로 작동한다는 것도 배웠다.
- 다음 주 준비할 것: LangGraph - 지금은 while 루프로 구현한 ReAct 흐름을 그래프(Nodes, Edges) 구조로 시각화하는 방법 학습 예정
