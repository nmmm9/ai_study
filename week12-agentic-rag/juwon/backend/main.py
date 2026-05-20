"""
main.py - FastAPI 서버 (week12 Agentic RAG)

week11 대비 변경사항:
  POST /api/chat         → Agentic RAG (도구 호출 단계 포함 반환)
  GET  /api/history      → Supabase에서 조회
  GET  /api/history/stats → 트렌드 차트용 시계열 통계
  GET  /api/keywords     → 구독 키워드 목록
  POST /api/keywords     → 키워드 추가
  DELETE /api/keywords/{keyword} → 키워드 삭제

실행: uvicorn main:app --reload --port 8000
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agentic_chat import run_agentic_chat
from compare import compare_reports
from graph import run_analysis
from notifier import send_gmail, send_keyword_alert, upload_github_readme
from scheduler import get_status, scheduler, update_schedule
from storage import (
    load_all_history, load_latest_history,
    get_keywords, add_keyword, delete_keyword, check_keyword_matches,
)
from vector_store import load_history_stats

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    print("[server] APScheduler 시작")
    yield
    scheduler.shutdown()
    print("[server] APScheduler 종료")


app = FastAPI(title="GitHub Trend Agentic RAG API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request models ────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    language: str = ""
    period:   str = "weekly"

class NotifyRequest(BaseModel):
    judge_decision: str
    language:       str = "전체"
    period:         str = "weekly"

class ScheduleRequest(BaseModel):
    enabled:  bool = False
    hour:     int  = 9
    minute:   int  = 0
    language: str  = ""
    period:   str  = "daily"

class ChatRequest(BaseModel):
    message: str
    report:  dict

class KeywordRequest(BaseModel):
    keyword: str


# ── 헬스체크 ─────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── 분석 ──────────────────────────────────────────────────────

@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    previous = load_latest_history()
    report   = run_analysis(language=req.language, period=req.period)

    prev_repos          = previous.get("repos", []) if previous else []
    report["comparison"] = compare_reports(report.get("repos", []), prev_repos)

    # 키워드 구독 알림
    matched = check_keyword_matches(report.get("repos", []))
    if matched:
        send_keyword_alert(matched, req.language or "전체")
    report["keyword_matches"] = matched

    return report


# ── 히스토리 ──────────────────────────────────────────────────

@app.get("/api/history")
def history():
    return load_all_history()

@app.get("/api/history/latest")
def latest():
    data = load_latest_history()
    return data or {}

@app.get("/api/history/stats")
def history_stats():
    """트렌드 차트용 시계열 통계"""
    return load_history_stats()


# ── 채팅 (Agentic RAG) ────────────────────────────────────────

@app.post("/api/chat")
def chat(req: ChatRequest):
    """
    Agentic RAG 채팅.
    에이전트가 스스로 RAG 도구를 호출해서 답변.
    반환에 steps(도구 호출 과정)가 포함됨.
    """
    result = run_agentic_chat(req.message, req.report)
    return result


# ── 스케줄 ────────────────────────────────────────────────────

@app.get("/api/schedule")
def schedule_status():
    return get_status()

@app.post("/api/schedule")
def schedule_update(req: ScheduleRequest):
    update_schedule(
        enabled=req.enabled,
        hour=req.hour,
        minute=req.minute,
        language=req.language,
        period=req.period,
    )
    return get_status()


# ── 알림 ──────────────────────────────────────────────────────

@app.post("/api/notify/email")
def notify_email(req: NotifyRequest):
    ok = send_gmail(req.judge_decision, req.language, req.period)
    if not ok:
        raise HTTPException(status_code=500, detail="메일 전송 실패")
    return {"status": "success", "message": "메일 전송 완료"}

@app.post("/api/notify/github")
def notify_github(req: NotifyRequest):
    ok = upload_github_readme(req.judge_decision, req.language, req.period)
    if not ok:
        raise HTTPException(status_code=500, detail="GitHub 업로드 실패")
    return {"status": "success", "message": "GitHub README 업로드 완료"}


# ── 키워드 구독 ───────────────────────────────────────────────

@app.get("/api/keywords")
def list_keywords():
    return {"keywords": get_keywords()}

@app.post("/api/keywords")
def create_keyword(req: KeywordRequest):
    kw = req.keyword.strip().lower()
    if not kw:
        raise HTTPException(status_code=400, detail="키워드를 입력하세요")
    ok = add_keyword(kw)
    if not ok:
        raise HTTPException(status_code=409, detail="이미 등록된 키워드입니다")
    return {"keywords": get_keywords()}

@app.delete("/api/keywords/{keyword}")
def remove_keyword(keyword: str):
    delete_keyword(keyword)
    return {"keywords": get_keywords()}
