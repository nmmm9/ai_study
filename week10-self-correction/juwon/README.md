# 10주차: Self-Correction - juwon

## 기술 스택
| 항목 | 선택 | 이유 |
|------|------|------|
| LLM API | OpenAI gpt-4o-mini | 9주차와 동일 환경 |
| Agent 프레임워크 | LangGraph | 그래프 기반 Self-Correction 루프 |
| 데이터 소스 | GitHub Search API | 무료, 실시간 데이터 |
| UI | Streamlit | 품질 점수 + 반성 이력 시각화 |
| 알림 | Gmail SMTP + GitHub API | 분석 결과 자동 발송/업로드 |
| 저장 | JSON 파일 | 히스토리 관리 |

## 핵심 구현

### LangGraph 흐름

```
[collect] → [validate] → [generate] → [reflect] → [compare] → [notify] → [report]
               ↑__↓                       ↑__↓
          (데이터 부족 시)          (품질 70점 미만 시
           재수집, 최대 3회)         재생성, 최대 3회)
```

### 9주차 vs 10주차

```python
# 9주차: analyze 노드 하나로 분석
graph.add_edge("validate", "analyze")

# 10주차: generate → reflect 루프
graph.add_edge("generate", "reflect")
graph.add_conditional_edges("reflect", should_regenerate, {
    "regenerate": "generate",  # 70점 미만이면 피드백 반영 재생성
    "compare":    "compare",   # 70점 이상이면 진행
})
```

### 품질 검토 기준 (reflect 노드)

| 기준 | 점수 | 조건 |
|------|------|------|
| 분석 길이 | 20점 | 300자 이상 |
| 트렌드 키워드 | 25점 | 3개 이상 |
| 구체적 레포 이름 | 25점 | 3개 이상 |
| 인사이트 수 | 15점 | 3개 이상 |
| 기술 방향성 | 15점 | 2개 이상 |
| **합계** | **100점** | **70점 이상 통과** |

### 파일 구조

| 파일 | 역할 |
|------|------|
| `github_tools.py` | GitHub Search API 호출 |
| `storage.py` | JSON 히스토리 저장/불러오기 |
| `graph.py` | LangGraph 노드 + 엣지 (Self-Correction 포함) |
| `notifier.py` | Gmail SMTP + GitHub README 업로드 |
| `app.py` | Streamlit 대시보드 (품질 지표 포함) |

### 코드 실행 방법

```bash
# 1. 폴더 이동
cd "c:\윤주원\ai study\ai_study\week10-self-correction\juwon"

# 2. 패키지 설치
pip install -r requirements.txt

# 3. .env 파일 설정 (.env.example 참고)
# OPENAI_API_KEY=sk-...
# GITHUB_TOKEN=ghp_...
# GMAIL_USER=yoonjuwon0618@gmail.com
# GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx  ← Google 앱 비밀번호
# GITHUB_TREND_REPO=owner/repo-name

# 4. 실행
streamlit run app.py
```

### Gmail 앱 비밀번호 발급 방법

1. Google 계정 → 보안 → 2단계 인증 활성화
2. 보안 → 앱 비밀번호 → 앱: 메일, 기기: Windows 컴퓨터
3. 생성된 16자리 비밀번호를 `GMAIL_APP_PASSWORD`에 입력

## WHY (의사결정 기록)

1. **Q**: 왜 Self-Correction을 별도 노드(reflect)로 만들었나?
   **A**: LangGraph의 장점을 활용하기 위해. reflect 노드를 독립적으로 분리하면 품질 기준을 수정할 때 generate 노드는 건드리지 않아도 된다.

2. **Q**: 70점 기준은 어떻게 정했나?
   **A**: 5개 기준 중 3~4개 통과 시 통과하는 수준. 너무 높으면 무한루프, 너무 낮으면 의미 없어서 중간값으로 설정.

3. **Q**: Gmail vs GitHub README — 둘 다 쓰는 이유?
   **A**: Gmail은 팀원에게 빠르게 공유, README는 히스토리가 남아서 나중에 참조 가능. 용도가 다름.

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | | | | |

## 회고
- 이번 주 배운 점: AI가 스스로 결과를 검토하고 개선하는 Self-Correction은 "if 조건 → 재실행"을 그래프 엣지로 표현한 것. 품질 기준을 명확히 정하는 것이 핵심.
- 다음 주 준비할 것: Multi-Agent (여러 에이전트가 협력하는 구조)
