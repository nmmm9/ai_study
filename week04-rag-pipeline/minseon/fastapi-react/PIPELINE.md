# Week04 RAG 파이프라인 구조 (개발자 메모)

> 이 파일은 내부 참고용입니다. UI에는 표시되지 않습니다.

## 전체 흐름

```
[data/ 폴더]
  ├── 청년_교육장학_종합.md
  ├── 청년_금융지원_종합.md
  ├── 청년_복지건강_종합.md
  ├── 청년_주거지원_종합.md
  └── 청년_취업지원_종합.md
       │
       ▼ (서버 시작 시 @app.on_event("startup") 자동 인덱싱)
[rag_pipeline.py]
  index_document()
    └── document_service.load_document()    → 텍스트 추출
    └── chunking_service.split_text()       → Recursive Splitting
    └── embedding_service.embed_texts()     → 1536차원 벡터
    └── vector_store.add()                  → JSON DB 저장
       │
       ▼ (사용자 질문)
[/chat/stream 엔드포인트]
  chat_stream(message, top_k, threshold, max_per_source, preset)
    └── search() → embed(질문) → cosine_similarity → top_k 청크
    └── _build_system_prompt(hits, preset) → 프롬프트 선택
    └── llm_service.stream_response()       → GPT-4o-mini SSE
```

## 주요 파일

| 파일 | 역할 |
|------|------|
| `backend/server.py` | FastAPI 서버, 자동 인덱싱, SSE 엔드포인트 |
| `../../rag_pipeline.py` | 파이프라인 오케스트레이터 |
| `../../services/document_service.py` | md/txt/pdf 로딩 |
| `../../services/chunking_service.py` | 텍스트 청킹 |
| `../../services/embedding_service.py` | OpenAI 임베딩 |
| `../../services/vector_store.py` | 벡터 저장/검색 |
| `../../services/llm_service.py` | GPT 스트리밍 + 대화 관리 |
| `../../vector_db.json` | 벡터 DB |
| `../../data/` | 자동 인덱싱 대상 문서 |
| `frontend/index.html` | React CDN 단일 파일 UI |

## 프롬프트 프리셋

| ID | 이름 | 특징 |
|----|------|------|
| `default` | 📚 기본 | 정확한 문서 기반, 구조화된 답변 |
| `friendly` | 🤝 친절하게 | 따뜻한 어조, 예시·비유 포함 |
| `concise` | ⚡ 간결하게 | 핵심만 3~5줄 |
| `simple` | 🎓 쉽게 | 중학생 수준, 어려운 용어 풀이 |
| `expert` | 💼 전문가 | 법령 근거, 유사 정책 비교, 심층 분석 |

## 자동 인덱싱 동작

- 서버 시작 시 `@app.on_event("startup")` 트리거
- `data/` 폴더 내 `.md`, `.txt` 파일 순회
- 이미 인덱싱된 파일(동일 source명)은 건너뜀
- 콘솔에 `[자동 인덱싱] 파일명 → N개 청크` 출력

## 검색 파라미터 (사이드바 슬라이더)

| 파라미터 | 기본값 | 설명 |
|---------|-------|------|
| `top_k` | 5 | 검색할 최대 청크 수 |
| `threshold` | 0.2 | 최소 코사인 유사도 |
| `max_per_source` | 2 | 같은 문서에서 최대 청크 수 (소스 다양성) |

## SSE 이벤트 포맷

```
data: {"type": "text",  "content": "..."}        ← 텍스트 스트리밍
data: {"type": "hits",  "hits": [...]}            ← 검색된 출처
data: {"type": "usage", "input": N, "output": N}  ← 토큰 사용량
data: {"type": "done"}                            ← 완료
```

## 청킹 파라미터

```python
CHUNK_SIZE = 600
CHUNK_OVERLAP = 60
separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]
```
