<div align="center">

# 너네 왜 22살 23살이냐?
pr
`LangChain` `LangGraph` `RAG` `Multi-Agent` `Evaluation`

[![Duration](https://img.shields.io/badge/Duration-14%20Weeks-blue)]()
[![Members](https://img.shields.io/badge/Members-4-green)]()
[![Review](https://img.shields.io/badge/Review-Every%20Tuesday%2022%3A00-orange)]()

</div>

<br>

<div align="center">
<table>
<tr>
<td align="center">

### 📌 이번 주차

# 1주차: LLM API 연동

- API 연동, .env 보안, Streaming 응답
- LLM 1:1 채팅 환경 구축 및 토큰 관리 전략
- **Claude Code, Cursor 등 AI 코딩 툴 사용법 숙지**

<br>

</td>
</tr>
</table>
</div>

<br>

---

## 커리큘럼0 - 언제든지 바뀔수있음 정해진거아님

### PART 1: RAG - 데이터 기반 답변 시스템 (1~6주)

> 목표: 외부 문서를 정확히 참조하고 환각을 최소화하는 검색 시스템 구축

| 주차 | 주제 | 핵심 내용 | 과제 |
|:---:|------|----------|------|
| 1 | LLM API 연동 | API 연동, .env 보안, Streaming 응답 | LLM 1:1 채팅 환경 구축 및 토큰 관리 전략 |
| 2 | Chunking | PDF/Markdown 로드 및 텍스트 분할 전략 | 도메인 데이터를 의미 단위로 분할 |
| 3 | Embedding & Vector DB | Embedding 모델 선정 및 Vector DB 구축 | 인덱싱 및 유사도 검색 구현 |
| 4 | RAG 파이프라인 | Retriever + Prompt + Generator 결합, Guardrails | 문맥 참고 답변 프롬프트 설계, Citation 표시, 출력 검증 |
| 5 | Advanced RAG | Hybrid Search(BM25+Vector), Reranking | 검색 알고리즘 개선 전/후 품질 수치 비교 |
| 6 | Streamlit UI (1차 시연) | Streamlit UI 및 세션 관리 | 웹 기반 RAG 서비스 시연 및 기술 결정 회고 |

### PART 2: AI Agent - 자율적 문제 해결 (7~14주)

> 목표: 스스로 판단하고, 도구를 활용하며, 협업하는 지능형 에이전트 설계

| 주차 | 주제 | 핵심 내용 | 과제 |
|:---:|------|----------|------|
| 7 | Function Calling | 외부 함수 호출 인터페이스 설계 | 질문 의도에 따른 함수 호출 및 JSON 스키마 정의 |
| 8 | ReAct / Plan-and-Execute | ReAct, Plan-and-Execute 프레임워크 | 단계적 사고로 다단계 태스크 해결 에이전트 구축 |
| 9 | LangGraph 입문 | 그래프 기반 워크플로우 (Nodes, Edges) | 에이전트 실행 순서도 설계 및 Graph Visualizing |
| 10 | Self-Correction | 결과 검토 및 수정 로직 (Reflection) | 틀린 결과 시 재검색/수정하는 루프 구현 |
| 11 | Multi-Agent | 역할 분담 및 에이전트 간 통신 (Hand-off) | 2개 이상 에이전트 협업으로 복합 목표 달성 |
| 12 | Agentic RAG | RAG를 에이전트 도구로 통합 | 정보 부족 시 스스로 검색 도구를 호출하는 지능형 RAG |
| 13 | 평가 (Evaluation) | RAGAS, LangSmith 활용 정량 평가 | 성공률 지표 산출 및 실패 사례 분석 리포트 |
| 14 | 최종 데모 | 전체 시스템 통합 시연 | 기술적 결정, 프롬프트 전략, 삽질 로그 총정리 발표 |

### PART 3: 오픈소스 모델 전환 및 비교 (14주 이후)

> 목표: API 기반으로 완성한 시스템을 오픈소스 모델로 교체하고, Fine-tuning 후 성능 비교

| 단계 | 내용 | 상세 |
|:---:|------|------|
| 1 | 오픈소스 모델 적용 | LLaMA, Mistral 등을 기존 RAG + Agent 파이프라인에 교체 적용 |
| 2 | Fine-tuning | QLoRA 등을 활용해 도메인 데이터로 모델 파인튜닝 |
| 3 | 성능 비교 | API 모델 vs 오픈소스 모델 vs Fine-tuned 모델 정량 비교 |
| 4 | 비교 리포트 | 13주차 평가 체계(RAGAS, LangSmith)를 재활용한 최종 리포트 |

> 일정 및 세부 계획은 14주차 완료 후 확정

---

## 운영 규칙

### 1. AI 코딩 툴 활용

- **적극 권장**: Cursor, GitHub Copilot, ChatGPT 등 모든 AI 툴 사용 가능
- **금지**: 복사 & 붙여넣기 후 원리를 이해하지 못한 채 넘어가는 행위
- **책임**: AI가 작성한 코드의 모든 버그와 논리적 오류는 본인이 디버깅하고 설명할 수 있어야 함 >> 이 과정에서도 AI 활용해서 학습하면 좋음

### 2. "WHY" 중심의 코드 리뷰

> 매주 화요일 밤 10시 | 세미나 형식 (실시간 코딩 X)

모임 시 아래 질문에 답변을 준비해 옵니다:

- **의사결정 이유**: "AI가 제안한 방법 중 왜 이 방식을 선택했나요?"
- **기술 비교**: "다른 대안은 무엇이 있고, 왜 이걸 썼나요?"

### 3. 트러블슈팅 로그 필수

구현 과정에서 겪은 어려움을 반드시 기록합니다:

- **AI의 한계**: AI에게 물어봐도 해결되지 않았던 지점
- **문제 해결**: 문제가 발생하고, 왜 발생했으며, 해결한 과정
- **에러 분석**: 주요 에러 메시지와 근본 원인(Root Cause)

### 4. 과제 제출

- **마감**: 매주 월요일 자정까지 개인 GitHub 저장소에 Push
- **README 필수 작성**: 아래 템플릿 참고

### 5. 도메인 자율성

각자 관심 있는 데이터(주식, 법률, 뉴스, 전공 등)를 정해 14주간 해당 도메인을 깊게 파는 것을 권장합니다.

---

## 주차별 과제 README 템플릿

```markdown
# N주차: [주제명]

## 개요
- 이번 주 목표:
- 사용한 도메인 데이터:

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| 예) Vector DB | Chroma | FAISS, Pinecone | 로컬 환경에서 설치가 간편하고... |

## 핵심 구현
- 주요 로직 설명:
- 코드 실행 방법:

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
```

---

## 폴더 구조

```
├── README.md
├── .gitignore
├── week01-llm-api/
│   ├── juwon/
│   ├── yewon/
│   ├── minseon/
│   └── mg/
├── week02-chunking/
│   └── (동일)
├── ...
└── week14-final-demo/
    └── (동일)
```

각 멤버 폴더 안에 개인 README.md 템플릿이 포함되어 있습니다.

---

## Git 브랜치 운영 방식

### 브랜치
각자 본인 이름으로 브랜치 하나 생성 후 계속 사용
```
juwon, yewon, minseon, mg
```

### 작업 흐름
```
1. 브랜치 생성 (최초 1회)   →  git checkout -b juwon
2. 자기 폴더에서 작업       →  weekNN-xxx/juwon/ 안에서 코드 작성
3. 커밋 & 푸시             →  git push origin juwon
4. PR 생성                →  GitHub에서 main으로 Pull Request
5. 리뷰 후 머지            →  승인 후 main에 merge
6. 다음 주차 작업 전        →  git pull origin main으로 최신 반영
```

### 규칙
- 자기 이름 폴더에서만 작업 (다른 사람 폴더 수정 X)
- PR 제목: `[weekNN] 이름 - 한줄 요약` (예: `[week01] juwon - OpenAI Streaming 채팅 구현`)
- 월요일 자정까지 PR 생성, 화요일 리뷰 후 머지
