# 4주차: RAG 파이프라인 - juwon

## 기술 스택

| 항목        | 선택               | 대안                  | 선택 이유                                        |
| --------- | ---------------- | ------------------- | -------------------------------------------- |
| LLM       | OpenAI GPT       | Claude, Llama       | API 사용이 간단하고 응답 품질이 안정적이라 선택                 |
| Embedding | OpenAI Embedding | SentenceTransformer | LLM과 동일한 API에서 쉽게 사용할 수 있어서 선택               |
| Vector DB | ChromaDB         | FAISS, Pinecone     | 로컬 환경에서 쉽게 구축 가능하고 파일 형태로 저장되는 실제 벡터 DB이기 때문 |
| Retrieval | Chroma Retriever | BM25                | 임베딩 기반 유사도 검색이 RAG 구조에 적합                    |
| Re-ranker | Cross-Encoder    | Bi-Encoder          | 검색된 결과를 재정렬하여 더 정확한 문서를 선택하기 위해 사용           |
| UI        | Streamlit        | Gradio, FastAPI     | 간단한 코드로 웹 UI를 만들 수 있어서 선택                    |

---

# 핵심 구현

## 주요 로직 설명

이번 주차에서는 기존에 구현한 **Chunking, Embedding, Vector DB** 구조를 기반으로 전체 **RAG 파이프라인**을 구성하였다.

전체 흐름은 다음과 같다.

```
사용자 질문
 ↓
Guardrail (취업 관련 질문인지 확인)
 ↓
Retriever (ChromaDB에서 top-10 문서 검색)
 ↓
Re-ranker (Cross-Encoder로 top-3 재정렬)
 ↓
Prompt 구성 (출처 포함)
 ↓
LLM Generator
 ↓
Output Validation
 ↓
최종 답변 출력
```

### 1. Retriever

사용자의 질문과 유사한 문서를 찾기 위해 ChromaDB를 사용하였다.
ChromaDB에는 취업 공고 데이터를 Chunk 단위로 저장하였으며, 현재 총 **129개의 청크**가 저장되어 있다.

검색 과정

```
Query → Embedding → Vector Similarity Search
```

이를 통해 질문과 가장 유사한 문서를 **top-10**까지 가져온다.

---

### 2. Re-ranker

Retriever 단계에서 가져온 문서가 항상 정확한 것은 아니기 때문에
**Cross-Encoder 기반 Re-ranker**를 추가하여 결과를 재정렬하였다.

동작 방식

```
top-10 문서
 ↓
Cross-Encoder score 계산
 ↓
score 기준 재정렬
 ↓
top-3 문서 선택
```

이 과정을 통해 실제 질문과 더 관련성이 높은 문서를 선택할 수 있다.

---

### 3. Prompt 설계

LLM이 정확한 답변을 생성할 수 있도록 **역할(Role)과 출력 형식**을 명확하게 지정하였다.

Prompt 주요 구성

* 역할: 취업 공고 정보를 기반으로 답변하는 AI
* 검색된 문서만 기반으로 답변
* 반드시 출처(Citation) 포함

Citation 형식

```
[출처: 회사명 - 섹션명]
```

예시

```
카카오의 자격 요건은 다음과 같습니다.

- Java 또는 Kotlin 개발 경험
- Spring Framework 사용 경험

[출처: 카카오 - 자격 요건]
```

---

### 4. Guardrail

취업과 관련 없는 질문이 들어오는 경우를 차단하기 위해 Guardrail을 추가하였다.

예시

입력 질문

```
오늘 날씨 어때?
```

출력

```
이 시스템은 취업 공고 관련 질문만 답변할 수 있습니다.
```

이를 통해 시스템의 **도메인 범위를 제한**하였다.

---

### 5. Output Validation

LLM이 잘못된 정보를 생성하는 것을 방지하기 위해
최종 출력 결과에 대해 간단한 검증 로직을 추가하였다.

검증 내용

* Citation 포함 여부 확인
* 빈 응답 여부 확인
* 검색 결과 없는 경우 안내 메시지 출력

---

### 6. Streamlit UI

사용자가 쉽게 질문할 수 있도록 **Streamlit 기반 웹 인터페이스**를 구현하였다.

구성

* 채팅 형태 인터페이스
* 스트리밍 응답 (타이핑 효과)
* 사이드바 기능

  * 토큰 사용량 표시
  * 대화 초기화 버튼

실행 시 웹 브라우저에서 **챗봇 형태로 RAG 시스템을 사용할 수 있다.**

---

## 코드 실행 방법

1️⃣ 가상환경 실행

```
conda activate rag
```

또는

```
venv\Scripts\activate
```

---

2️⃣ Streamlit 실행

```
streamlit run app.py
```

---

3️⃣ 브라우저 접속

```
http://localhost:8501
```

---

## WHY (의사결정 기록)

### 1. Q: 왜 이 방식을 선택했는가?

RAG 시스템을 구성할 때 **검색 정확도와 답변 신뢰도**를 높이는 것이 중요하다고 생각하였다.

그래서 단순히 Retriever만 사용하는 것이 아니라 다음과 같은 구조를 선택하였다.

```
Retriever → Re-ranker → LLM
```

Retriever는 빠르게 문서를 찾는 역할을 하고,
Re-ranker는 검색된 문서를 다시 평가하여 더 관련성이 높은 문서를 선택한다.

또한 LLM이 임의로 정보를 생성하는 것을 방지하기 위해 **Citation 기반 Prompt**를 사용하였다.

---

### 2. Q: 다르게 구현한다면 어떻게 했을까?

다른 방법으로는 다음과 같은 구조도 가능하다.

1. Vector DB를 **ChromaDB 대신 FAISS**로 구현
2. Re-ranker 대신 **MMR(Maximal Marginal Relevance)** 기반 검색
3. Streamlit 대신 **FastAPI + React** 구조로 웹 인터페이스 구현

또는 실제 서비스 환경이라면
로컬 Vector DB 대신 **Pinecone 같은 클라우드 Vector DB**를 사용하는 방법도 고려할 수 있다.

---

# 트러블슈팅 로그

| # | 문제 상황                | 에러 메시지               | 원인 (Root Cause)             | 해결 방법                          |
| - | -------------------- | -------------------- | --------------------------- | ------------------------------ |
| 1 | FAISS 제거 후 IDE 경고 발생 | unresolved reference | FAISS 관련 코드 잔재 존재           | EmbeddingStore, numpy 관련 코드 제거 |
| 2 | 터미널 실행 시 프로그램 종료     | exit code 1          | 파이프 입력 방식 문제                | Streamlit 환경에서 실행              |
| 3 | 검색 결과 부족             | 관련 공고 검색 안됨          | chunk_size가 너무 큼            | chunk_size 400 → 200으로 변경      |
| 4 | chroma_db 폴더 삭제 불가   | file in use          | Python 프로세스가 sqlite 파일 사용 중 | delete_collection()으로 자동 재구축   |
| 5 | 회사 검색 시 다른 회사 결과 출력  | 검색 정확도 낮음            | 청크에 회사명이 포함되지 않음            | 청크 앞에 "회사명 - 섹션명" 접두어 추가       |

---

# 회고

### 이번 주 배운 점

* RAG 시스템은 단순히 Vector DB를 사용하는 것만으로 완성되는 것이 아니라
  **Retriever, Re-ranker, Prompt, Guardrail** 등 여러 요소가 함께 동작해야 한다는 것을 알게 되었다.
* Chunking 방식이 검색 성능에 큰 영향을 미친다는 것도 확인하였다.
* Streamlit을 이용하면 비교적 간단한 코드로 RAG 시스템을 웹 인터페이스 형태로 구현할 수 있었다.

---

### 다음 주 준비할 것

* Vector DB 검색 성능 개선
* Re-ranker 성능 비교 실험
* Prompt 최적화
* 더 다양한 취업 공고 데이터 추가

---


