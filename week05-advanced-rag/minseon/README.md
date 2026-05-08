# 5주차: Advanced RAG - minseon

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
|RAG| Advanced RAG| Naive RAG|검색 전, 중, 후 정교한 필터링 작업으로 답변의 품질을 높임|

## 핵심 구현
- 주요 로직 설명:
- 코드 실행 방법:

# 
cd c:\Users\user\ai_study\week05-advanced-rag\minseon\fastapi-react\backend
uvicorn server:app --reload



## WHY (의사결정 기록)
1. **Q**: 왜 이 방식을 선택했는가?
   **A**:
2. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**:

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | | | | |

## 회고
- 이번 주 배운 점:
- 다음 주 준비할 것:




Advanced RAG

① 검색 전 단계 (Pre-retrieval Optimization)
사용자의 질문이 모호하거나 데이터베이스와 매칭하기 어려울 때 이를 정제하는 과정입니다.

Query Rewriting: 사용자의 질문을 검색하기 더 좋은 문장으로 재작성합니다.

Query Expansion: 질문과 관련된 유의어나 개념을 추가하여 검색 범위를 넓힙니다.

Multi-query Generation: 하나의 질문을 여러 관점의 질문으로 쪼개어 검색 효율을 높입니다.

② 검색 단계 (Retrieval Optimization)
단순한 의미론적 유사도(Semantic Similarity) 검색의 한계를 보완합니다.

Hybrid Search: 키워드 기반의 BM25 방식과 의미 기반의 Vector Search를 결합하여 문맥과 핵심 키워드를 모두 잡습니다.

Small-to-Big Retrieval: 실제 검색은 작은 단위(Sentence)로 수행하고, LLM에게 전달할 때는 앞뒤 문맥을 포함한 큰 단위(Chunk)를 제공합니다.

③ 검색 후 단계 (Post-retrieval Optimization)
검색된 결과 중 노이즈를 제거하고 순서를 조정합니다.

Reranking: 검색 엔진이 가져온 상위 결과들을 다시 한 번 정교한 모델을 통해 관련성 순으로 재정렬합니다. (가장 중요한 단계 중 하나입니다.)

Context Compression: 불필요한 내용을 쳐내고 답변에 꼭 필요한 정보만 압축해서 LLM에 전달합니다.


Few-Shot (예시학습법)
