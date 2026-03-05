"""
3주차: FastAPI 백엔드 서버 - 임베딩 & 벡터DB 시각화

엔드포인트:
  POST /embed/single   - 텍스트 1개 임베딩 → 벡터 정보 반환 (시각화용)
  POST /embed/compare  - 텍스트 2개 비교 → 코사인 유사도 + 벡터 반환
  POST /search         - 질문으로 유사 청크 검색
  POST /chat/stream    - RAG 챗봇 (SSE 스트리밍)
  GET  /sources        - 인덱싱된 파일 목록
  GET  /stats          - 벡터DB 통계
  GET  /health         - 서버 상태
"""

import glob
import json
import os
import sys
import tempfile

import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI as OAI

# embedder.py가 상위 폴더에 있으므로 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from embedder import (
    embed_texts, load_document, split_text, store_embeddings,
    cosine_similarity, search, load_db, EMBEDDING_MODEL,
)

app = FastAPI(title="임베딩 시각화 API")

# data/ 폴더 경로 (서버 기준 상위 두 단계)
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))


@app.on_event("startup")
async def auto_index():
    """서버 시작 시 data/ 폴더 자동 인덱싱"""
    if not os.path.isdir(DATA_DIR):
        print(f"[자동 인덱싱] data/ 폴더 없음: {DATA_DIR}")
        return
    files = glob.glob(os.path.join(DATA_DIR, "**", "*"), recursive=True)
    targets = [f for f in files if os.path.isfile(f) and os.path.splitext(f)[1].lower() in {".md", ".txt", ".pdf"}]
    if not targets:
        print("[자동 인덱싱] 인덱싱할 파일 없음")
        return
    for path in targets:
        name = os.path.basename(path)
        try:
            text    = load_document(path)
            chunks  = split_text(text)
            vectors = embed_texts(chunks)
            store_embeddings(chunks, vectors, name)
            print(f"[자동 인덱싱] {name} → {len(chunks)}개 청크")
        except Exception as e:
            print(f"[자동 인덱싱] {name} 실패: {e}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 요청 모델 ──────────────────────────────────────────
class SingleEmbedRequest(BaseModel):
    text: str

class CompareRequest(BaseModel):
    text1: str
    text2: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3

class ChatRequest(BaseModel):
    message: str
    top_k: int = 3
    system_prompt: str | None = None


# ── 유틸 ──────────────────────────────────────────────
def vector_stats(vector: list[float]) -> dict:
    """벡터 통계 (시각화에 사용)"""
    arr = np.array(vector)
    return {
        "dimension":  len(vector),
        "min":        round(float(arr.min()), 4),
        "max":        round(float(arr.max()), 4),
        "mean":       round(float(arr.mean()), 4),
        "norm":       round(float(np.linalg.norm(arr)), 4),
        "preview_30": [round(v, 4) for v in vector[:30]],  # 첫 30차원 (막대그래프용)
    }


# ── 엔드포인트 ─────────────────────────────────────────

@app.post("/embed/single")
async def embed_single(req: SingleEmbedRequest):
    """
    텍스트 1개 임베딩 후 벡터 정보 반환

    반환값:
      - vector_stats: 차원·최솟값·최댓값·평균·L2 노름·첫 30차원 값
      - model: 사용된 임베딩 모델명
    """
    vector = embed_texts([req.text])[0]
    return {
        "text":   req.text,
        "model":  EMBEDDING_MODEL,
        "stats":  vector_stats(vector),
    }


@app.post("/embed/compare")
async def embed_compare(req: CompareRequest):
    """
    텍스트 2개를 임베딩하고 코사인 유사도 계산

    반환값:
      - similarity: 코사인 유사도 (0~1)
      - interpretation: 유사도 해석 텍스트
      - stats1, stats2: 각 텍스트의 벡터 통계
    """
    vectors = embed_texts([req.text1, req.text2])
    v1, v2 = vectors[0], vectors[1]
    sim = cosine_similarity(v1, v2)

    if sim >= 0.9:
        interp = "매우 유사 — 거의 같은 의미"
    elif sim >= 0.7:
        interp = "유사 — 비슷한 주제/의미"
    elif sim >= 0.5:
        interp = "보통 — 약간 관련 있음"
    elif sim >= 0.3:
        interp = "낮음 — 관련성 적음"
    else:
        interp = "매우 낮음 — 전혀 다른 내용"

    return {
        "text1":          req.text1,
        "text2":          req.text2,
        "similarity":     round(sim, 4),
        "similarity_pct": round(sim * 100, 1),
        "interpretation": interp,
        "model":          EMBEDDING_MODEL,
        "stats1":         vector_stats(v1),
        "stats2":         vector_stats(v2),
    }


@app.post("/index")
async def index_file(file: UploadFile = File(...)):
    """파일 업로드 → 청킹 → 임베딩 → 저장"""
    suffix = os.path.splitext(file.filename)[1].lower()
    if suffix not in {".md", ".txt", ".pdf"}:
        return {"error": f"지원하지 않는 형식: {suffix}"}

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        text    = load_document(tmp_path)
        chunks  = split_text(text)
        vectors = embed_texts(chunks)
        store_embeddings(chunks, vectors, file.filename)
    finally:
        os.unlink(tmp_path)

    return {
        "source": file.filename,
        "chunks": len(chunks),
        "chars":  len(text),
        "dims":   len(vectors[0]) if vectors else 0,
    }


@app.post("/search")
async def search_query(req: SearchRequest):
    """질문으로 유사한 청크 검색"""
    hits = search(req.query, top_k=req.top_k)
    return {
        "query": req.query,
        "hits": [
            {
                "content":     h["content"],
                "similarity":  round(h["similarity"], 4),
                "sim_pct":     round(h["similarity"] * 100, 1),
                "source":      h["metadata"]["source"],
                "chunk_index": h["metadata"]["chunk_index"],
            }
            for h in hits
        ],
    }


PROMPT_PRESETS = {
    "default":  "아래 참고 문서를 바탕으로 질문에 정확하게 답변하세요. 문서에 없는 내용은 '문서에서 찾을 수 없습니다'라고 답하세요. 한국어로 답변합니다.",
    "friendly": "아래 참고 문서를 바탕으로 친절하고 따뜻한 어조로 답변하세요. 예시나 비유를 곁들여 이해하기 쉽게 설명해 주세요. 한국어로 답변합니다.",
    "concise":  "아래 참고 문서를 바탕으로 핵심만 3줄 이내로 간결하게 답변하세요. 불필요한 설명은 생략합니다. 한국어로 답변합니다.",
    "simple":   "아래 참고 문서를 바탕으로 중학생도 이해할 수 있게 쉽게 설명하세요. 어려운 용어는 풀어서 설명하고 일상적인 비유를 활용하세요. 한국어로 답변합니다.",
    "expert":   "아래 참고 문서를 바탕으로 전문가 수준으로 깊이 있게 분석하고 답변하세요. 기술 용어와 세부 메커니즘을 포함해 심층적으로 설명하세요. 한국어로 답변합니다.",
}

NO_CONTEXT_PROMPT = "인덱싱된 문서가 없습니다. 일반 지식으로 답변하되 '문서 없음'을 안내해주세요. 한국어로 답변합니다."


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """RAG 챗봇: 문서 검색 → GPT 스트리밍 답변"""
    hits = search(req.message, top_k=req.top_k)

    context = "\n\n---\n\n".join([
        f"[출처: {h['metadata']['source']}]\n{h['content']}"
        for h in hits
    ]) if hits else ""

    if context:
        base = req.system_prompt or PROMPT_PRESETS["default"]
        system_prompt = f"{base}\n\n[참고 문서]\n{context}"
    else:
        system_prompt = NO_CONTEXT_PROMPT

    hits_payload = [
        {
            "content":     h["content"][:200],
            "sim_pct":     round(h["similarity"] * 100, 1),
            "source":      h["metadata"]["source"],
            "chunk_index": h["metadata"]["chunk_index"],
        }
        for h in hits
    ]

    def generate():
        yield f"data: {json.dumps({'type':'hits','hits':hits_payload}, ensure_ascii=False)}\n\n"
        client = OAI()
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": req.message},
            ],
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield f"data: {json.dumps({'type':'text','content':chunk.choices[0].delta.content}, ensure_ascii=False)}\n\n"
        yield "data: {\"type\":\"done\"}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/sources")
async def get_sources():
    """인덱싱된 파일 목록"""
    db = load_db()
    counts: dict[str, int] = {}
    for m in db.get("metadatas", []):
        src = m.get("source", "unknown")
        counts[src] = counts.get(src, 0) + 1
    return [{"source": k, "chunks": v} for k, v in counts.items()]


@app.delete("/sources/{name:path}")
async def delete_source(name: str):
    """파일 삭제"""
    db = load_db()
    before = len(db["chunks"])
    keep = [
        (c, v, m)
        for c, v, m in zip(db["chunks"], db["vectors"], db["metadatas"])
        if m.get("source") != name
    ]
    if keep:
        db["chunks"], db["vectors"], db["metadatas"] = map(list, zip(*keep))
    else:
        db = {"chunks": [], "vectors": [], "metadatas": []}

    from embedder import save_db
    save_db(db)
    return {"success": len(db["chunks"]) < before}


@app.get("/stats")
async def get_stats():
    db = load_db()
    counts: dict[str, int] = {}
    for m in db.get("metadatas", []):
        src = m.get("source", "unknown")
        counts[src] = counts.get(src, 0) + 1
    return {
        "total_chunks":    len(db["chunks"]),
        "total_documents": len(counts),
        "embedding_model": EMBEDDING_MODEL,
        "vector_dim":      len(db["vectors"][0]) if db["vectors"] else 0,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "model": EMBEDDING_MODEL}
