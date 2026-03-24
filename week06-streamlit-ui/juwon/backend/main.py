"""
취업 상담 AI - FastAPI 백엔드
배포: Railway (https://railway.app)
"""
import os
import sys
import json
import asyncio
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# RAG 파이프라인 (같은 폴더의 rag_pipeline.py 사용)
sys.path.insert(0, str(Path(__file__).parent))
from rag_pipeline import AdvancedRAGPipeline, DocumentLoader, extract_metadata_with_parents

from supabase import create_client
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 파이프라인 초기화 (앱 시작 시 1회)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BASE_DIR = Path(__file__).parent
pipeline: Optional[AdvancedRAGPipeline] = None


def init_pipeline():
    global pipeline
    p = AdvancedRAGPipeline()
    all_chunks = []
    for fname in ["job_postings.md", "job_postings_crawled.md"]:
        fpath = BASE_DIR / fname
        if fpath.exists():
            raw = DocumentLoader.load(str(fpath))
            chunks = extract_metadata_with_parents(raw, str(fpath))
            all_chunks.extend(chunks)
    if all_chunks:
        p.store.build(all_chunks)
    pipeline = p
    print(f"✅ 파이프라인 초기화 완료 ({len(all_chunks)}개 청크)")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FastAPI 앱
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app = FastAPI(title="취업 상담 AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 Vercel 도메인으로 교체
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, init_pipeline)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Auth
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class AuthRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/login")
async def login(req: AuthRequest):
    try:
        res = supabase.auth.sign_in_with_password({"email": req.email, "password": req.password})
        return {
            "user":  {"id": res.user.id, "email": res.user.email},
            "token": res.session.access_token,
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/auth/signup")
async def signup(req: AuthRequest):
    try:
        res = supabase.auth.sign_up({"email": req.email, "password": req.password})
        return {"user": {"id": res.user.id, "email": res.user.email}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 인증 미들웨어
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_user_id(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 필요")
    token = authorization.split(" ")[1]
    try:
        user = supabase.auth.get_user(token)
        return user.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 채팅 (SSE 스트리밍)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ChatRequest(BaseModel):
    message: str
    filter_stack:  str = ""
    filter_career: str = "전체"


@app.post("/api/chat")
async def chat(req: ChatRequest, user_id: str = Depends(get_user_id)):
    if not pipeline:
        raise HTTPException(status_code=503, detail="파이프라인 초기화 중입니다. 잠시 후 다시 시도하세요.")

    # 필터 적용
    filter_parts = []
    if req.filter_stack.strip():
        filter_parts.append(f"기술스택: {req.filter_stack.strip()}")
    if req.filter_career != "전체":
        filter_parts.append(f"경력: {req.filter_career}")
    query = f"[검색 조건 - {', '.join(filter_parts)}] {req.message}" if filter_parts else req.message

    def generate():
        try:
            for event in pipeline.ask_stream(query):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 대화 히스토리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.get("/api/conversations")
async def get_conversations(user_id: str = Depends(get_user_id)):
    try:
        res = (supabase.table("conversations")
               .select("*").eq("user_id", user_id)
               .order("updated_at", desc=True).execute())
        return res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SaveConvRequest(BaseModel):
    id:       str
    title:    str
    messages: list


@app.post("/api/conversations")
async def save_conversation(req: SaveConvRequest, user_id: str = Depends(get_user_id)):
    try:
        supabase.table("conversations").upsert({
            "id":         req.id,
            "user_id":    user_id,
            "title":      req.title,
            "messages":   req.messages,
            "updated_at": datetime.now().isoformat(),
        }).execute()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str, user_id: str = Depends(get_user_id)):
    try:
        supabase.table("conversations").delete().eq("id", conv_id).execute()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Top-3 유사 공고 카드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.get("/api/top3")
async def top3(query: str, user_id: str = Depends(get_user_id)):
    if not pipeline:
        return []
    try:
        results = pipeline.store.search_hybrid(query, top_k=3)
        return [
            {"company": cm.company, "section": cm.section, "snippet": cm.text[:150]}
            for _, cm in results[:3]
        ]
    except Exception:
        return []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 회사 목록 / 토큰 사용량
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.get("/api/companies")
async def companies(user_id: str = Depends(get_user_id)):
    if not pipeline:
        return []
    return sorted(list(pipeline.store._companies))


@app.get("/api/token-usage")
async def token_usage(user_id: str = Depends(get_user_id)):
    if not pipeline:
        return {"input": 0, "output": 0}
    return pipeline.token_usage


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 북마크
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOOKMARKS_FILE = BASE_DIR / "bookmarks.json"


def _load_bms():
    if BOOKMARKS_FILE.exists():
        try:
            return json.loads(BOOKMARKS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_bms(bms):
    BOOKMARKS_FILE.write_text(json.dumps(bms, ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/api/bookmarks")
async def get_bookmarks(user_id: str = Depends(get_user_id)):
    return _load_bms()


class BookmarkRequest(BaseModel):
    id:        str
    question:  str
    answer:    str
    citations: list = []


@app.post("/api/bookmarks")
async def save_bookmark(req: BookmarkRequest, user_id: str = Depends(get_user_id)):
    bms = _load_bms()
    if not any(b["id"] == req.id for b in bms):
        bms.append({
            "id": req.id, "question": req.question,
            "answer": req.answer, "citations": req.citations,
            "saved_at": datetime.now().strftime("%m/%d %H:%M"),
        })
        _save_bms(bms)
    return {"ok": True}


@app.delete("/api/bookmarks/{bid}")
async def delete_bookmark_api(bid: str, user_id: str = Depends(get_user_id)):
    _save_bms([b for b in _load_bms() if b["id"] != bid])
    return {"ok": True}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 파일 업로드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from fastapi import UploadFile, File

UPLOADS_DIR  = BASE_DIR / "uploads"
UPLOADS_LIST = BASE_DIR / "uploaded_files.json"
UPLOADS_DIR.mkdir(exist_ok=True)


def _get_upload_list() -> list[str]:
    """저장된 업로드 파일명 목록 반환 (파일명만 저장)"""
    if UPLOADS_LIST.exists():
        try:
            return json.loads(UPLOADS_LIST.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_upload_list(names: list[str]):
    UPLOADS_LIST.write_text(json.dumps(names, ensure_ascii=False), encoding="utf-8")


def _rebuild_pipeline():
    global pipeline
    all_chunks = []
    # 기본 문서
    for fname in ["job_postings.md", "job_postings_crawled.md"]:
        fpath = BASE_DIR / fname
        if fpath.exists():
            raw    = DocumentLoader.load(str(fpath))
            chunks = extract_metadata_with_parents(raw, str(fpath))
            all_chunks.extend(chunks)
    # 업로드 문서 (파일명 → UPLOADS_DIR 경로로 변환)
    for fname in _get_upload_list():
        fpath = UPLOADS_DIR / fname
        if fpath.exists():
            raw    = DocumentLoader.load(str(fpath))
            chunks = extract_metadata_with_parents(raw, str(fpath))
            all_chunks.extend(chunks)
            print(f"  [업로드] {fname} 로드 완료 ({len(chunks)}개 청크)")
    new_p = AdvancedRAGPipeline()
    if all_chunks:
        new_p.store.build(all_chunks)
    pipeline = new_p
    print(f"✅ 파이프라인 재빌드 완료 (총 {len(all_chunks)}개 청크)")


def _add_file_to_pipeline(fpath: Path):
    """파일 하나만 기존 파이프라인에 추가 (빠름)"""
    global pipeline
    if not pipeline:
        _rebuild_pipeline()
        return
    raw    = DocumentLoader.load(str(fpath))
    chunks = extract_metadata_with_parents(raw, str(fpath))
    pipeline.store.add_chunks(chunks)
    print(f"✅ {fpath.name} 추가 완료 ({len(chunks)}개 청크)")


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), user_id: str = Depends(get_user_id)):
    save_path = UPLOADS_DIR / file.filename
    save_path.write_bytes(await file.read())
    names = _get_upload_list()
    if file.filename not in names:
        names.append(file.filename)
        _save_upload_list(names)
    # 전체 재빌드 대신 새 파일만 추가 → 훨씬 빠름
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _add_file_to_pipeline, save_path)
    return {"ok": True, "filename": file.filename}


@app.get("/api/uploads")
async def get_uploads(user_id: str = Depends(get_user_id)):
    return [f for f in _get_upload_list() if (UPLOADS_DIR / f).exists()]


@app.delete("/api/uploads/{filename}")
async def delete_upload(filename: str, user_id: str = Depends(get_user_id)):
    names = _get_upload_list()
    if filename in names:
        (UPLOADS_DIR / filename).unlink(missing_ok=True)
        _save_upload_list([f for f in names if f != filename])
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _rebuild_pipeline)
    return {"ok": True}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 헬스체크
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.get("/api/health")
async def health():
    return {"status": "ok", "pipeline_ready": pipeline is not None}
