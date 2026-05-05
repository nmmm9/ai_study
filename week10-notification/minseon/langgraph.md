# LangGraph 구조 설명

## LangGraph란?

LangGraph는 AI 에이전트의 **흐름(Flow)을 그래프로 정의**하는 프레임워크입니다.

일반 LLM 호출은 단순히 입력 → 출력이지만,  
LangGraph는 여러 단계를 **노드(Node)** 로 나누고, 조건에 따라 다른 경로로 분기할 수 있습니다.

```
일반 LLM:   질문 → GPT → 답변

LangGraph:  질문 → [분석] → [검색] → [필터] → [답변]
                              ↑           |
                              └── 결과 없으면 재시도
```

---

## 핵심 개념

### State (상태)

노드 간에 공유되는 데이터 묶음입니다.  
한 노드가 업데이트하면 다음 노드가 그 값을 받아서 씁니다.

```python
# state.py
class NotifyState(TypedDict, total=False):
    user_query:    str    # 사용자 질문
    user_age:      int    # 나이
    user_region:   str    # 지역
    keywords:      list   # 검색 키워드
    search_results: list  # 검색 결과
    recommendation: str   # 최종 답변
    email_sent:    bool   # 이메일 발송 여부
```

`total=False` 이므로 모든 키는 선택 사항입니다.  
각 노드는 자기가 담당하는 키만 반환(업데이트)하면 됩니다.

---

### Node (노드)

하나의 작업 단위입니다. **State를 받아서 → 처리 후 → 변경된 키만 반환**합니다.

```python
def chat_search_node(state: NotifyState) -> dict:
    keywords = state.get("keywords", [])        # State에서 읽기
    results  = search_policies(keywords)        # 처리
    return {"search_results": results}          # State 일부만 반환
```

반환한 값은 자동으로 기존 State에 **병합(merge)** 됩니다.

---

### Edge (엣지)

노드 간의 연결입니다.

```python
# 단순 엣지: A 끝나면 반드시 B로
g.add_edge("profile_build_node", "search_node")

# 조건부 엣지: 함수 결과에 따라 분기
g.add_conditional_edges(
    "search_node",
    route_by_results,               # 분기 함수
    {"retry": "search_node",        # "retry" 반환 시 → 자기 자신으로 루프
     "proceed": "match_node"},      # "proceed" 반환 시 → 다음 노드로
)
```

---

## week10의 두 그래프

### 1. chat_graph — 챗봇 답변용

```
START
  │
  ▼
chat_parse_node         질문 유형 분석 (specific / general)
  │
  ▼  [chat_route_by_type]
  ├─ general  → chat_profile_node    로그인 사용자 프로필 주입
  │                  │
  └─ specific ────── ┤
                     ▼
              chat_search_node       정책 DB 키워드 검색
                     │
                     ▼  [chat_route_by_results]
                     ├─ retry   → chat_search_node  (결과 없으면 재검색)
                     └─ proceed → chat_recommend_node
                                        │
                                        ▼
                                       END
```

#### 각 노드 역할

| 노드 | 입력 (State 읽기) | 처리 | 출력 (State 갱신) |
|------|-----------------|------|-----------------|
| `chat_parse_node` | `user_query` | GPT-4o-mini로 질문 분석 | `query_type`, `keywords`, `query_category` |
| `chat_profile_node` | `user_query`, `user_profile` | 로그인 정보 주입 or LLM 추출 | `user_profile`, `keywords` (보강) |
| `chat_search_node` | `keywords`, `query_category` | 로컬 정책 MD 파일 검색 | `search_results`, `search_retry_count` |
| `chat_recommend_node` | `user_query`, `user_profile`, `search_results` | GPT-4o 마크다운 답변 생성 | `recommendation` |

#### 로그인 사용자 vs 비로그인 사용자 차이

```
비로그인:  "나 25살 서울인데" → chat_parse_node가 텍스트에서 나이·지역 추출
로그인:    DB에 저장된 나이·지역이 자동으로 user_profile에 주입됨
           → chat_profile_node에서 LLM 추출 생략, 검색 키워드만 보강
```

---

### 2. notify_graph — 이메일 자동 알림용

```
START
  │
  ▼
profile_build_node      나이·지역 → 검색 키워드 생성
  │
  ▼
search_node             정책 DB 전체 검색 (top 8)
  │
  ▼  [route_by_results]
  ├─ retry   → search_node        (결과 없으면 전체 DB 재검색)
  └─ proceed → match_node         GPT-4o 조건 매칭 + HTML 생성
                   │
                   ▼  [route_by_match]
                   ├─ send → notify_node   Gmail SMTP 발송
                   │              │
                   └─ skip        ▼
                                 END
```

#### 각 노드 역할

| 노드 | 입력 (State 읽기) | 처리 | 출력 (State 갱신) |
|------|-----------------|------|-----------------|
| `profile_build_node` | `user_age`, `user_region` | 나이대·지역별 키워드 매핑 | `keywords` |
| `search_node` | `keywords` | 로컬 정책 MD 파일 검색 | `search_results`, `search_retry_count` |
| `match_node` | `user_age`, `user_region`, `search_results` | GPT-4o HTML 본문 생성 | `matched_policies`, `recommendation` |
| `notify_node` | `user_name`, `user_email`, `recommendation` | Gmail SMTP 발송, DB 기록 | `email_sent` |

---

## 조건부 라우터 (Router)

분기 함수는 State를 받아서 **문자열(경로 이름)을 반환**합니다.

```python
# 검색 결과가 있는지 확인
def route_by_results(state: NotifyState) -> str:
    results     = state.get("search_results", [])
    retry_count = state.get("search_retry_count", 0)

    if not results and retry_count <= 1:
        return "retry"    # → search_node로 다시
    return "proceed"      # → match_node로
```

```python
# 이메일 발송 여부 확인
def route_by_match(state: NotifyState) -> str:
    if state.get("user_email") and state.get("recommendation"):
        return "send"     # → notify_node로
    return "skip"         # → END로
```

---

## 그래프 조립 코드 구조

```python
from langgraph.graph import StateGraph, START, END

g = StateGraph(NotifyState)   # 1. State 타입으로 그래프 생성

# 2. 노드 등록
g.add_node("search_node", search_node)
g.add_node("match_node",  match_node)

# 3. 엣지 연결
g.add_edge(START, "search_node")           # 시작점
g.add_conditional_edges(                   # 조건부 분기
    "search_node",
    route_by_results,
    {"retry": "search_node", "proceed": "match_node"},
)
g.add_edge("match_node", END)              # 종료점

graph = g.compile()                        # 4. 컴파일
result = graph.invoke(initial_state)       # 5. 실행
```

---

## week09 → week10 변화 요약

| | week09 | week10 |
|---|---|---|
| 그래프 수 | 1개 | **2개** (chat_graph + notify_graph) |
| 입력 방식 | 자유 텍스트 질문 | 로그인 정보 자동 주입 |
| 종료 조건 | 답변 생성 | 답변 생성 **또는** 이메일 발송 |
| 루프 | search retry | search retry (동일) |
| 새 노드 | — | `profile_build_node`, `match_node`, `notify_node` |
| 상태 추가 | — | `email_sent`, `matched_policies`, `user_email` |

---

## 실행 추적 (execution_trace)

모든 노드는 실행 후 State의 `execution_trace`에 기록을 남깁니다.

```python
def _add_trace(state, node, summary):
    trace = list(state.get("execution_trace", []))
    trace.append({"node": node, "summary": summary})
    return trace

# 노드 내부에서:
return {
    "search_results":  results,
    "execution_trace": _add_trace(state, "search_node", f"{len(results)}개 검색"),
}
```

Streamlit UI에서 이 리스트를 읽어서 실행 추적 UI로 표시합니다.

```
✅ 질문 분석   general / 취업 / ['취업', '청년', '구직']
✅ 프로필 반영  나이=25세, 지역=서울
✅ 정책 검색   5개 검색 (retry=0)
✅ 맞춤 답변   맞춤 답변 생성 완료
```
