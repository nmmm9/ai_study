"""
main.py - FastAPI 서버

실행: uvicorn main:app --reload --port 8000

엔드포인트:
GET  /api/health          → 서버 상태 확인
POST /api/analyze         → 분석 시작
GET  /api/history         → 이전 분석 기록
GET  /api/schedule        → 자동 분석 스케줄 상태 조회
POST /api/schedule        → 자동 분석 스케줄 설정
POST /api/notify/email    → 메일 전송
POST /api/notify/github   → GitHub 업로드
POST /api/chat            → 분석 결과 기반 채팅
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from compare import compare_reports
from graph import llm, run_analysis
from notifier import send_gmail, upload_github_readme
from scheduler import get_status, scheduler, update_schedule
from storage import load_all_history, load_latest_history


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    print("[server] APScheduler 시작")
    yield
    scheduler.shutdown()
    print("[server] APScheduler 종료")


app = FastAPI(title="GitHub Trend Multi-Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    previous = load_latest_history()
    report   = run_analysis(language=req.language, period=req.period)

    prev_repos = previous.get("repos", []) if previous else []
    report["comparison"] = compare_reports(report.get("repos", []), prev_repos)

    return report


@app.get("/api/history")
def history():
    return load_all_history()


@app.get("/api/history/latest")
def latest():
    data = load_latest_history()
    return data or {}


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


@app.post("/api/chat")
def chat(req: ChatRequest):
    report = req.report
    repos  = report.get("repos", [])[:10]
    repo_summary = "\n".join([
        f"- {r['name']} (⭐{r.get('stars',0):,} / 트렌드점수:{r.get('trend_score',0)}): {r.get('description','')[:60]}"
        for r in repos
    ])

    context = f"""아래는 최신 GitHub 트렌드 분석 결과야.

[트렌딩 레포 TOP 10]
{repo_summary}

[AI/ML 전문가 분석]
{report.get('analysis_ai', '')}

[웹/앱 전문가 분석]
{report.get('analysis_web', '')}

[보안 전문가 분석]
{report.get('analysis_sec', '')}

[Judge 최종 결론]
{report.get('judge_decision', '')}
"""

    response = llm.invoke(f"""{context}

위 분석 결과를 바탕으로 아래 질문에 한국어로 답해줘.
질문: {req.message}
""")
    return {"reply": response.content}


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
