"""
2주차: FastAPI 백엔드 서버 - 문서 청킹 시각화

Streamlit(app.py) 대신 FastAPI로 REST API 서버 구현
React 프론트엔드(index.html)와 JSON 방식으로 통신

기능:
  - 파일 업로드 (md / txt / pdf) → 청킹 결과 반환
  - 텍스트 직접 입력 → 청킹 결과 반환
  - chunk_size / chunk_overlap 파라미터 지원
"""

import os
import sys
import tempfile

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# minseon/ 폴더가 상위에 있으므로 경로 추가 (services/ 임포트를 위해)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from services.document_loader import load_document
from services.chunker import chunk_text, chunk_markdown_by_headers

app = FastAPI(title="문서 청킹 API")

# ── CORS 설정 ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 공통 청킹 로직 ─────────────────────────────────────

def run_chunking(text: str, chunk_size: int, chunk_overlap: int, source_name: str) -> dict:
    """텍스트를 청킹하고 결과 dict 반환"""
    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    lengths = [len(c) for c in chunks]

    return {
        "source": source_name,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "stats": {
            "total": len(chunks),
            "avg": round(sum(lengths) / len(lengths)) if lengths else 0,
            "min": min(lengths) if lengths else 0,
            "max": max(lengths) if lengths else 0,
        },
        "chunks": [
            {"index": i, "length": len(c), "content": c}
            for i, c in enumerate(chunks)
        ],
    }


# ── API 엔드포인트 ─────────────────────────────────────

@app.post("/chunk/file")
async def chunk_file(
    file: UploadFile = File(...),
    chunk_size: int = Form(900),
    chunk_overlap: int = Form(90),
):
    """
    파일 업로드 → 청킹 결과 반환

    지원 형식: .md / .txt / .pdf
    """
    suffix = os.path.splitext(file.filename)[1].lower()
    allowed = {".md", ".txt", ".pdf"}
    if suffix not in allowed:
        return {"error": f"지원하지 않는 파일 형식: {suffix}"}

    # 임시 파일로 저장 후 로드
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        text = load_document(tmp_path)
    finally:
        os.unlink(tmp_path)

    return run_chunking(text, chunk_size, chunk_overlap, file.filename)


@app.post("/chunk/text")
async def chunk_text_input(
    text: str = Form(...),
    chunk_size: int = Form(900),
    chunk_overlap: int = Form(90),
):
    """텍스트 직접 입력 → 청킹 결과 반환"""
    if not text.strip():
        return {"error": "텍스트를 입력하세요."}
    return run_chunking(text, chunk_size, chunk_overlap, "직접 입력")


@app.get("/health")
async def health():
    return {"status": "ok"}
