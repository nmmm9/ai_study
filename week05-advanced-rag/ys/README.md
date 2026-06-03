# 5주차: Advanced RAG - ys

## 기술 스택

| 항목              | 선택                        | 대안                                      | 선택 이유                                                                                                 |
| --------------- | ------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Retrieval       | Hybrid Search             | Vector Search only / BM25 only          | 주식 에이전트는 종목명, 종목코드, 재무 용어처럼 정확한 키워드와 뉴스·공시 문맥 의미가 모두 중요하므로 BM25와 Vector Search를 결합한 Hybrid Search를 선택 |
| Keyword Search  | BM25                      | 단순 키워드 매칭                               | PER, 유상증자, HBM, 005930 같은 정확한 용어를 더 잘 검색하기 위해 BM25를 선택                                                |
| Semantic Search | Vector Search             | BM25 only                               | 사용자가 전문 용어를 몰라도 자연어 질문으로 관련 문서를 찾을 수 있도록 Vector Search를 유지                            |
| Result Fusion   | RRF                       | 단순 병합 / 점수 합산                           | BM25 점수와 Vector 유사도 점수의 범위가 다르기 때문에 점수 합산 대신 순위 기반으로 안정적으로 결합할 수 있는 RRF를 선택                           |
| Reranking       | Rule-based Reranking      | Cross-Encoder Reranking / LLM Reranking | 주식 정보는 최신성, 출처 신뢰도, 종목 메타데이터 일치가 중요하므로 규칙 기반 재정렬을 선택                                                  |
| Evaluation      | Hit Rate@3, Recall@3, MRR | 단순 주관 평가                                | 검색 알고리즘 개선 전후의 품질 차이를 수치로 비교하기 위해 검색 평가 지표를 사용                                                        |

## 핵심 구현

* 주요 로직 설명:

  * 기존 Qdrant 기반 Vector Search는 개선 전 Baseline 검색 방식으로 유지
  * BM25 기반 키워드 검색 기능을 추가하여 종목명, 종목코드, 재무 용어, 공시 용어를 정확히 검색할 수 있도록 구성
  * 사용자 질문이 들어오면 Vector Search와 BM25 Search를 각각 실행
  * 두 검색 결과는 단순 점수 합산이 아니라 RRF 방식으로 병합
  * 병합된 검색 후보에서 중복 문서를 제거하고 최종 후보 문서 목록을 생성
  * 이후 Rule-based Reranking을 적용하여 키워드 일치도, 최신성, 출처 신뢰도, 종목명·종목코드 메타데이터 일치도, 문서 유형 일치도를 기준으로 재정렬
  * 검색 방식은 Vector Search only, Hybrid Search, Hybrid Search + Reranking 세 가지 모드로 비교 가능하게 구성
  * 평가용 질문과 정답 문서를 매핑한 evaluation dataset을 만들고, 각 방식의 검색 결과를 비교
  * 검색 품질은 Hit Rate@3, Recall@3, MRR 지표로 계산하여 개선 전후 결과를 표 형태로 확인

* 코드 실행 방법:

  * 백엔드

    * cd backend
    * .\venv\Scripts\Activate.ps1
    * uvicorn main:app --reload --port 8000

  * 프론트엔드

    * cd ../frontend
    * npm run dev

  * 검색 평가 실행

    * cd backend
    * .\venv\Scripts\Activate.ps1
    * python retrieval_eval.py

  * 브라우저

    * http://localhost:5173

## WHY (의사결정 기록)

1. **Q**: 왜 이 방식을 선택했는가?
   **A**: 기존 Vector Search는 질문의 의미와 비슷한 문서를 찾는 데 강하지만, 주식 에이전트에서는 종목코드, 재무지표, 공시명, 산업 키워드처럼 정확한 단어 검색도 중요하다. 그래서 BM25 기반 키워드 검색을 추가하고, 기존 Vector Search와 결합한 Hybrid Search 방식을 사용했다. 또한 BM25 점수와 Vector 유사도 점수는 기준이 다르기 때문에 단순히 더하지 않고 RRF 방식으로 순위 기반 병합을 적용했다. 이후 최신성, 출처 신뢰도, 종목 메타데이터 일치도를 반영한 Rule-based Reranking을 추가하여 최종 검색 문서의 품질을 높였다.

2. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**: Cross-Encoder 기반 Reranker를 사용하여 사용자 질문과 검색 문서의 관련성을 더 정밀하게 판단하도록 구현할 수 있다. 이 방식은 단순 규칙보다 문맥 이해력이 높아 검색 품질을 더 개선할 가능성이 있다. 하지만 후보 문서마다 모델 추론이 필요하기 때문에 응답 시간이 길어지고 추가 모델 실행 비용이 발생할 수 있다. 따라서 이번 구현에서는 프로젝트 구조에 맞게 Rule-based Reranking을 우선 적용하고, 추후 고도화 단계에서 Cross-Encoder Reranking을 적용하는 방향이 적합하다고 판단했다.

## 트러블슈팅 로그

| # | 문제 상황                                                | 에러 메시지                       | 원인 (Root Cause)                                     | 해결 방법                                                             |
| - | ---------------------------------------------------- | ---------------------------- | --------------------------------------------------- | ----------------------------------------------------------------- |
| 1 | BM25 점수와 Vector 유사도 점수를 직접 합산하면 특정 검색 방식 결과가 과하게 반영됨 | HYBRID_SCORE_SCALE_MISMATCH  | BM25 점수는 값의 범위가 크고 Vector 유사도는 보통 0~1 범위라 점수 기준이 다름 | 점수 직접 합산 대신 RRF 방식을 적용하여 각 검색 결과의 순위를 기준으로 병합                     |                         |
| 2 | 특정 종목 질문에서 다른 종목 문서가 함께 검색됨                          | STOCK_METADATA_MISMATCH      | 질문 키워드와 일부 문서 내용이 비슷해 종목이 다른 문서가 검색 결과에 포함됨         | stock_name, stock_code 메타데이터 일치 점수를 추가하여 질문 대상 종목과 일치하는 문서를 우선 정렬 |

## 회고

* 이번 주 배운 점: Advanced RAG에서는 Vector Search만 사용하는 것이 아니라 BM25 기반 키워드 검색과 Vector Search 기반 의미 검색을 결합하여 검색 품질을 높일 수 있다는 것을 배웠다. 그리고 RRF를 사용하면 서로 점수 기준이 다른 검색 결과를 안정적으로 병합할 수 있고, Reranking을 통해 최신성, 출처 신뢰도, 종목 메타데이터 일치도를 반영할 수 있다는 점을 알게 되었다.
* 다음 주 준비할 것: Function Calling 개념 공부 및 구현하기
