"""
4주차: FastAPI 백엔드 서버 - RAG 파이프라인

Streamlit(app.py) 대신 FastAPI로 REST API 서버 구현
React 프론트엔드(index.html)와 JSON + SSE 방식으로 통신

엔드포인트:
  POST /chat/stream       - SSE 스트리밍 RAG 챗봇
  GET  /sources           - 인덱싱된 문서 목록
  POST /index             - 문서 파일 업로드 & 인덱싱
  DELETE /sources/{name}  - 문서 삭제
  POST /auto-index        - data/ 폴더 자동 인덱싱
  GET  /stats             - 파이프라인 통계
  GET  /pipeline-info     - 파이프라인 동작 방식 설명
  DELETE /chat            - 대화 초기화
  GET  /health            - 서버 상태 확인
"""

import json
import os
import sys
import tempfile

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# .env 파일을 server.py 기준 상위 두 단계(minseon/)에서 로드
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# rag_pipeline.py가 상위 폴더에 있으므로 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from rag_pipeline import RagPipeline

app = FastAPI(title="청년정책 RAG 챗봇 API")

# ── CORS 설정 ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── RAG 파이프라인 초기화 ──────────────────────────────────
rag = RagPipeline()


@app.on_event("startup")
async def auto_index_on_startup():
    """서버 시작 시 data/ 폴더 자동 인덱싱"""
    try:
        results = rag.auto_index_data_dir()
        for r in results:
            print(f"[자동 인덱싱] {r['source']} → {r['chunks']}개 청크")
        if not results:
            print("[자동 인덱싱] 새로 인덱싱할 파일 없음 (이미 완료됨)")
    except Exception as e:
        import traceback
        print(f"[자동 인덱싱] 실패: {e}")
        traceback.print_exc()


# ── 요청 모델 ──────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    top_k: int = 5
    threshold: float = 0.2
    max_per_source: int = 2
    preset: str = "default"


# ── 스트리밍 제너레이터 ────────────────────────────────────
async def stream_generator(req: ChatRequest):
    """
    RAG 스트리밍 응답을 SSE 형식으로 변환

    SSE 메시지 타입:
      {"type": "text",  "content": "..."}   - 텍스트 토큰
      {"type": "hits",  "hits": [...]}       - 검색된 출처 정보
      {"type": "usage", "input": N, "output": N}  - 토큰 사용량
      {"type": "done"}                       - 완료 신호
    """
    for token in rag.chat_stream(
        req.message,
        top_k=req.top_k,
        threshold=req.threshold,
        max_per_source=req.max_per_source,
        preset=req.preset,
    ):
        yield f"data: {json.dumps({'type': 'text', 'content': token}, ensure_ascii=False)}\n\n"

    # 스트리밍 종료 후 메타데이터 전송
    hits = getattr(rag, "_last_hits", [])
    usage = getattr(rag, "_last_usage", {"input": 0, "output": 0})

    # 출처 정보 (source, similarity, chunk_index, content 미리보기 포함)
    hits_payload = [
        {
            "source":      h["metadata"]["source"],
            "similarity":  round(h["similarity"], 4),
            "chunk_index": h["metadata"]["chunk_index"],
            "preview":     h["content"][:150].replace("\n", " "),
            "content":     h["content"],
        }
        for h in hits
    ]

    yield f"data: {json.dumps({'type': 'hits', 'hits': hits_payload}, ensure_ascii=False)}\n\n"
    yield f"data: {json.dumps({'type': 'usage', 'input': usage['input'], 'output': usage['output']})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


# ── API 엔드포인트 ─────────────────────────────────────────

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE 스트리밍 RAG 챗봇 응답"""
    return StreamingResponse(
        stream_generator(req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/sources")
async def get_sources():
    """인덱싱된 문서 목록 반환"""
    return rag.get_indexed_sources()


@app.post("/index")
async def index_document(file: UploadFile = File(...)):
    """파일 업로드 후 인덱싱"""
    suffix = os.path.splitext(file.filename)[1].lower()
    allowed = {".md", ".txt", ".pdf"}
    if suffix not in allowed:
        return {"error": f"지원하지 않는 파일 형식: {suffix}"}

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        result = rag.index_document(tmp_path, source_name=file.filename)
    finally:
        os.unlink(tmp_path)

    return result


@app.delete("/sources/{name:path}")
async def delete_source(name: str):
    """문서 삭제"""
    success = rag.delete_source(name)
    return {"success": success}


@app.post("/auto-index")
async def auto_index():
    """data/ 폴더 자동 인덱싱"""
    results = rag.auto_index_data_dir()
    return {"indexed": results, "count": len(results)}


@app.get("/stats")
async def get_stats():
    """파이프라인 통계"""
    return rag.get_stats()


@app.get("/pipeline-info")
async def get_pipeline_info():
    """파이프라인 동작 방식 설명"""
    return rag.get_pipeline_info()


@app.delete("/chat")
async def reset_chat():
    """대화 히스토리 초기화"""
    rag.reset_conversation()
    return {"status": "reset"}


@app.get("/health")
async def health():
    return {"status": "ok"}
