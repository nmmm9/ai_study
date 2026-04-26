# 9주차: LangGraph 입문 — minseon

청년정책 AI 상담사를 LangGraph 기반 그래프 워크플로우로 구현했습니다.  
week01~06에서 쌓은 청년정책 데이터를 재활용하고, **선언적 그래프 구조**로 에이전트를 설계하는 것이 핵심입니다.

---

## 기술 스택

| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| 워크플로우 | LangGraph `StateGraph` | LangChain AgentExecutor | 노드/엣지 선언적 정의, 조건부 분기·루프가 코드로 명확히 드러남 |
| 상태 관리 | `TypedDict` (total=False) | Pydantic | 노드별 부분 업데이트 허용, 가볍고 직관적 |
| 질문 분석 LLM | Claude Haiku (빠름) | GPT-4o-mini | JSON 추출 전용 — 속도·비용 절약 |
| 최종 추천 LLM | Claude Opus 4-6 | GPT-4o | 품질 우선, 한국어 정책 설명 강점 |
| 정책 검색 | 키워드 기반 텍스트 검색 | Vector DB (ChromaDB) | 의존성 최소화, 데이터 15개로 충분 |
| 데이터 | week02/week04 .md 파일 재사용 | 새로 수집 | 기존 자산 활용 |

---

## 핵심 구현

### 그래프 구조

```
START
  ↓
parse_query_node      ← Claude Haiku: 질문 분석 (type / category / keywords)
  ↓ [route_by_query_type: 조건부 엣지 1]
  ├─ 일반 추천 요청  → profile_node → search_node
  └─ 특정 정책 문의 →               search_node

search_node           ← 키워드·카테고리 기반 정책 문서 검색
  ↓ [route_by_results: 조건부 엣지 2]
  ├─ 결과 0개       → search_node (전체 DB 재검색)
  └─ 결과 있음      → recommend_node

recommend_node        ← Claude Opus: 맞춤 추천 생성
  ↓
END
```

### 조건부 엣지

| 출발 노드 | 조건 | 이동 | 패턴 |
|----------|------|------|------|
| `parse_query_node` | 일반 추천 요청 | `profile_node` | 노드 추가 실행 |
| `parse_query_node` | 특정 정책 문의 | `search_node` (프로필 스킵) | 노드 건너뛰기 |
| `search_node` | 결과 없음 & 재시도 미만 | `search_node` (넓은 검색) | 자기 자신 루프 |
| `search_node` | 결과 있음 | `recommend_node` | 정상 진행 |

### 주요 파일

```
week09-langgraph/minseon/
├── state.py                 # YouthPolicyState TypedDict
├── nodes.py                 # 4개 노드 + 2개 라우터
├── graph.py                 # StateGraph 조립
├── main.py                  # CLI (대화형 + 그래프 시각화)
├── app.py                   # Streamlit UI
├── tools/
│   └── policy_loader.py     # 정책 문서 로드 & 키워드 검색
└── requirements.txt
```

### 코드 실행 방법

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. .env 파일
# ANTHROPIC_API_KEY=sk-ant-...

# 3. CLI (대화형)
python main.py

# 4. 특정 질문
python main.py --query "청년도약계좌 자격조건 알려줘"

# 5. 그래프 구조만 확인
python main.py --visualize

# 6. Streamlit UI
python -X utf8 -m streamlit run app.py
```

pip install -r requirements.txt
python -X utf8 -m streamlit run week09-langgraph/minseon/app.py
---

## WHY (의사결정 기록)

1. **Q**: 청년정책을 주제로 선택한 이유?  
   **A**: week01~06에서 직접 수집·정리한 데이터가 있어 즉시 활용 가능합니다. 본인이 실제 타겟 사용자이므로 도메인 이해가 깊고, 면접에서 "왜 만들었나요?"에 자연스럽게 답할 수 있습니다.

2. **Q**: 질문 유형을 specific/general로 나눈 이유?  
   **A**: "청년도약계좌가 뭐야?"는 바로 검색이 가능하지만, "나한테 맞는 정책 추천해줘"는 사용자 조건(나이·소득·취업상태)을 먼저 파악해야 합니다. 이 두 경로를 조건부 엣지로 분기하면 **불필요한 노드 실행을 방지**합니다.

3. **Q**: Vector DB 대신 키워드 검색을 쓴 이유?  
   **A**: 정책 문서가 15개 내외로 적어 벡터 검색의 이점이 크지 않습니다. 의존성을 줄이고 검색 로직을 투명하게 유지했습니다. week12 Agentic RAG에서 벡터 검색으로 교체 예정입니다.

---

## 트러블슈팅 로그

| # | 문제 상황 | 에러 메시지 | 원인 | 해결 방법 |
|---|----------|-----------|------|----------|
| 1 | | | | |

---

## 회고

- **LangGraph vs week08 직접 구현 비교**:
  - week08 ReAct: while 루프 + if문으로 흐름 제어 → 유연하지만 흐름 파악이 코드를 직접 봐야 가능
  - week08 Plan-and-Execute: JSON 플랜 생성 후 실행 → 계획이 틀리면 전체 실패
  - week09 LangGraph: 그래프 선언 후 프레임워크가 실행 → `draw_mermaid()`로 즉시 시각화, 조건부 분기가 명시적
- **다음 주 준비**: week10 Self-Correction — 추천 결과를 LLM이 검토하고 품질이 낮으면 재검색하는 루프 추가
