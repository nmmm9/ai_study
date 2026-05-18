# Week 12 — Agentic RAG

> RAG를 에이전트 도구로 통합 — 정보 부족 시 스스로 검색 도구를 호출하는 지능형 RAG

## week11과의 차이점

| 구분 | week11 Multi-Agent | week12 Agentic RAG |
|------|--------------------|--------------------|
| RAG 방식 | 고정 파이프라인 (항상 검색) | 에이전트가 검색 필요 여부 스스로 판단 |
| 검색 실패 시 | 그대로 답변 생성 | 쿼리 재작성 후 최대 2회 재검색 |
| 라우팅 | Intent Router (사람이 설계) | LLM이 tool call 여부로 스스로 결정 |
| 핵심 기술 | LangGraph Multi-Agent | OpenAI Tool Calling + Self-Correction |

## 그래프 흐름

```
START → agent_node
          │
          ├─[tool call]→ search_tool_node → grade_docs_node
          │                                      │
          │                              ┌── relevant ──→ generate_node → END
          │                              └── not_relevant
          │                                      │
          │                              retry < 2 → rewrite_node → agent_node
          │                              retry >= 2 → generate_node → END
          │
          └─[직접 답변]→ generate_node → END
```

## 핵심 노드

| 노드 | 역할 |
|------|------|
| `agent_node` | LLM이 search_policy 도구 호출 여부 결정 |
| `search_tool_node` | tool call 실행 → 정책 문서 검색 |
| `grade_docs_node` | 검색 결과 관련성 평가 (relevant / not_relevant) |
| `rewrite_node` | 쿼리 재작성으로 검색 전략 개선 |
| `generate_node` | 검색 문서 기반 최종 답변 생성 |

## 실행

```bash
cd week12-agentic-rag/minseon
python -X utf8 -m streamlit run app.py
```

`.env` 파일에 `OPENAI_API_KEY=sk-...` 필요

기본 정책 탐색 (explore)

나 24살 서울 사는데 받을 수 있는 청년 정책 다 알려줘
경기도 22살 취업 준비 중인데 지원받을 수 있는 거 뭐 있어?
대학생이 받을 수 있는 장학금 종류 추천해줘
팩트 질문 (qa · Agentic RAG 검색 테스트)

청년도약계좌 가입 조건이 어떻게 돼?
청년내일채움공제 얼마 받을 수 있어?
국민취업지원제도 1유형이랑 2유형 차이가 뭐야?
중복 수혜 검증 (교차 검증 테스트)

청년도약계좌랑 청년희망적금 같이 가입할 수 있어?
국가장학금이랑 근로장학금 동시에 받을 수 있어?
재검색 유도 (쿼리 재작성 테스트)

전세 사기 당한 청년한테 주는 지원금 있어?
취업 안 된 졸업생한테 매달 돈 주는 정책 있어?
