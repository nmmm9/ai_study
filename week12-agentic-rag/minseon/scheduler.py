"""
scheduler.py
────────────
APScheduler — 매일 오전 9시 이메일 허용 사용자에게 자동 알림
(week10 scheduler → week12 Agentic RAG 버전)

직접 실행 시 즉시 1회 테스트:
    python scheduler.py
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from apscheduler.schedulers.background import BackgroundScheduler

import user_db
import graph as agent_graph


def run_all_notifications() -> None:
    """이메일 허용 사용자 전체에게 Agentic RAG 기반 맞춤 정책 알림 발송."""
    users = user_db.get_email_allowed_users()
    print(f"\n[scheduler] 시작 — {len(users)}명 ({datetime.now():%Y-%m-%d %H:%M})")

    for u in users:
        if not user_db.should_notify(u):
            print(f"  → {u['email']} : 발송 시간 아님 (건너뜀)")
            continue

        print(f"  → {u['email']} ({u['name']}, {u['age']}세, {u['region']}) : Agentic RAG 실행…")
        try:
            agent_graph.run_notify(
                name=u["name"],
                email=u["email"],
                age=u["age"],
                region=u["region"],
                send_notification=True,
            )
        except Exception as e:
            print(f"  → {u['email']} : 오류 — {e}")

    print("[scheduler] 완료\n")


_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    """싱글톤 BackgroundScheduler (Streamlit @cache_resource 용)."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="Asia/Seoul")
        _scheduler.add_job(
            run_all_notifications,
            trigger="cron",
            hour=9,
            minute=0,
            id="daily_policy_notify",
            replace_existing=True,
        )
        _scheduler.start()
        print("[scheduler] 시작 — 매일 09:00 Agentic RAG 자동 알림")
    return _scheduler


if __name__ == "__main__":
    run_all_notifications()
