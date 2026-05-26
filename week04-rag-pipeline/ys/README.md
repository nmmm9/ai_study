# 4주차: RAG 파이프라인 - ys

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| Retrieval | Hybrid Retriever | Vector Retriever / BM25 | 종목명, 공시명, 이슈 키워드와 문맥 의미가 모두 중요하므로 Hybrid Retriever를 선택 |
| Prompting | Context-aware Prompting | Basic Prompting | 뉴스·공시·리포트 문맥을 근거로 답변해야 하므로, 문맥 자료만 참고하도록 제한할 수 있는 Context-aware Prompting을 선택 |
| Citation | Document ID Citation | No Citation / URL-only Citation | 답변 문장과 근거 자료를 직접 연결하기 위해 [자료 1], [자료 2] 형식의 Document ID Citation을 선택 |
| Guardrails | Rule-based Guardrails | LLM-based Guardrails | 명확히 제한해야 할 표현이 정해져 있어서 Rule-based Guardrails를 선택 |
| Output Validation | Rule-based Validation | Manual Review / LLM-as-a-Judge | Citation 누락, 가짜 자료 번호, 필수 섹션 누락, 금지 표현은 규칙으로 검사할 수 있으므로 Rule-based Validation을 선택 |
| Answer Regeneration | Validation-based Regeneration | Direct Output | 출력 검증에서 문제가 발견된 경우 오류 내용을 반영해 다시 생성할 수 있도록 Validation-based Regeneration을 선택 |

## 핵심 구현
- 주요 로직 설명:
  - 사용자의 질문이 들어오면 먼저 Input Guardrail에서 위험 표현을 검사
  - Retriever는 질문 의도를 분석한 뒤, 메타데이터를 기준으로 관련 문서를 검색
  - 검색된 문서는 벡터 유사도뿐 아니라 키워드 일치도, 최신성, 출처 신뢰도를 함께 고려하여 재정렬
  - citation_service.py에서 검색 문서에 [자료 1], [자료 2] 형식의 번호를 부여하고, 해당 번호를 Prompt와 출처 목록에 함께 전달
  - prompt_service.py는 검색된 문맥 자료, 사용자 질문, Citation 규칙, 투자 안전 규칙을 합쳐 최종 RAG Prompt를 생성
  - llm_service.py의 Generator는 해당 Prompt를 기반으로 5섹션 형식의 답변을 생성
  - validation_service.py는 생성된 답변에서 Citation 누락, 존재하지 않는 자료 번호, 필수 섹션 누락, 매수·매도 단정 표현을 검사
  - 검증에 실패하면 오류 내용을 반영하여 답변을 다시 생성하고, 검증을 통과한 답변만 사용자에게 제공

- 코드 실행 방법:
  - 백엔드
     - cd backend
     - .\venv\Scripts\Activate.ps1
     - uvicorn main:app --reload --port 8000

  - 프론트엔드
     - cd ../frontend
     - npm run dev

  - 브라우저
     - http://localhost:5173

## WHY (의사결정 기록)
1. **Q**: 왜 이 방식을 선택했는가?
   **A**: Retriever 단계에서는 Hybrid Retriever 방식을 사용하면 벡터 유사도뿐 아니라 키워드 일치도, 최신성, 종목 메타데이터를 함께 고려한다. Prompt 단계에서는 검색된 문맥 자료만 근거로 답변하도록 제한하고, 주요 주장에는 [자료 번호] Citation을 붙이도록 설계해서 신뢰성을 높였다. 또한 Rule-based Guardrails와 Output Validation을 추가해 답변을 검증하도록 구성했다.  

2. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**: Cross-Encoder 기반 Re-ranker나 LLM-as-a-Judge 검증 방식을 사용할 것이다. Cross-Encoder Re-ranker를 사용하면 검색된 문서와 사용자 질문의 관련성을 더 정밀하게 판단할 수 있고, LLM-as-a-Judge를 사용하면 답변이 문맥 자료에 근거하고 있는지 더 유연하게 검증할 수 있다. 하지만 이 방식은 추가 모델 호출이 필요해 응답 시간이 길어지고 API 비용이 증가할 수 있다.
   
## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | 답변에 존재하지 않는 자료 번호가 표시됨 | INVALID_CITATION: [자료 5] does not exist | 검색된 자료는 3개뿐인데 LLM이 임의로 [자료 5]를 생성함 | citation_service.py에서 실제 검색 문서 수를 기준으로 유효한 자료 번호를 관리하고, validation_service.py에서 존재하지 않는 자료 번호를 검사하도록 구현 |
| 2 | 검증 실패한 답변이 그대로 사용자에게 출력될 가능성이 있음 | VALIDATION_FAILED | 스트리밍 구조에서는 답변이 생성되는 즉시 사용자에게 전달되므로 사후 검증이 어려움 | 내부적으로 답변 전체를 먼저 생성하고 검증한 뒤, 검증을 통과한 답변만 SSE 형식으로 전송하는 방식으로 변경 |

## 회고
- 이번 주 배운 점: RAG 파이프라인은 Retriever, Prompt, Generator가 결합되어 문맥 기반 답변을 생성하는 구조라는 것을 배웠고 Retriever, Prompt, Citation, Guardrails의 각 개념과 사용하는 이유, 작동 방식, 종류에 대해 알게됐다.
- 다음 주 준비할 것: Advanced RAG 개념 공부
