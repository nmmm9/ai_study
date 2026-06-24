"""
scheduler.py — 매일 오전 9시 맞춤 정책 이메일 발송

Supabase user_profiles 테이블에서 notify=true인 사용자를 조회해
프로필(나이/지역)에 맞는 정책을 찾아 이메일로 발송합니다.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from supabase import create_client

from backend.tools.rag_tool import execute_search_policies
from backend.notifier import send_email, build_policy_email

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


def _admin_client():
    """SUPABASE_SERVICE_KEY로 RLS 우회 — 없으면 anon key 사용."""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY", "")
    return create_client(url, key)


async def notify_matching_users():
    """프로필 있는 모든 사용자에게 맞춤 정책 이메일 발송."""
    print("[scheduler] 알림 발송 시작")
    client = _admin_client()

    res = client.table("user_profiles").select("*").eq("notify", True).execute()
    profiles = res.data or []
    print(f"[scheduler] 대상: {len(profiles)}명")

    sent = 0
    for p in profiles:
        email = p.get("email")
        if not email:
            continue

        # 프로필 → 검색 쿼리
        parts = []
        if p.get("age"):    parts.append(f"만 {p['age']}세")
        if p.get("region"): parts.append(p["region"])
        query = " ".join(parts) + " 청년 지원 정책"

        docs = execute_search_policies(query=query, top_k=3)
        if not docs:
            continue

        ok = send_email(
            to=email,
            subject=f"[청년정책AI] 맞춤 정책 {len(docs)}건 도착",
            html=build_policy_email(docs),
        )
        if ok:
            sent += 1

    print(f"[scheduler] 완료: {sent}건 발송")


def init_scheduler() -> AsyncIOScheduler:
    scheduler.add_job(notify_matching_users, "cron", hour=9, minute=0)
    return scheduler
