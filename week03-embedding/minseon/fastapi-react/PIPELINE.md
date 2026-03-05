# Week03 RAG 파이프라인 구조 (개발자 메모)

> 이 파일은 내부 참고용입니다. UI에는 표시되지 않습니다.

## 전체 흐름

```
[data/ 폴더]
  ├── AI_기초_개념.md
  └── Python_프로그래밍_기초.md
       │
       ▼ (서버 시작 시 자동 인덱싱)
[embedder.py]
  load_document() → split_text() → embed_texts() → store_embeddings()
       │
       ▼
[vector_db.json]  ← JSON 파일 기반 벡터 DB
  { chunks: [...], vectors: [[...], ...], metadatas: [...] }
       │
       ▼ (사용자 질문 입력)
[/chat/stream 엔드포인트]
  1. embed_texts([질문]) → 질문 벡터
  2. cosine_similarity(질문 벡터, 저장된 벡터들) → 유사도 계산
  3. top_k 청크 추출
  4. system_prompt 선택 (사용자 프리셋)
  5. OpenAI GPT-4o-mini 스트리밍 호출
  6. SSE로 프론트엔드에 전송
```

## 주요 파일

| 파일 | 역할 |
|------|------|
| `backend/server.py` | FastAPI 서버, 엔드포인트 정의, 자동 인덱싱 |
| `../../embedder.py` | 문서 로딩, 청킹, 임베딩, 벡터DB 저장/검색 |
| `../../vector_db.json` | 벡터 DB (청크 텍스트 + 임베딩 벡터) |
| `../../data/` | 자동 인덱싱 대상 문서 폴더 |
| `frontend/index.html` | React CDN 단일 파일 프론트엔드 |

## 프롬프트 프리셋

| ID | 이름 | 특징 |
|----|------|------|
| `default` | 기본 | 정확한 문서 기반 답변 |
| `friendly` | 친절하게 | 따뜻한 어조, 예시 포함 |
| `concise` | 간결하게 | 핵심만 3줄 이내 |
| `simple` | 쉽게 | 중학생 수준, 비유 활용 |
| `expert` | 전문가 | 기술 용어, 심층 분석 |

## 자동 인덱싱 동작

- 서버 시작 시 `@app.on_event("startup")` 트리거
- `data/` 폴더 내 `.md`, `.txt`, `.pdf` 파일 순회
- 이미 인덱싱된 파일(동일 source명)은 덮어쓰기
- 인덱싱 결과 서버 콘솔에 출력

## 청킹 파라미터

```python
CHUNK_SIZE = 900       # 청크당 최대 문자 수
CHUNK_OVERLAP = 90     # 인접 청크 겹침 (문맥 유지)
separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]
```

## 임베딩 모델

- **모델**: `text-embedding-3-small`
- **차원**: 1536
- **비용**: $0.02 / 1M tokens (매우 저렴)
- **특징**: 다국어 지원, 한국어 성능 우수

## SSE 이벤트 포맷

```
data: {"type": "hits", "hits": [...]}     ← 검색 결과 (먼저 전송)
data: {"type": "text", "content": "..."}  ← 텍스트 스트리밍 (여러 번)
data: {"type": "done"}                    ← 완료 신호
```
