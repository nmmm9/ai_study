"""
scheduler.py - 자동 분석 스케줄러

APScheduler를 사용해서 정해진 시간에 자동으로 분석 실행 + 메일 발송
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from compare import compare_reports
from graph import run_analysis
from notifier import send_gmail
from storage import load_latest_history, save_history

scheduler = BackgroundScheduler(timezone="Asia/Seoul")

_schedule_config = {
    "enabled": False,
    "hour":    9,
    "minute":  0,
    "language": "",
    "period":   "daily",
}


def _run_scheduled_analysis():
    print(f"[scheduler] 자동 분석 시작 (언어: {_schedule_config['language'] or '전체'}, 기간: {_schedule_config['period']})")

    previous = load_latest_history()
    report   = run_analysis(
        language=_schedule_config["language"],
        period=_schedule_config["period"],
    )

    prev_repos = previous.get("repos", []) if previous else []
    report["comparison"] = compare_reports(report.get("repos", []), prev_repos)
    save_history(report)

    content  = report.get("judge_decision", "") or report.get("supervisor_report", "")
    language = _schedule_config["language"] or "전체"
    send_gmail(content, language, _schedule_config["period"])

    print("[scheduler] 자동 분석 완료 + 메일 발송")


def get_status() -> dict:
    job = scheduler.get_job("auto_analysis")
    next_run = str(job.next_run_time) if job and job.next_run_time else None
    return {
        "enabled":  _schedule_config["enabled"],
        "hour":     _schedule_config["hour"],
        "minute":   _schedule_config["minute"],
        "language": _schedule_config["language"],
        "period":   _schedule_config["period"],
        "next_run": next_run,
    }


def update_schedule(enabled: bool, hour: int, minute: int, language: str, period: str):
    _schedule_config.update({
        "enabled":  enabled,
        "hour":     hour,
        "minute":   minute,
        "language": language,
        "period":   period,
    })

    scheduler.remove_job("auto_analysis") if scheduler.get_job("auto_analysis") else None

    if enabled:
        scheduler.add_job(
            _run_scheduled_analysis,
            trigger=CronTrigger(hour=hour, minute=minute, timezone="Asia/Seoul"),
            id="auto_analysis",
            replace_existing=True,
        )
        print(f"[scheduler] 스케줄 등록: 매일 {hour:02d}:{minute:02d}")
    else:
        print("[scheduler] 스케줄 해제")
