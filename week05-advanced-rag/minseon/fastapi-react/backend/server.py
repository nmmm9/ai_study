"""
5주차: FastAPI 백엔드 - Advanced RAG 파이프라인

[4주차 대비 변경점]
  - AdvancedRagPipeline 사용 (Multi-query + Hybrid Search + Re-ranking + Compression)
  - SSE 이벤트에 파이프라인 단계별 중간 결과 추가
    {"type": "pipeline", "stage": "pre",       "queries": [...]}
    {"type": "pipeline", "stage": "retrieval", "count": N, "queries_used": N}
    {"type": "pipeline", "stage": "post",      "reranked": N, "compressed": N}
  - 프론트엔드에서 각 단계를 실시간으로 시각화 가능

엔드포인트:
  POST /chat/stream       - SSE 스트리밍 (파이프라인 단계 이벤트 포함)
  GET  /sources           - 인덱싱된 문서 목록
  POST /index             - 문서 업로드 & 인덱싱
  DELETE /sources/{name}  - 문서 삭제
  POST /auto-index        - data/ 폴더 자동 인덱싱
  GET  /stats             - 통계
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

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# rag_pipeline.py 가 상위 두 단계에 있으므로 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from rag_pipeline import AdvancedRagPipeline
from services.embedding_service import embed_texts
from services.llm_service import stream_response
from services.cost_tracker import CostTracker

app = FastAPI(title="Advanced RAG 챗봇 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = AdvancedRagPipeline()


@app.on_event("startup")
async def auto_index_on_startup():
    try:
        results = rag.auto_index_data_dir()
        for r in results:
            print(f"[자동 인덱싱] {r['source']} → {r['chunks']}개 청크")
        if not results:
            print("[자동 인덱싱] 새로 인덱싱할 파일 없음")
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
    use_compression: bool = True


# ── SSE 스트리밍 제너레이터 ────────────────────────────────
async def stream_generator(req: ChatRequest):
    """
    Advanced RAG 파이프라인을 단계별로 실행하며 SSE 이벤트 전송

    SSE 이벤트 타입:
      {"type": "pipeline", "stage": "pre",       "queries": [...]}
      {"type": "pipeline", "stage": "retrieval", "count": N, "queries_used": N}
      {"type": "pipeline", "stage": "post",      "reranked": N, "compressed": N}
      {"type": "text",     "content": "..."}
      {"type": "hits",     "hits": [...]}
      {"type": "usage",    "input": N, "output": N}
      {"type": "cost",     ...cost_summary}
      {"type": "done"}
    """
    def sse(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    tracker = CostTracker()

    try:
        # ── Step 1: Pre-retrieval (Multi-query Generation) ─────
        tracker.start_stage("pre")
        queries = rag._generate_queries(req.message, tracker)
        tracker.end_stage("pre")
        rag._last_queries = queries
        yield sse({"type": "pipeline", "stage": "pre", "queries": queries})

        # ── Step 2: Retrieval (Hybrid Search) ─────────────────
        tracker.start_stage("retrieval")
        candidates = rag._hybrid_search_all(
            queries, req.top_k, req.threshold, req.max_per_source, tracker
        )
        tracker.end_stage("retrieval")
        rag._last_candidates = candidates
        yield sse({
            "type": "pipeline",
            "stage": "retrieval",
            "count": len(candidates),
            "queries_used": len(queries),
        })

        # ── Step 3: Post-retrieval (Re-rank + Compress) ────────
        tracker.start_stage("post")
        final_hits = rag._post_process(
            req.message, candidates, req.top_k, req.use_compression, tracker
        )
        tracker.end_stage("post")
        compressed_count = sum(1 for h in final_hits if h.get("compressed"))
        yield sse({
            "type": "pipeline",
            "stage": "post",
            "reranked": len(final_hits),
            "compressed": compressed_count,
        })

        # ── Step 4: Generation (LLM 스트리밍) ──────────────────
        tracker.start_stage("generation")
        system_content = rag._build_system_prompt(final_hits)
        for token in stream_response(system_content, rag.conversation, req.message, tracker=tracker):
            yield sse({"type": "text", "content": token})
        tracker.end_stage("generation")

        # ── Step 5: 메타데이터 전송 ────────────────────────────
        usage = getattr(stream_response, "_last_usage", {"input": 0, "output": 0})
        hits_payload = [
            {
                "source":      h["metadata"]["source"],
                "similarity":  round(h["similarity"], 4),
                "chunk_index": h["metadata"]["chunk_index"],
                "preview":     h["content"][:150].replace("\n", " "),
                "content":     h["content"],
                "compressed":  h.get("compressed", False),
            }
            for h in final_hits
        ]
        cost_summary = tracker.get_summary()
        yield sse({"type": "hits",  "hits": hits_payload})
        yield sse({"type": "usage", "input": usage["input"], "output": usage["output"]})
        yield sse({"type": "cost",  **cost_summary})
        yield sse({"type": "done"})

    except Exception as e:
        yield sse({"type": "error", "message": str(e)})
        yield sse({"type": "done"})


# ── API 엔드포인트 ─────────────────────────────────────────

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    return StreamingResponse(
        stream_generator(req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/sources")
async def get_sources():
    return rag.get_indexed_sources()


@app.post("/index")
async def index_document(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1].lower()
    if suffix not in {".md", ".txt", ".pdf"}:
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
    success = rag.delete_source(name)
    return {"success": success}


@app.post("/auto-index")
async def auto_index():
    results = rag.auto_index_data_dir()
    return {"indexed": results, "count": len(results)}


@app.get("/stats")
async def get_stats():
    return rag.get_stats()


@app.delete("/chat")
async def reset_chat():
    rag.reset_conversation()
    return {"status": "reset"}


@app.get("/health")
async def health():
    return {"status": "ok"}
