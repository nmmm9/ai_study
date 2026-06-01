# 10주차: Self-Correction — 청년정책 자동 알림 에이전트

> LangGraph Self-Correction 패턴으로 검색 품질을 보장하고,  
> 나이·지역 기반 맞춤 정책을 이메일로 자동 발송하는 에이전트

---

## 기술 스택

| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| 에이전트 프레임워크 | LangGraph | LangChain LCEL | 조건부 분기·루프 그래프 표현이 직관적 |
| LLM | GPT-4o / GPT-4o-mini | Claude, Gemini | 이미 보유한 API 키, 빠른 응답 |
| 벡터 검색 | numpy (코사인 유사도) | FAISS, Chroma | 소규모 DB에서 외부 의존성 없이 충분 |
| 임베딩 | text-embedding-3-small | text-embedding-ada-002 | 저렴하고 성능 우수 (1536차원) |
| 이메일 | Gmail SMTP (smtplib) | SendGrid, Mailgun | 추가 비용 없음, 설정 간단 |
| 스케줄러 | APScheduler | Celery, cron | 경량, Python 내장 운용 가능 |
| DB | SQLite | PostgreSQL, MongoDB | 로컬 환경에서 설치 없이 사용 가능 |
| 웹 검색 | Tavily API | SerpAPI, 직접 크롤링 | LangGraph 에이전트 친화적, 무료 1,000회/월 |
| UI | Streamlit | FastAPI + React | 빠른 프로토타이핑, 데이터 앱에 최적 |

---

## 핵심 구현

### 시스템 구조

```
사용자 (비로그인 / 로그인)
        ↓
   Streamlit UI
        ↓
  ┌─────────────────────────────┐
  │       LangGraph             │
  │  chat_graph  notify_graph   │
  │  (챗봇 답변) (이메일 알림)   │
  └─────────────────────────────┘
        ↓
  ┌────────────────────────────────────┐
  │ RAG (text-embedding-3-small+numpy) │
  │ 정책 MD 파일 + Tavily + 공공API    │
  └────────────────────────────────────┘
        ↓
  Gmail SMTP → 이메일 발송
  APScheduler → 매일 09:00 자동 실행
  SQLite → 사용자·발송 이력 저장
```

### Self-Correction 구현

검색 결과가 없으면 자동으로 재검색하는 Reflection 루프:

```python
def route_by_results(state: NotifyState) -> str:
    results     = state.get("search_results", [])
    retry_count = state.get("search_retry_count", 0)

    if not results and retry_count <= 1:
        return "retry"    # search_node로 루프 (카테고리 필터 제거)
    return "proceed"      # match_node로 진행
```

- **1차 검색**: 카테고리 필터 + 키워드 (정확도 우선)
- **Self-Correction 발동**: 결과 0개 감지
- **2차 검색**: 전체 DB에서 키워드만으로 재검색 (재현율 우선)

### 두 개의 LangGraph

| 그래프 | 용도 | 노드 |
|--------|------|------|
| `chat_graph` | 챗봇 답변 | parse → profile → search → recommend |
| `notify_graph` | 이메일 알림 | profile_build → search → match → notify |

### RAG 파이프라인

```
정책 MD 파일 → 단락 청킹(600자) → text-embedding-3-small
→ numpy 배열 저장 → 질문 임베딩 → 코사인 유사도 → Top-K 반환
```

키워드 검색 대비 의미 기반 검색으로 "취업"→"일자리·고용·채용"도 매칭

### 코드 실행 방법

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. .env 파일 설정
# OPENAI_API_KEY=sk-...
# SMTP_USER=gmail주소
# SMTP_PASSWORD=앱비밀번호16자리
# TAVILY_API_KEY=tvly-...  (선택)
# PUBLIC_DATA_API_KEY=...  (선택)

# 3. 앱 실행
python -X utf8 -m streamlit run app.py

# 4. 사이드바 → 벡터 DB 빌드 (최초 1회)
```

---

## WHY (의사결정 기록)

1. **Q**: 왜 그래프를 2개로 분리했는가?
   **A**: 챗봇(사용자 인터랙션)과 알림(자동 배치)은 입력 방식과 종료 조건이 완전히 다르다. 하나의 그래프에 모든 경우를 넣으면 조건부 엣지가 복잡해지고 유지보수가 어려워진다. 관심사 분리(Separation of Concerns) 원칙에 따라 2개로 분리했다.

2. **Q**: FAISS 대신 numpy를 쓴 이유는?
   **A**: 정책 문서가 최대 수백 개 수준이라 FAISS의 인덱스 빌드 오버헤드가 불필요하다. numpy 코사인 유사도로 충분한 성능이 나오고, Windows 환경에서 FAISS 설치 시 바이너리 호환 문제가 자주 발생한다.

3. **Q**: 크롤링 대신 Tavily를 쓴 이유는?
   **A**: youthcenter.go.kr가 JavaScript 렌더링 방식이라 requests+BeautifulSoup으로 접근이 불가능하다. Selenium은 브라우저 실행 오버헤드와 유지보수 비용이 크다. Tavily는 AI 에이전트 전용 검색 API로, 코드가 단순하고 사이트 구조 변경에 영향받지 않는다.

4. **Q**: 로그인 없이도 챗봇을 쓸 수 있게 한 이유는?
   **A**: 이메일과 회원가입이라는 진입 장벽을 낮춰야 더 많은 사용자가 서비스를 경험할 수 있다. 비로그인 사용자도 나이·지역을 임시 입력하면 맞춤 추천을 받을 수 있도록 했다.

---

## 트러블슈팅 로그

| # | 문제 상황 | 에러 메시지 | 원인 | 해결 방법 |
|---|----------|-----------|------|----------|
| 1 | youthcenter.go.kr 크롤링 실패 | `ConnectTimeoutError (port=8080)` | JS 렌더링 사이트 + 잘못된 포트 | Tavily API로 대체 |
| 2 | 이메일 발송 실패 | `SMTPAuthenticationError` | 일반 비밀번호 사용 | Google 앱 비밀번호(16자리)로 교체 |
| 3 | 앱 비밀번호 메뉴 없음 | (구글 계정 설정) | 2단계 인증 미설정 | 2단계 인증 켠 후 재시도 |
| 4 | `NameError: get_fetched_docs` | `name 'get_fetched_docs' is not defined` | import 누락 | `from tools.policy_fetcher import get_fetched_docs` 추가 |
| 5 | 사이드바 입력 글자 안 보임 | (UI 깨짐) | 다크 배경에 다크 텍스트 CSS 충돌 | 사이드바 input 셀렉터에 `color:#fff` 강제 적용 |

---

## 회고

- **이번 주 배운 점**:
  - LangGraph의 `add_conditional_edges`로 루프(Self-Correction)를 구현하는 방법
  - RAG가 단순 키워드 검색과 달리 의미 기반으로 유사 문서를 찾는 원리
  - APScheduler를 Streamlit `@cache_resource`와 함께 써서 백그라운드 스케줄러를 단 한 번만 초기화하는 패턴
  - Gmail SMTP는 일반 비밀번호가 아닌 앱 비밀번호를 사용해야 한다는 점
  - JavaScript 렌더링 사이트는 requests로 접근 불가 → Tavily 같은 대안 필요

- **다음 주 준비할 것**:
  - 실제 공공데이터포털 API 키 발급 후 정책 데이터 대량 수집 테스트
  - 이메일 HTML 템플릿 개선 (더 읽기 쉬운 레이아웃)
  - 벡터 DB 자동 재빌드 스케줄 추가 (새 데이터 수집 시 자동 반영)
  

  cd C:\Users\user\Desktop\ai_study\week10-self-correction\minseon
python -X utf8 -m streamlit run app.py