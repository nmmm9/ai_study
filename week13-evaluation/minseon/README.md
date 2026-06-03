# Week 13 — 평가 (Evaluation)

> RAGAS + LangSmith로 week12 Agentic RAG의 품질을 정량 측정

## 개요

- **이번 주 목표**: 완성된 Agentic RAG 파이프라인의 성능을 수치로 평가
- **도메인 데이터**: week12와 동일한 청년정책 492개
- **평가 기준**: 10개 수동 제작 QA 쌍 (카테고리별 조건·금액·비교·중복수혜 포함)

## 기술 스택

| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| 평가 프레임워크 | RAGAS | TruLens, ARES | RAG 특화 4개 지표 제공, HuggingFace Dataset 연동 간편 |
| 트레이싱 | LangSmith | MLflow, W&B | RAGAS 내부 LLM 호출 자동 캡처, 별도 코드 불필요 |
| 시각화 | Streamlit + Plotly | Gradio, Dash | week12와 동일 스택, 레이더 차트 |

## RAGAS 4개 지표

| 지표 | 의미 | 필요 입력 |
|------|------|----------|
| **Faithfulness** (충실성) | 답변이 검색 문서에 근거하는 정도 | answer + contexts |
| **Answer Relevancy** (답변 관련성) | 답변이 질문에 얼마나 관련있는가 | answer + question |
| **Context Precision** (컨텍스트 정밀도) | 검색된 문서 중 실제 관련 문서 비율 | contexts + ground_truth |
| **Context Recall** (컨텍스트 재현율) | 정답에 필요한 정보를 검색했는가 | contexts + ground_truth |

## 핵심 구현

```
week13-evaluation/minseon/
├── dataset.py      # 10개 테스트 QA 쌍 (카테고리별)
├── evaluator.py    # RAG 실행 → 수집 → RAGAS 평가 → JSON 저장
├── app.py          # Streamlit 대시보드 (실행 + 결과 시각화)
├── requirements.txt
└── results/        # 평가 결과 JSON (자동 생성)
```

코드 실행 방법:

```bash
cd week13-evaluation/minseon
pip install -r requirements.txt
python -X utf8 -m streamlit run app.py
```

`.env` 파일 설정:

```
OPENAI_API_KEY=sk-...

# LangSmith (선택)
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=week13-evaluation
```

CLI로 직접 평가만 실행:

```bash
python -X utf8 evaluator.py
```

## WHY (의사결정 기록)

1. **Q**: 왜 RAGAS를 선택했나?
   **A**: RAG 평가에 특화된 4개 지표를 한 번에 계산할 수 있고, `ground_truth`만 준비하면 LLM 기반으로 자동 채점해준다. TruLens는 설치가 복잡하고, 직접 구현하면 신뢰성 있는 LLM judge 설계가 어렵다.

2. **Q**: LangSmith를 별도 코드 없이 연동한 이유?
   **A**: RAGAS가 내부적으로 LangChain을 사용하기 때문에 `LANGCHAIN_TRACING_V2=true`만 설정하면 RAGAS의 LLM 평가 호출이 자동으로 LangSmith에 기록된다. 불필요한 래퍼 코드 없이 트레이싱을 얻을 수 있다.

3. **Q**: Ground Truth를 수동으로 만든 이유?
   **A**: 자동 생성(LLM으로 QA 생성)은 평가 bias 문제가 있다. 실제 정책 문서에서 직접 작성해야 `context_recall`이 의미있게 측정된다.

## 트러블슈팅 로그

| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | RAGAS 0.1.x / 0.2.x API 불일치 | ImportError | 버전에 따라 import 경로 변경 | try/except로 두 버전 모두 지원 |
| 2 | week12 경로 import 오류 | ModuleNotFoundError | 상위 폴더 패키지 미인식 | `sys.path.insert(0, week12_path)` |

## 회고

- 이번 주 배운 점: 같은 질문도 검색 카테고리 지정 여부에 따라 context_precision 점수가 크게 달라짐. week12의 카테고리 개선이 평가 지표에 직접 영향을 미침을 확인.
- 다음 주 준비할 것: week14 최종 데모 — 전체 파이프라인 통합 + 평가 지표 기반 개선 포인트 발표
