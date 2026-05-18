# 3주차: Embedding & Vector DB - ys

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| Embedding 모델 | OpenAI text-embedding-3-small | text-embedding-3-large, 로컬 SentenceTransformer 모델 | 문서를 벡터로 변환하기 위해 사용하였다. text-embedding-3-small은 1536차원 벡터를 생성하며, 비용 부담이 비교적 낮고 의미 기반 검색에 적합하여 임베딩 모델로 선정했다. |
| Vector DB | Qdrant | Chroma, FAISS, Pinecone | 임베딩된 문서 벡터를 저장하고 사용자 질문과 유사한 문서를 검색하기 위해 사용했고 Qdrant는 로컬 파일 모드로 사용할 수 있어 Docker 없이 구축 가능하며, 메타데이터 필터링을 지원하여 필요한 문서 검색에 적합하다. |
| 인덱싱 방식 | 문서 Chunk 단위 벡터 인덱싱 | 전체 문서 단위 인덱싱, 키워드 검색 | PDF, Markdown, TXT 문서를 의미 단위로 나눈 뒤 각 chunk를 임베딩하여 Vector DB에 저장하였다. 전체 문서를 하나의 벡터로 저장하면 여러 주제가 섞여 검색 정확도가 떨어질 수 있으므로, chunk 단위로 인덱싱하여 질문과 관련된 부분만 검색되도록 구현하였다. |
| 유사도 검색 | Qdrant Vector Search + Score Threshold | 단순 키워드 검색, 전체 벡터 비교 | 사용자 질문을 임베딩 후 Qdrant에 저장된 문서 벡터와 비교하여 의미적으로 가까운 자료와 유사도 50% 이상인 자료만 LLM에 전달하도록 설정하여 관련성이 낮은 문서가 답변에 포함되는 것을 줄이기 위해 선정했다. |

## 핵심 구현
- 주요 로직 설명:
  - auto_collect_service.py는 사용자의 질문과 종목 정보를 기준으로 뉴스·공시 수집이 필요한지 판단하고, Naver News API와 OpenDART API 수집 과정을 통합 관리한다.
  - embedding_service.py는 수집된 뉴스·공시 텍스트를 OpenAI text-embedding-3-small 모델에 전달하여 1536차원 벡터로 변환한다.
  - vector_service.py는 생성된 벡터와 원문 텍스트, 종목명, 종목코드, 섹터, 문서유형, 출처, 날짜 등의 메타데이터를 Qdrant에 저장하고 검색한다.
  - retrieval_service.py는 사용자 질문을 검색에 적합한 형태로 확장하고, 질문 벡터와 Qdrant에 저장된 문서 벡터를 비교해 유사도 기준을 만족하는 자료만 가져온다.
    
- 코드 실행 방법:
  - 사전 설치 항목을 준비
     - Python 3.10 이상
     - Node.js 18 이상
     - OpenAI API Key
     - Naver Developers API Key
     - OpenDART API Key
  - 백엔드
     - cd backend
     - python -m venv venv
     - .\venv\Scripts\Activate.ps1
     - pip install -r requirements.txt
     - .env` 파일에 API Key를 입력
     - uvicorn main:app --reload --port 8000
  - 프론트엔드
     - cd ../frontend
     - npm install
     - .env.local 파일에 VITE_API_URL=http://localhost:8000 입력
     npm run dev
  - 브라우저
     - http://localhost:5173
     - 화면에서 종목명, 종목코드, 질문을 입력

## WHY (의사결정 기록)
1. **Q**: 왜 이 방식을 선택했는가?  
   **A**: 사용자의 질문과 관련 있는 데이터를 단순 키워드가 아니라 의미 기준으로 찾아야 하기 때문에 Embedding과 Vector DB 방식을 선택하여 수집된 자료는 OpenAI text-embedding-3-small 모델로 벡터화하고, Qdrant Vector DB에 저장하여 질문과 의미적으로 가까운 자료를 유사도 검색으로 찾도록 구현하였다. 또한 메타데이터를 함께 저장하여 자료 유형에 맞는 검색이 가능하도록 하였다.
2. **Q**: 다르게 구현한다면 어떻게 했을까?  
   **A**: 의미 검색 + 키워드 검색을 결합한 Hybrid Search 구조를 할 것이다. Qdrant의 벡터 유사도 검색에 더해 BM25 같은 키워드 검색을 함께 적용하여 두 검색 결과를 재정렬하는 방식을 할 것이다. 이렇게 하면 의미적으로 관련 있는 자료를 찾으면서도, 키워드가 포함된 문서를 더 정확하게 검색할 수 있다.
   
## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | Qdrant에 벡터 저장 실패 | Vector dimension error | Qdrant Collection의 벡터 차원과`text-embedding-3-small이 생성한 1536차원 벡터 크기가 일치하지 않음 | Qdrant Collection 생성 시 vector size를 1536으로 설정 |
| 2 | 질문과 관련 없는 문서가 검색됨 | 에러 메시지 없음 | 벡터 유사도만 사용하고 종목명, 종목코드, 문서유형 필터를 적용하지 않아 관련 없는 자료가 함께 검색됨 | Qdrant 검색 시 메타데이터 필터를 함께 적용하여 종목명, 종목코드, 섹터, 문서유형 기준으로 검색 범위를 제한 |
| 3 | 검색 결과가 너무 많이 LLM에 전달됨 | 토큰 초과 또는 응답 지연 | 검색된 문서를 모두 LLM context에 넣어 토큰 사용량이 증가함 | SEARCH_TOP_K, SEARCH_SCORE_THRESHOLD, MAX_CONTEXT_TOKENS 값을 설정하여 유사도 기준을 통과한 문서만 제한적으로 전달 |
| 4 | 같은 뉴스나 공시가 반복 저장됨 | 에러 메시지 없음 | 자동 수집 시 이미 저장된 뉴스·공시를 다시 임베딩하여 Vector DB에 중복 저장함 | 뉴스는 URL 기준, 공시는 DART 접수번호 기준으로 중복 여부를 확인한 뒤 저장하도록 수정 |

## 회고
- 이번 주 배운 점: Embedding, Vector DB의 개념과 종류(API 기반 모델, 로컬 실행 모델), Embedding 모델의 벡터화 작동 과정 그리고 유사도 검색과 빠른 검색에 장단점에 대해서도 배웠다.
- 다음 주 준비할 것: RAG 파이프라인 개념 공부
