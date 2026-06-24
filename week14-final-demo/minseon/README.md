# 14주차: Final Demo — 청년정책 AI 챗봇

> week4~13에서 배운 핵심 기술을 모두 통합한 최종 버전

---

## week별 기여 기술

| 주차 | 기술 | 이번 버전 적용 |
|------|------|--------------|
| Week4 | RAG 파이프라인 | 620개 정책 MD → 키워드 검색 |
| Week5 | Advanced RAG | BM25 키워드 검색 + 카테고리 필터 |
| Week6 | 세션 관리 | 사이드바 멀티세션 (JSON 영속) |
| Week7 | Function Calling | 3가지 도구 (search/compare/list) |
| Week8 | ReAct Agent | 실행 추적 (Trace) UI 표시 |
| Week9 | LangGraph | StateGraph 기반 워크플로우 |
| Week10 | Self-Correction | 검색 실패 시 쿼리 재작성 (최대 2회) |
| Week11 | Multi-Agent | 8개 카테고리 전문 분류 |
| Week12 | Agentic RAG | LLM이 검색 여부 스스로 판단 |
| Week13 | RAGAS 평가 | 평가 결과 대시보드 탭 |

---

## 아키텍처

```
START → agent_node (3가지 도구 선택)
          │
          ├─ search_policy ──→ tool_dispatcher → grade_docs_node
          │                                           ├─ relevant → generate_node → END
          │                                           └─ not_relevant → rewrite_node → agent_node
          │
          ├─ compare_policies → tool_dispatcher → generate_node → END
          │
          ├─ list_by_category → tool_dispatcher → generate_node → END
          │
          └─ (직접 답변) ──────────────────────→ generate_node → END
```

## 3가지 도구 (week7 Function Calling)

| 도구 | 사용 시점 | 예시 질문 |
|------|---------|---------|
| `search_policy` | 특정 정책 조건·금액 검색 | "청년도약계좌 조건이 뭐야?" |
| `compare_policies` | 두 정책 비교 | "도약계좌랑 희망적금 뭐가 나아?" |
| `list_by_category` | 카테고리 목록 탐색 | "취업 관련 정책 어떤 게 있어?" |

## 실행

```bash
cd week14-final-demo/minseon
python -m pip install -r requirements.txt
python -X utf8 -m streamlit run app.py
```

`.env` 파일에 `OPENAI_API_KEY=sk-...` 필요

## WHY (의사결정 기록)

1. **Q**: 왜 search_policy만 grade → rewrite 루프를 거치나?
   **A**: compare와 list는 두 정책을 단순 검색·나열하는 작업이라 관련성 평가가 불필요하다. search_policy만 "정확한 정보"가 중요하므로 self-correction 루프를 적용했다.

2. **Q**: 왜 세션을 SQLite가 아닌 JSON으로 저장했나?
   **A**: week6에서 동일한 결정을 내렸다. 단일 사용자 로컬 환경에서는 JSON이 설치·설정 없이 충분하다.

3. **Q**: RAGAS 평가 탭을 앱에 넣은 이유?
   **A**: 챗봇 품질을 "느낌"이 아닌 "수치"로 보여주기 위해서다. Faithfulness/Answer Relevancy/Context Precision/Context Recall 4개 지표가 최종 데모에서 가장 설득력 있는 근거가 된다.

## 트러블슈팅 로그

| # | 문제 상황 | 원인 | 해결 방법 |
|---|---------|------|---------|
| 1 | 복지 카테고리 쏠림 (405/492개) | "지원" 키워드가 모든 문서에 포함 | 제목 우선 키워드 매칭으로 변경 |
| 2 | 챗봇이 답변 못 함 | 온통청년 API 필드명 오류로 문서 내용 전부 공백 | PLCY_EXPLN_CN 등 올바른 필드명으로 수정 후 재수집 |
| 3 | pip install 실패 | python 3.14 / pip 3.14 버전 불일치 | python -m pip 사용 |

## 회고

- 이번 주 배운 점: 단순 기능 추가보다 "왜 이 구조인가"를 설명할 수 있는 것이 더 중요하다
- 다음 단계: 벡터 검색(ChromaDB) 도입으로 의미 기반 검색 정확도 향상
