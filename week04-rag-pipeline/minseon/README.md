# 4주차: RAG 파이프라인 - minseon

*RAG란? Retrieval-Augmented Generation — LLM이 모르는 지식을 "검색해서 주입"하는 기법

RAG 파이프라인	: LLM API(답변생성) 청킹(적절히 자르기) 임베딩 + Vector DB(검색진구축) 연결


## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
|문서파싱  |pymuPDF| pythin-docx, pdfplumber|  PDF·md·txt 통합 지원, 속도 빠름, 설치 간단 |
|청킹| labgChiain, RecursiveChaterTextSplitter | 고정길이분할, 문장 단위 분할 | 문장 -> 문장-> 단어 순서로 의미 단위를 최대한 보존하며 분할 | 
| 임베딩 | OpenAI text-embedding-3-small| text-embedding-ada-002, HuggingFace | ada-002 대비 성능 향상 + 비용 절감, API 키 하나로 LLM과 통합 관리| 
| 벡터 DB | ChromaDB | FAISS, Pinecone, Weaviat | 로컬 영구 저장(PersistentClient), 코사인 유사도 내장, 별도 서버 불필요 |
| LLM |  OpenAI gpt-4o-mini | gpt-4o, Claude, Gemini | 임베딩과 동일 API 키 사용, 빠른 응답속도, 저렴한 비용 | 
| 벡엔드 | FastAPI + Uvicorn | flask ,django | 비동기 SSE 스트리밍 지원, 자동 API 문서 셍성, 타임 검증| 
| 환경변수| python-dotenv | 시스템 환경변수 직접 설정 | .env 파일로 API 키를 코드와 분리 관리, git 실수 방지 | 
| 프론트엔드 | React 18 (CDN, Babel Standalone) | Create React App, Next.js, Vite | npm 설치·빌드 없이 HTML 파일 하나로 React 컴포넌트 사용 가능, 빠른 프로토타이핑| 

## 핵심 구현
- 주요 로직 설명:
- 코드 실행 방법:
1. venv312 활성화
c:\Users\user\ai_study\.venv312\Scripts\Activate.ps1

2. 서버 실행
cd c:\Users\user\ai_study\week04-rag-pipeline\minseon\fastapi-react\backend
uvicorn server:app --reload


## WHY (의사결정 기록)
1. **Q**: 왜 이 방식을 선택했는가?
   **A**:
2. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**:

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | chromaDB로 데이터들이 인덱싱되지않음 |그냥 실행이 안됨 인덱싱 중만 뜨고|파이썬이 최신이라서(3.14) chromaDB 내부의 pydantic v1이랑 호환되지 않음 | python 3.12로 가상화면 새로 만들기 |
|2| 데이터 인덱싱이 안됨 | [자동 인덱싱] 실패: Error code: 400 - {'error': {'message': "'$.input' is invalid. Please check the API reference: https://platform.openai.com/docs/api-reference.", 'type': 'invalid_request_error', 'param': None, 'code': None}}| OpenAI 임베딩 API에 빈 문자열("") 이 들어간 겁니다.| 각 청크에서 공백 제거 후 빈 문자열이면 제외시키기| 

## 회고
- 이번 주 배운 점:
- 다음 주 준비할 것:






RAG파이프 순서 

1. 사전 준비 (문서 저장)
문서를 가져와 작게 쪼갠 뒤, AI가 이해할 수 있는 형태의 암호(숫자 벡터)로 변환하여 데이터베이스에 차곡차곡 저장해 둡니다.

2. 정보 검색 (관련 내용 찾기)
사용자가 질문을 하면, 질문 역시 암호로 변환한 뒤 데이터베이스를 뒤져 질문과 가장 연관성이 높은 문서 조각들을 찾아냅니다.

3. 답변 생성 (최종 답변하기)
미리 찾아낸 문서 조각들을 '참고 자료'로 삼아, AI(GPT, Claude 등)가 사용자의 질문에 대한 정확한 최종 답변을 작성합니다.