"""
scheduler.py — 자동 스케줄 작업

  08:00 — 공공API + 온통청년에서 최신 정책 수집 → ChromaDB 업데이트
  09:00 — 신규 정책 중 프로필 매칭 사용자에게 이메일 발송
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from supabase import create_client

from backend.tools.rag_tool import execute_search_policies
from backend.tools.policy_updater import run_daily_update
from backend.notifier import send_email, build_policy_email

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

# 마지막 수집된 신규 정책 임시 보관 (8시 수집 → 9시 발송)
_latest_new_docs: list[dict] = []


def _admin_client():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY", "")
    return create_client(url, key)


# ── 8시: 정책 수집 ────────────────────────────────────────────────

async def fetch_and_update():
    """매일 오전 8시 — 최신 정책 수집 후 ChromaDB 업데이트."""
    global _latest_new_docs
    _latest_new_docs = await run_daily_update()
    print(f"[scheduler] 수집 완료: 신규 {len(_latest_new_docs)}개")


# ── 9시: 이메일 발송 ──────────────────────────────────────────────

async def notify_matching_users():
    """매일 오전 9시 — 신규 정책 중 프로필 매칭 사용자에게 이메일 발송."""
    print("[scheduler] 알림 발송 시작")
    client = _admin_client()

    res      = client.table("user_profiles").select("*").eq("notify", True).execute()
    profiles = res.data or []
    print(f"[scheduler] 대상: {len(profiles)}명")

    sent = 0
    for p in profiles:
        email = p.get("email")
        if not email:
            continue

        # 신규 정책이 있으면 신규 정책 중에서, 없으면 전체 검색
        if _latest_new_docs:
            # 신규 정책을 사용자 프로필로 필터링
            age    = p.get("age")
            region = p.get("region", "")
            docs   = [
                d for d in _latest_new_docs
                if (not region or region in d.get("content", ""))
            ][:3]
        else:
            # 신규 정책 없으면 기존 벡터 검색으로 맞춤 추천
            parts = []
            if p.get("age"):    parts.append(f"만 {p['age']}세")
            if p.get("region"): parts.append(p["region"])
            query = " ".join(parts) + " 청년 지원 정책"
            docs  = execute_search_policies(query=query, top_k=3)

        if not docs:
            continue

        subject = (
            f"[청년정책AI] 신규 정책 {len(docs)}건 — 오늘의 맞춤 추천"
            if _latest_new_docs else
            f"[청년정책AI] 맞춤 정책 {len(docs)}건 도착"
        )

        ok = send_email(to=email, subject=subject, html=build_policy_email(docs))
        if ok:
            sent += 1

    print(f"[scheduler] 발송 완료: {sent}건")


# ── 스케줄러 초기화 ───────────────────────────────────────────────

def init_scheduler() -> AsyncIOScheduler:
    scheduler.add_job(fetch_and_update,      "cron", hour=8,  minute=0)
    scheduler.add_job(notify_matching_users, "cron", hour=9,  minute=0)
    return scheduler
