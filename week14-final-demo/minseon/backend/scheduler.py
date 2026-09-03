"""
scheduler.py — 자동 스케줄 작업

  [4시간마다] 정부 RSS 피드 수집 → 신규 항목 감지 → 매칭 사용자 이메일 발송
  08:00      공공API + 온통청년 수집 → ChromaDB 업데이트
  08:30      LH·HUG 주택 청약·임대 신규 공고 감지 → 알림 발송
  09:00      신규 정책 중 프로필 매칭 사용자에게 이메일 발송
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from supabase import create_client

from backend.config import settings
from backend.logging_config import get_logger
from backend.tools.rag_tool import execute_search_policies
from backend.tools.policy_updater import run_daily_update
from backend.tools.housing_fetcher import fetch_new_announcements
from backend.tools.realtime_fetcher import collect_rss_and_detect_new
from backend.notifier import send_email, build_policy_email, build_housing_email, build_realtime_email

logger = get_logger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

# 마지막 수집된 신규 정책 임시 보관 (8시 수집 → 9시 발송)
_latest_new_docs: list[dict] = []


def _admin_client():
    return create_client(settings.supabase_url, settings.supabase_service_key)


# ── 4시간마다: RSS 신규 정책 감지 + 이메일 ──────────────────────────

async def check_rss_and_notify():
    """4시간마다 — 정부 RSS 신규 항목 감지 → 매칭 사용자 이메일."""
    logger.info("[scheduler] RSS 신규 정책 감지 시작")
    try:
        new_docs = collect_rss_and_detect_new()
    except Exception as e:
        logger.error(f"[scheduler] RSS 수집 오류: {e}")
        return

    if not new_docs:
        return

    client   = _admin_client()
    res      = client.table("user_profiles").select("*").eq("notify", True).execute()
    profiles = res.data or []

    sent = 0
    for p in profiles:
        email  = p.get("email")
        region = p.get("region", "")
        age    = p.get("age", 0)
        if not email:
            continue

        # 지역·나이 관련 정책만 필터
        matched = []
        for d in new_docs:
            text = d.get("content", "")
            region_ok = (not region) or (region in text)
            if region_ok:
                matched.append(d)

        if not matched:
            matched = new_docs[:3]  # 관련 없어도 최신 3건은 전송

        ok = send_email(
            to=email,
            subject=f"[청년정책AI] 신규 정책 {len(matched)}건 — 실시간 업데이트",
            html=build_realtime_email(matched, region=region, age=age),
        )
        if ok:
            sent += 1

    logger.info(f"[scheduler] RSS 알림 발송: {sent}건")


# ── 8시: 정책 수집 ────────────────────────────────────────────────

async def fetch_and_update():
    """매일 오전 8시 — 최신 정책 수집 후 ChromaDB 업데이트."""
    global _latest_new_docs
    _latest_new_docs = await run_daily_update()
    logger.info(f"[scheduler] 수집 완료: 신규 {len(_latest_new_docs)}개")


# ── 9시: 이메일 발송 ──────────────────────────────────────────────

async def notify_matching_users():
    """매일 오전 9시 — 신규 정책 중 프로필 매칭 사용자에게 이메일 발송."""
    logger.info("[scheduler] 알림 발송 시작")
    client = _admin_client()

    res      = client.table("user_profiles").select("*").eq("notify", True).execute()
    profiles = res.data or []
    logger.info(f"[scheduler] 대상: {len(profiles)}명")

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

    logger.info(f"[scheduler] 발송 완료: {sent}건")


# ── 8시 30분: 주택 공고 신규 감지 및 알림 ─────────────────────────

async def check_and_notify_housing():
    """매일 오전 8시 30분 — LH·HUG 신규 주택 공고 감지 → 알림 이메일 발송."""
    logger.info("[scheduler] 주택 공고 신규 감지 시작")

    try:
        new_docs = fetch_new_announcements()
    except Exception as e:
        logger.error(f"[scheduler] 주택 공고 수집 오류: {e}")
        return

    if not new_docs:
        logger.warning("[scheduler] 신규 주택 공고 없음")
        return

    logger.info(f"[scheduler] 신규 주택 공고 {len(new_docs)}건 → 알림 발송")

    client = _admin_client()
    res = client.table("user_profiles").select("*").eq("notify", True).execute()
    profiles = res.data or []

    sent = 0
    for p in profiles:
        email = p.get("email")
        if not email:
            continue

        region = p.get("region", "")
        # 지역 필터링: 사용자 지역 또는 전국 공고
        matched = [
            d for d in new_docs
            if not region or not d.get("region") or region in d.get("region", "")
        ]
        if not matched:
            continue

        subject = f"[청년정책AI] LH·HUG 신규 주택 공고 {len(matched)}건"
        ok = send_email(to=email, subject=subject, html=build_housing_email(matched))
        if ok:
            sent += 1

    logger.info(f"[scheduler] 주택 공고 알림 발송 완료: {sent}건")


# ── D-Day 알림 (Feature 3) ───────────────────────────────────────

async def send_dday_reminders():
    """매일 오전 8시 45분 — 스크랩한 정책 D-3, D-1 마감 알림."""
    from backend.db.subscription_db import get_upcoming_deadlines_for_email
    items = get_upcoming_deadlines_for_email()
    if not items:
        return

    # 이메일별 그룹화
    by_email: dict = {}
    for item in items:
        email = item["user_email"]
        by_email.setdefault(email, []).append(item)

    for email, deadlines in by_email.items():
        rows_html = "".join(
            f"<tr><td>{d['policy_name']}</td><td>{d['deadline']}</td>"
            f"<td><b>{d.get('dday','')}</b></td><td>{d.get('status','')}</td></tr>"
            for d in deadlines
        )
        html = f"""
        <h2>⏰ 마감 임박 정책 알림</h2>
        <p>스크랩하신 정책의 신청 마감이 임박했습니다.</p>
        <table border="1" cellpadding="6" style="border-collapse:collapse">
          <tr><th>정책명</th><th>마감일</th><th>D-Day</th><th>상태</th></tr>
          {rows_html}
        </table>
        <p>지금 바로 신청하세요!</p>
        """
        send_email(
            to=email,
            subject=f"[청년정책AI] 마감 임박 알림 — {len(deadlines)}건",
            html=html,
        )
    logger.info(f"[scheduler] D-Day 알림 발송: {len(by_email)}명")


# ── 키워드 구독 알림 (Feature 1) ─────────────────────────────────

async def check_keyword_subscriptions():
    """4시간마다 — 신규 RSS 정책이 구독 키워드와 매칭되면 알림."""
    from backend.db.subscription_db import match_subscriptions
    try:
        new_docs = collect_rss_and_detect_new()
    except Exception as e:
        logger.error(f"[scheduler] RSS 키워드구독 오류: {e}")
        return

    for doc in new_docs:
        text   = doc.get("title", "") + " " + doc.get("content", "")
        emails = match_subscriptions(text)
        for email in emails:
            send_email(
                to=email,
                subject=f"[청년정책AI] 구독 키워드 매칭 — {doc['title'][:30]}",
                html=build_realtime_email([doc]),
            )
    logger.info(f"[scheduler] 키워드 구독 알림 처리: {len(new_docs)}건")


# ── 스케줄러 초기화 ───────────────────────────────────────────────

def init_scheduler() -> AsyncIOScheduler:
    # 4시간마다: RSS 신규 정책 감지 + 키워드 구독 매칭
    scheduler.add_job(check_rss_and_notify,        "cron", hour="0,4,8,12,16,20", minute=0)
    scheduler.add_job(check_keyword_subscriptions, "cron", hour="0,4,8,12,16,20", minute=10)
    # 매일 08:00: 공공 API + 온통청년 수집 → ChromaDB
    scheduler.add_job(fetch_and_update,            "cron", hour=8,  minute=0)
    # 매일 08:30: LH·HUG 주택 공고 감지
    scheduler.add_job(check_and_notify_housing,    "cron", hour=8,  minute=30)
    # 매일 08:45: D-Day 마감 임박 알림
    scheduler.add_job(send_dday_reminders,         "cron", hour=8,  minute=45)
    # 매일 09:00: 프로필 맞춤 이메일
    scheduler.add_job(notify_matching_users,       "cron", hour=9,  minute=0)
    return scheduler
