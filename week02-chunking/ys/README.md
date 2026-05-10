# 2주차: Chunking - ys

## 기술 스택
| 항목 | 선택 | 대안 | 선택 이유 |
|------|------|------|----------|
| PDF 로드 | pypdf | PyMuPDF, pdfplumber | PDF 파일에서 페이지별 텍스트를 추출하고 page metadata를 저장하기 위해 사용했다. |
| Markdown 로드 | Python pathlib | Markdown 전용 파서 | Markdown 파일은 텍스트 기반 문서이므로 기본 파일 읽기 방식으로도 충분히 처리할 수 있기 때문이다. |
| 텍스트 분할 방식 | RecursiveCharacterTextSplitter | 직접 구현 Splitter, TokenTextSplitter | 문단, 줄바꿈, 문장, 공백 순서로 분할이 가능해서 도메인 데이터를 의미 단위로 나눌 수 있다. |
| 텍스트 정제 | 정규표현식 re | 별도 전처리 라이브러리 | 불필요한 공백, 줄바꿈, 빈 줄을 정리하여 Chunking 품질을 높이기 위해 사용했다. |
| 메타데이터 관리 | JSON 구조 | CSV, SQLite | chunk 내용과 source, page, section, chunk_id 같은 정보를 함께 저장하기 쉽다. |

## 핵심 구현
- 주요 로직 설명:
- 문서 로드: data 폴더에 있는 PDF/Markdown 파일을 읽어와 프로그램에서 처리할 수 있는 텍스트로 변환
- 텍스트 정제: 추출된 텍스트의 불필요한 공백, 줄바꿈, 빈 줄을 정리하여 Chunking 품질 개선
- Chunking 방식: RecursiveCharacterTextSplitter를 사용해 (문단 → 줄바꿈 → 문장 → 공백 순서) 의미가 최대한 끊기지 않게 분할
- Metadata 저장: 각 chunk에 원본 파일명, 문서 유형, PDF 페이지 번호, Markdown 섹션명, chunk 번호, 글자 수를 함께 저장
- 결과 저장: 분할된 chunk는 output/chunks.json에 저장하고, chunk 품질 확인용 output/chunk_report.txt를 생성
- 사용자 질문 처리: 사용자가 질문을 입력하면 chunks.json에 저장된 chunk 중 질문과 관련 있는 내용을 검색하여 참고 문서로 활용할 수 있도록 구성

- 코드 실행 방법:
  - 프로젝트 폴더로 이동  
     cd chunking-study
    
  - 가상환경 생성 및 실행
     python -m venv venv
    .\venv\Scripts\Activate.ps1
    
  - 라이브러리 설치  
     pip install -r requirements.txt
    
  - data 폴더에 PDF 또는 Markdown 파일 추가
    
  - Chunking 실행  
     python main.py
    
  - 사용자 질문 검색 테스트  
     python retriever.py

## WHY (의사결정 기록)
1. **Q**: 왜 이 방식을 선택했는가?
   **A**: PDF와 Markdown 문서를 모두 처리해야 했기 때문에 둘 다 사용할 수 있는 RecursiveCharacterTextSplitter를 선택했다. 이 방식은 글자 수로 자르는 방식보다 의미가 덜 끊기도록 분할할 수 있고 각 chunk에 원본 파일명, 문서 유형, PDF 페이지 번호, Markdown 섹션명 등을 metadata로 저장해 이후 검색 기능이나 RAG 챗봇으로 확장하기 쉽게 구성했다.
2. **Q**: 다르게 구현한다면 어떻게 했을까?
   **A**: 문서 유형에 따라 다른 chunking 전략을 적용했을 것이다. Markdown 문서는 MarkdownHeaderTextSplitter를 사용해 제목 구조를 더 정확히 보존하고, PDF 문서는 페이지 단위뿐 아니라 문단, 표, 제목 구조를 더 세밀하게 분석하도록 구현할 수 있다. 또한 검색 정확도를 높이기 위해 임베딩 기반 Semantic Chunking을 적용해 문장 간 의미 유사도를 기준으로 chunk를 나누는 방식을 적용했을 것이다.

## 트러블슈팅 로그
| # | 문제 상황 | 에러 메시지 | 원인 (Root Cause) | 해결 방법 |
|---|----------|-----------|-------------------|----------|
| 1 | Markdown chunk의 섹션 정보 누락 | metadata의 section 값 없음 | chunk 내부에 제목이 포함되지 않아 chunk의 소속 섹션을 알 수 없음 | Markdown을 먼저 제목 기준으로 분리, 섹션 내부에서 chunking 수행 |

## 회고
- 이번 주 배운 점: 이번 활동을 통해 PDF와 Markdown 문서를 불러오고, 텍스트를 추출한 뒤 정제하는 전체 전처리 흐름을 이해할 수 있었다. 또한 문서를 무작정 자르는 것이 아니라 chunk size, overlap, 문단, 문장, 섹션 구조를 함께 고려해야 검색 품질이 좋아진다는 점을 배웠다. Chunking이 단순한 텍스트 분할이 아니라, 문서를 AI가 활용할 수 있는 지식 단위로 구조화하는 과정이라는 것을 알게 되었다.
- 다음 주 준비할 것: Embedding & Vector DB 공부하기
