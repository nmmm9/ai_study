# 13주차: 평가 (Evaluation) - juwon

> **목표**: Simple RAG vs Advanced RAG vs Agentic RAG 를 동일 질문셋으로 A/B 비교하고, RAGAS 메트릭으로 정량 평가 + 실패 케이스 분석 HTML 보고서 생성

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| 평가 프레임워크 | RAGAS | MTEB, 수동 평가 | RAG 특화 메트릭(Faithfulness/Relevancy/Precision/Recall) |
| LLM 트레이싱 | LangSmith | Langfuse, W&B | LangChain 공식 통합, env var 설정만으로 자동 트레이싱 |
| 벡터 DB | Supabase pgvector | Pinecone, ChromaDB | 12주차와 동일 DB 공유 → 공정한 비교 |
| 보고서 | Chart.js + HTML | Plotly, Streamlit | 별도 서버 없이 단일 HTML 파일로 공유 가능 |

## 파일 구조
```
week13-evaluation/juwon/
├── dataset.json          # 20개 테스트 질문 + ground_truth
├── evaluate.py           # 메인 실행: 3개 시스템 × 20문항 평가
├── report.py             # HTML 보고서 생성기
├── requirements.txt
├── .env.example
└── systems/
    ├── base.py           # 공통 유틸 (embed, vector_search, llm_answer)
    ├── simple_rag.py     # System A: 단순 검색 1회
    ├── advanced_rag.py   # System B: Multi-Query + RRF + 리랭킹
    └── agentic_rag.py    # System C: LangGraph ReAct 에이전트
```

## 핵심 구현

### System A — Simple RAG
```
질문 → 벡터 검색(limit=3) → LLM 답변
```

### System B — Advanced RAG
```
질문 → Multi-Query 확장(2개) → 각 쿼리 검색 → RRF 합산 → 리랭킹(top_k=3) → LLM 답변
```

### System C — Agentic RAG
```
질문 → ReAct 에이전트 → [search_trend_history / get_recent_trends] 자율 호출 → 답변
```

### RAGAS 평가 메트릭
| 메트릭 | 의미 |
|--------|------|
| Faithfulness | 답변이 컨텍스트에 근거하는 정도 |
| Answer Relevancy | 답변이 질문과 관련 있는 정도 |
| Context Precision | 검색된 컨텍스트의 정확도 |
| Context Recall | ground_truth 대비 컨텍스트 포함률 |

### 코드 실행 방법
```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일에 OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY 입력

# 3. 평가 실행 (약 5~10분 소요)
python evaluate.py

# 결과: results/results_<timestamp>.json
#       results/report_<timestamp>.html  ← 브라우저에서 열기
```

## WHY (의사결정 기록)
1. **Q**: 왜 A/B/C 3개 시스템을 비교했는가?
   **A**: 12주차까지 점진적으로 발전시켜온 RAG 파이프라인의 실제 성능 차이를 수치로 검증하고, 복잡도 증가 대비 품질 향상 정도를 확인하기 위해

2. **Q**: RAGAS 외 다른 방법을 쓰지 않은 이유는?
   **A**: RAG 시스템 특화 메트릭을 한 번에 제공하고, `datasets.Dataset` 포맷으로 배치 평가가 간편해서 선택. 수동 평가는 주관성이 높고 시간이 많이 걸림

3. **Q**: 왜 동일한 Supabase DB를 3개 시스템이 공유하는가?
   **A**: 검색 대상 데이터가 다르면 시스템 간 비교가 불공정해짐. 같은 DB를 사용해야 검색 전략의 차이만 측정 가능

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | RAGAS 평가 시 JSON 파싱 오류 | `json.JSONDecodeError` | LLM이 RAGAS 내부적으로 JSON을 반환해야 하는데 형식 불일치 | RAGAS >= 0.1.14 버전 사용, `gpt-4o-mini` 모델로 평가 |
| 2 | Agentic RAG 응답 없음 | `messages[-1].content` 빈 문자열 | ReAct 에이전트가 도구 호출만 하고 최종 답변을 생성하지 않음 | `_SYSTEM` 프롬프트에 "반드시 최종 한국어 답변 작성" 명시 |

## 회고
- **이번 주 배운 점**: RAGAS 메트릭이 단순히 답변 품질뿐 아니라 검색 전략의 효과를 수치화해주어 RAG 파이프라인 개선 방향을 구체적으로 잡을 수 있음. Advanced RAG의 Multi-Query + RRF가 Context Recall을 실질적으로 높여주는지 실험으로 확인 가능
- **다음 주 준비할 것**: 평가 결과를 바탕으로 약한 메트릭 집중 개선, Cross-Encoder 리랭킹 추가 검토
