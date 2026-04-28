# 9주차: LangGraph 입문 - juwon

## 기술 스택
| 항목 | 선택 | 이유 |
|------|------|------|
| LLM API | OpenAI gpt-4o-mini | 8주차와 동일 환경 |
| Agent 프레임워크 | LangGraph | 그래프 기반 워크플로우 학습 |
| 데이터 소스 | GitHub Search API | 무료, 실시간 데이터 |
| UI | Streamlit | 대시보드 + 차트 통합 |
| 스케줄링 | APScheduler | 매일 자동 실행 |
| 저장 | JSON 파일 | 히스토리 관리 |

## 핵심 구현

### LangGraph 흐름

```
[collect] → [validate] → [analyze] → [compare] → [report]
                ↑___________↓
           (데이터 부족 시 재수집, 최대 3회)
```

### 8주차 vs 9주차

```python
# 8주차: while 루프로 직접 관리
while iteration < 25:
    response = client.chat(messages, tools=TOOLS)
    if tool_calls:
        execute_tool()
    else:
        break

# 9주차: LangGraph가 흐름 관리
graph.add_node("collect",  collect_node)
graph.add_node("validate", validate_node)
graph.add_node("analyze",  analyze_node)
graph.add_conditional_edges("validate", should_retry, {
    "retry":   "collect",
    "analyze": "analyze",
})
```

### 파일 구조

| 파일 | 역할 |
|------|------|
| `github_tools.py` | GitHub Search API 호출 |
| `storage.py` | JSON 히스토리 저장/불러오기 |
| `graph.py` | LangGraph 노드 + 엣지 정의 |
| `app.py` | Streamlit 대시보드 |

### 코드 실행 방법

```bash
# 1. 폴더 이동
cd "c:\윤주원\ai study\ai_study\week09-langgraph\juwon"

# 2. 패키지 설치
pip install -r requirements.txt

# 3. .env 파일 설정
# OPENAI_API_KEY=sk-...
# GITHUB_TOKEN=ghp_...

# 4. 실행
streamlit run app.py
```

## WHY (의사결정 기록)

1. **Q**: 왜 LangGraph를 쓰나?
   **A**: 8주차의 while 루프는 흐름을 코드로만 파악해야 했다. LangGraph는 노드/엣지 구조로 흐름을 명시적으로 설계할 수 있어서 유지보수와 확장이 쉽다.

2. **Q**: conditional_edge가 왜 중요한가?
   **A**: "데이터 부족 → 재수집"처럼 조건에 따라 흐름을 바꾸는 게 실무에서 자주 필요하다. while 루프로 하면 복잡해지지만 LangGraph는 한 줄로 표현 가능하다.

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | | | | |

## 회고
- 이번 주 배운 점: LangGraph는 while 루프를 그래프 구조로 바꾼 것. 노드가 함수, 엣지가 실행 순서, conditional_edge가 if/else에 해당한다.
- 다음 주 준비할 것: Multi-Agent, 더 복잡한 그래프 설계
