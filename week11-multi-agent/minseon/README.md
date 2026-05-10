# 11주차: Multi-Agent — 청년정책 멀티에이전트 AI

> 7개 전문 에이전트 협업 · 자연어 대화로 프로필 수집  
> 온통청년 495개 정책 연동 · 실시간 관련 사이트 링크 제공

---

## 기술 스택

| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| 에이전트 프레임워크 | LangGraph | CrewAI, AutoGen | 조건부 분기·루프·상태 관리가 직관적 |
| LLM | GPT-4o / GPT-4o-mini | Claude, Gemini | 기존 API 키 재사용, 비용 절감 |
| 멀티에이전트 패턴 | 오케스트레이터 + 전문 에이전트 | 동등 협업(Peer) | 역할 명확화, 선택 실행으로 비용 최적화 |
| 데이터 수집 | 온통청년 POST API | 공공데이터포털, 크롤링 | API 역분석으로 1,895개 정책 즉시 접근 |
| 검색 | 키워드 매칭 | RAG(벡터) | 495개 수준에서 속도·비용 균형 |
| UI | Streamlit 커스텀 CSS | FastAPI+React | 빠른 프로토타이핑, 상용 챗봇 수준 구현 |

---

## 핵심 구현

### 멀티에이전트 구조

```
START → conversation_node (대화로 프로필 수집)
            ↓ [profile_complete?]
            ├─ 아직 → END (다음 입력 대기)
            └─ 완성 → orchestrator_node (에이전트 선택)
                            ↓
                    scholarship_node  (장학금 전문)
                    employment_node   (취업 전문)
                    housing_node      (주거 전문)
                    finance_node      (금융 전문)
                            ↓
                    synthesizer_node → TOP 3 추천 → END
```

### 7개 에이전트 역할

| 에이전트 | 역할 | 특징 |
|---------|------|------|
| `conversation_node` | 나이·지역·상황·관심분야 수집 | 멀티턴 대화, `<PROFILE>` 태그 감지 |
| `orchestrator_node` | 전문 에이전트 선택 | GPT-4o-mini가 최적 조합 결정 |
| `scholarship_node` | 장학금·교육비 전담 | 선택된 경우만 실행 |
| `employment_node` | 취업·일자리 전담 | 선택된 경우만 실행 |
| `housing_node` | 주거·월세 전담 | 선택된 경우만 실행 |
| `finance_node` | 금융·적금 전담 | 선택된 경우만 실행 |
| `synthesizer_node` | 결과 통합 | TOP 3 추천 + 신청 순서 + 중복 가이드 |

### 온통청년 API 수집

```python
# DevTools Network 탭에서 역분석한 엔드포인트
POST https://www.youthcenter.go.kr/pubot/search/portalPolicySearch

payload = {"query": "청년", "pageNum": 1, "listCount": 100, "searchFields": "all"}
items   = resp.json()["searchResult"]["youthpolicy"]  # 리스트 직접 반환
```

- 총 1,895개 정책 / 500개 수집 → 479개 MD 저장
- HTML 태그 자동 제거: `re.sub(r"<[^>]+>", "", text)`

### 관련 사이트 자동 링크

답변 키워드 분석 → 관련 사이트 자동 추출:

| 키워드 | 연결 사이트 |
|--------|------------|
| 취업, 일자리 | 고용24, 청년일자리 |
| 장학금, 학자금 | 국가장학금, 한국장학재단 |
| 주거, 월세, 청약 | 청약홈, 마이홈 |
| 적금, 금융 | 서민금융진흥원 |
| 청년, 정책 | 온통청년, 복지로 |

### 코드 실행 방법

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. .env 파일 설정
# OPENAI_API_KEY=sk-...

# 3. 정책 데이터 수집 (최초 1회, 약 1~2분)
python tools/youthcenter_crawler.py

# 4. 앱 실행
python -X utf8 -m streamlit run app.py
```

---

## WHY (의사결정 기록)

1. **Q**: 왜 에이전트를 7개로 분리했는가?
   **A**: 하나의 에이전트에 모든 분야를 맡기면 프롬프트가 길어지고 각 분야의 깊이 있는 분석이 어렵다. 전문화로 도메인별 정확도를 높이고, 오케스트레이터가 필요한 에이전트만 선택해 API 비용도 절감한다.

2. **Q**: 왜 폼 입력 대신 자연어 대화를 선택했는가?
   **A**: 폼은 UX가 딱딱하고 이탈률이 높다. 자연어 대화는 ChatGPT·Claude와 동일한 경험을 제공하며, 사용자가 자연스럽게 필요한 정보를 제공하게 된다.

3. **Q**: 왜 공공데이터포털 대신 온통청년 API를 역분석했는가?
   **A**: 공공데이터포털 API 승인이 1~2일 소요되지만, 온통청년은 DevTools로 즉시 발견·사용 가능했다. 결과적으로 1,895개 정책에 직접 접근해 훨씬 많은 데이터를 확보했다.

4. **Q**: 왜 UI를 대폭 개선했는가?
   **A**: week10까지는 Streamlit 기본 UI라 학습 프로젝트 느낌이 강했다. 커스텀 CSS로 실제 서비스 수준의 UX를 목표로 했다. 색상 대비 원칙(흰 배경→검정 글자, 파란 배경→흰 글자)을 적용해 가독성을 확보했다.

---

## 트러블슈팅 로그

| # | 문제 | 에러 | 원인 | 해결 |
|---|------|------|------|------|
| 1 | API 응답 파싱 실패 | `AttributeError: list has no attribute 'get'` | `searchResult["youthpolicy"]`가 dict가 아닌 list | `isinstance` 체크 후 직접 사용 |
| 2 | 정책명에 HTML 태그 포함 | `중랑<span class="highlight">청년</span>청` | API가 검색어를 highlight 처리 | `re.sub(r"<[^>]+>", "", text)` 추가 |
| 3 | 사용자 버블 글자 안 보임 | (UI 깨짐) | 파란 배경에 다크 텍스트 충돌 | `.bubble.user *` 전체 `color:#fff` 강제 |
| 4 | OPENAI_API_KEY 오류 | `OpenAIError: api_key must be set` | week11 폴더에 `.env` 없음 | week10에서 `.env` 복사 |
| 5 | 페이지당 100개만 수집 | (데이터 부족) | max_count 기본값 50 | `max_count=500`으로 수정 |

---

## 회고

- **이번 주 배운 점**:
  - 멀티에이전트 오케스트레이터 패턴: 역할 분리로 전문성 극대화
  - LangGraph 멀티턴 대화: `profile_complete` 플래그로 대화/분석 모드 전환
  - DevTools로 내부 API 역분석하는 실전 기술 (DevTools → Network → Fetch/XHR)
  - CSS 커스터마이징으로 Streamlit을 상용 챗봇 수준으로 개선
  - 색상 대비 원칙: 흰 배경→검정 글자 / 파란 배경→흰 글자

- **다음 주 준비할 것**:
  - 전문 에이전트 병렬 실행으로 응답 속도 개선
  - 벡터 DB 도입으로 시맨틱 검색 적용
  - 사용자별 대화 이력 저장 (세션 영속성)
