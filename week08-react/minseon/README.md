# OOTD 스타일리스트 AI — minseon

날씨·옷장·색상 데이터를 분석하여 오늘의 코디를 추천하는 AI 에이전트입니다.
ReAct / Plan-and-Execute 두 가지 에이전트 방식을 모두 지원하며,
의류 사진을 업로드하면 멀티모달 분석으로 코디를 추천받을 수 있습니다.

---

## 기술 스택

| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| LLM | GPT-4o (OpenAI) | Claude, Gemini | Function Calling + Vision 통합 지원, 안정적인 한국어 품질 |
| 에이전트 패턴 | ReAct / Plan-and-Execute | LangChain Agent | 직접 구현으로 동작 과정 투명하게 확인 가능 |
| UI 프레임워크 | Streamlit | Gradio, Flask | 빠른 프로토타이핑, chat_input·camera_input 내장 |
| 날씨 API | 기상청 공공 API (KMA) | OpenWeather | 국내 정확도 우수, 무료 |
| 패키지 관리 | pip + .env | Poetry | 환경 단순화 |

---

## 핵심 구현

### 에이전트 구조

**ReAct 모드**
- 사고(Thought) → 도구 호출(Action) → 결과 관찰(Observation) 루프를 반복
- 최종 답변(`[Final Answer]`)이 나올 때까지 최대 10스텝 반복
- 각 단계가 실시간 스트리밍으로 UI에 표시됨

**Plan-and-Execute 모드**
- Phase 1: 전체 실행 계획을 JSON으로 수립
- Phase 2: 계획에 따라 도구를 순서대로 실행
- Phase 3: 수집된 데이터를 바탕으로 최종 추천 스트리밍 생성

**멀티모달 (사진 추천)**
- 카메라 촬영 또는 이미지 업로드
- GPT-4o Vision으로 의류 색상·스타일·카테고리 분석
- 옷장 데이터 + 날씨 정보와 결합하여 코디 추천

### 사용 도구 (Function Calling)

| 도구 | 설명 |
|------|------|
| `get_weather` | 기상청 API로 현재 기온·날씨·습도 조회 |
| `check_rain_and_umbrella` | 비·눈·고습도 여부 판단 및 우산 알림 |
| `get_wardrobe_items` | 옷장 아이템 조회 (카테고리·계절·날씨 필터) |
| `get_wardrobe_overview` | 옷장 전체 구성 요약 |
| `get_color_pairings` | 색채학 기반 색상 조합 추천 |
| `get_season_palette` | 계절별 추천 색상 팔레트 |

### 주요 파일

```
ootd_agent/
├── app.py                  # Streamlit UI + 에이전트 스트리밍 로직
├── function_calling.py     # OpenAI Tool 스키마 + 실행 디스패처
├── wardrobe.json           # 옷장 데이터 (34개 아이템)
├── colorhunt_scraper.py    # ColorHunt 색상 팔레트 스크레이퍼
├── tools/
│   ├── weather.py          # 기상청 API 날씨 조회
│   ├── wardrobe.py         # 옷장 CRUD
│   └── colors.py           # 색상 조합 데이터
└── .env                    # API 키 (KMA_API_KEY, OPENAI_API_KEY)
```

### 코드 실행 방법

```bash
# 1. 패키지 설치
pip install streamlit openai python-dotenv requests

# 2. .env 파일에 API 키 입력
# KMA_API_KEY=발급받은키
# OPENAI_API_KEY=sk-proj-...

# 3. 앱 실행 (Windows 한글 깨짐 방지를 위해 -X utf8 필수)
python -X utf8 -m streamlit run app.py
```

---

## WHY (의사결정 기록)

1. **Q**: ReAct와 Plan-and-Execute를 둘 다 구현한 이유?  
   **A**: 두 방식의 장단점을 직접 비교하기 위해. ReAct는 유연하지만 루프가 불안정할 수 있고, Plan-and-Execute는 예측 가능하지만 계획 단계에서 오류가 생기면 전체가 틀어짐. 사용자가 상황에 맞게 선택할 수 있도록 둘 다 제공.

2. **Q**: LangChain 대신 직접 구현한 이유?  
   **A**: 에이전트 내부 동작(Thought/Action/Observation 흐름)을 UI에 실시간으로 보여주려면 직접 이벤트를 yield하는 방식이 필요했음. LangChain 추상화 레이어가 오히려 스트리밍 커스터마이징을 어렵게 만듦.

3. **Q**: 색상 조합 데이터를 ColorHunt에서 스크레이핑한 이유?  
   **A**: 단순한 보색·유사색 규칙보다 실제 패션에서 쓰이는 색상 조합이 필요했음. ColorHunt의 인기 팔레트를 파싱해서 18가지 색상에 대한 실용적 조합 데이터를 구축.

---

## 트러블슈팅 로그

| # | 문제 상황 | 에러 메시지 | 원인 | 해결 방법 |
|---|----------|-----------|------|----------|
| 1 | Windows 터미널 한글 출력 오류 | `UnicodeEncodeError: 'cp949'` | Windows 기본 인코딩이 cp949 | `python -X utf8` 플래그로 실행 |
| 2 | 탭 추가 후 들여쓰기 오류 | `IndentationError` | `with tab_chat:` 블록 들여쓰기 불일치 | 파일 전체 구조를 읽고 패치 스크립트로 재작성 |
| 3 | ColorHunt 스크레이핑 403 | `HTTPError: 403` | 일반 GET 요청 차단 | POST + 브라우저 헤더로 비공식 feed.php 엔드포인트 호출 |
| 4 | Streamlit 응답 후 내용이 사라짐 | (없음) | `stream_placeholder.empty()` → `st.rerun()` 이중 렌더링 | placeholder에 최종 내용 덮어쓰고 `st.rerun()` 제거 |
| 5 | 사이드바 텍스트가 안 보임 | (없음) | Streamlit 다크 테마 영향으로 텍스트 흰색 렌더링 | CSS `[data-testid="stSidebar"] * { color: #1a1a1a }` 추가 |

---

## 회고

- **배운 점**:
  - ReAct 에이전트를 직접 구현하면서 LLM의 추론 루프 구조를 깊이 이해함
  - Streamlit의 `st.empty()`와 generator 기반 스트리밍을 조합하는 방법 습득
  - OpenAI Function Calling과 Vision API를 하나의 파이프라인에서 함께 사용하는 방법 학습
  - 색상 조합을 단순 규칙이 아닌 실제 팔레트 데이터로 구성하는 방법 경험

- **다음에 개선할 것**:
  - 옷장 아이템을 UI에서 직접 추가/삭제할 수 있는 관리 기능
  - 날씨 예보(내일, 주간) 기반 코디 추천 기능
  - 추천 결과 저장 및 히스토리 조회 기능
