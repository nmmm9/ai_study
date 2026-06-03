"""
main.py - FastAPI 서버 (Week 13: Agentic RAG + 평가 시스템)

실행: uvicorn main:app --reload --port 8000

엔드포인트:
POST /api/analyze          → 트렌드 분석 (RAG 강화)
GET  /api/history          → 전체 분석 히스토리
GET  /api/history/latest   → 최신 분석
GET  /api/history/stats    → 트렌드 차트용 통계
POST /api/chat             → Agentic RAG 채팅
GET  /api/keywords         → 키워드 구독 목록
POST /api/keywords         → 키워드 추가
DELETE /api/keywords/{kw}  → 키워드 삭제
GET  /api/schedule         → 스케줄 상태
POST /api/schedule         → 스케줄 설정
POST /api/notify/email     → 이메일 알림
POST /api/notify/github    → GitHub 업로드
POST /api/evaluate         → RAGAS 평가 실행
GET  /api/evaluate/results → 평가 결과 조회
POST /api/my-github        → 내 GitHub vs 트렌드 비교
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agentic_chat import run_agentic_chat
from compare import compare_reports
from evaluate import load_eval_results, run_evaluation
from graph import run_analysis
from my_github import analyze_my_github
from notifier import send_gmail, send_keyword_alert, upload_github_readme
from scheduler import get_status, scheduler, update_schedule
from storage import (
    add_keyword, check_keyword_matches, delete_keyword,
    get_keywords, load_all_history, load_history_stats, load_latest_history,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    print("[server] APScheduler 시작")
    yield
    scheduler.shutdown()
    print("[server] APScheduler 종료")


app = FastAPI(title="GitHub Trend Agentic RAG + Evaluation API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

class EvaluateRequest(BaseModel):
    n_questions: int = 20

class MyGithubRequest(BaseModel):
    username: str
    report:   dict


# ── 헬스체크 ─────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── 분석 ─────────────────────────────────────────────────────
@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    previous = load_latest_history()
    report   = run_analysis(language=req.language, period=req.period)

    prev_repos           = previous.get("repos", []) if previous else []
    report["comparison"] = compare_reports(report.get("repos", []), prev_repos)

    matched = check_keyword_matches(report.get("repos", []))
    if matched:
        send_keyword_alert(matched, req.language or "전체")
    report["keyword_matches"] = matched

    return report


# ── 히스토리 ─────────────────────────────────────────────────
@app.get("/api/history")
def history():
    return load_all_history()

@app.get("/api/history/latest")
def latest():
    return load_latest_history() or {}

@app.get("/api/history/stats")
def history_stats():
    return load_history_stats()


# ── Agentic RAG 채팅 ─────────────────────────────────────────
@app.post("/api/chat")
def chat(req: ChatRequest):
    return run_agentic_chat(req.message, req.report)


# ── 스케줄 ───────────────────────────────────────────────────
@app.get("/api/schedule")
def schedule_status():
    return get_status()

@app.post("/api/schedule")
def schedule_update(req: ScheduleRequest):
    update_schedule(
        enabled=req.enabled, hour=req.hour, minute=req.minute,
        language=req.language, period=req.period,
    )
    return get_status()


# ── 알림 ─────────────────────────────────────────────────────
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


# ── 평가 (Week 13) ────────────────────────────────────────────
@app.post("/api/evaluate")
def evaluate(req: EvaluateRequest):
    result = run_evaluation(n_questions=req.n_questions)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/api/evaluate/results")
def eval_results():
    data = load_eval_results()
    return data or {"message": "평가 결과가 없습니다. 먼저 평가를 실행해주세요."}


# ── 내 GitHub 분석 ────────────────────────────────────────────
@app.post("/api/my-github")
def my_github(req: MyGithubRequest):
    result = analyze_my_github(req.username, req.report)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
