"""
notifier.py — Gmail SMTP 이메일 발송 (무료)

.env 필요:
  GMAIL_USER=본인@gmail.com
  GMAIL_PASS=앱비밀번호16자리
"""

import smtplib
import ssl
from datetime import datetime

from backend.config import settings
from backend.logging_config import get_logger

logger = get_logger(__name__)


def send_email(to: str, subject: str, html: str) -> bool:
    gmail_user = settings.smtp_user
    gmail_pass = settings.smtp_password
    if not gmail_user or not gmail_pass:
        logger.warning("[notifier] SMTP_USER / SMTP_PASSWORD 설정 없음")
        return False

    try:
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = gmail_user
        msg["To"]      = to
        msg.attach(MIMEText(html, "html", "utf-8"))

        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
            s.login(gmail_user, gmail_pass)
            s.sendmail(gmail_user, to, msg.as_string())

        logger.info(f"[notifier] 발송 완료 → {to}")
        return True

    except Exception as e:
        logger.error(f"[notifier] 발송 실패 {to}: {e}")
        return False


def build_realtime_email(policies: list, region: str = "", age: int = 0) -> str:
    """정부 RSS 신규 정책 알림 이메일."""
    profile_desc = ""
    if region or age:
        parts = []
        if region: parts.append(region)
        if age:    parts.append(f"만 {age}세")
        profile_desc = f"<p style='font-size:13px;color:#666;margin:0 0 16px;'>맞춤 조건: {' · '.join(parts)}</p>"

    items = ""
    for p in policies:
        source   = p.get("source", "")
        pub_date = p.get("pub_date", "")
        url      = p.get("url", "#")
        category = p.get("category", "")
        layer    = p.get("layer", "rss")
        badge_color = "#2563eb" if layer == "rss" else "#7c3aed"
        badge_label = "정부 RSS" if layer == "rss" else "실시간검색"

        items += f"""
        <div style="margin:10px 0;padding:14px 16px;background:#f9fafb;
                    border-radius:8px;border-left:4px solid {badge_color};">
          <div style="display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap;">
            <span style="background:{badge_color};color:#fff;font-size:10px;
                         padding:2px 7px;border-radius:4px;">{badge_label}</span>
            <span style="background:#e5e7eb;color:#374151;font-size:10px;
                         padding:2px 7px;border-radius:4px;">{category}</span>
            {f'<span style="color:#9ca3af;font-size:10px;padding:2px 4px;">{source}</span>' if source else ''}
            {f'<span style="color:#9ca3af;font-size:10px;padding:2px 4px;">{pub_date}</span>' if pub_date else ''}
          </div>
          <h3 style="margin:0 0 6px;font-size:14px;color:#111827;line-height:1.4;">
            {p['title']}
          </h3>
          <p style="margin:0 0 8px;font-size:12px;color:#6b7280;line-height:1.5;">
            {p['content'][:200].split(chr(10))[0]}...
          </p>
          <a href="{url}" style="font-size:12px;color:{badge_color};text-decoration:none;">
            원문 보기 →
          </a>
        </div>
        """

    now_str = datetime.now().strftime("%Y년 %m월 %d일 %H시")
    return f"""
    <div style="font-family:'Apple SD Gothic Neo',sans-serif;
                max-width:600px;margin:0 auto;color:#111827;">
      <div style="background:#111827;padding:24px;border-radius:12px 12px 0 0;">
        <h1 style="color:#fff;margin:0;font-size:20px;">청년정책 AI</h1>
        <p style="color:#9ca3af;margin:4px 0 0;font-size:12px;">
          📡 실시간 정책 업데이트 — {now_str}
        </p>
      </div>
      <div style="padding:20px 24px;border:1px solid #e5e7eb;
                  border-top:none;border-radius:0 0 12px 12px;">
        <p style="font-size:14px;margin:0 0 6px;">신규 청년 정책이 업데이트됐습니다.</p>
        {profile_desc}
        {items}
        <div style="margin-top:20px;text-align:center;">
          <a href="http://localhost:3000"
             style="background:#2563eb;color:#fff;padding:10px 24px;
                    border-radius:8px;text-decoration:none;font-size:13px;">
            챗봇에서 자세히 확인하기
          </a>
        </div>
        <p style="margin-top:14px;font-size:10px;color:#9ca3af;text-align:center;">
          챗봇 → 내 정보 → 알림 해제로 수신 거부 가능
        </p>
      </div>
    </div>
    """


def build_housing_email(announcements: list) -> str:
    """LH·HUG 신규 주택 공고 이메일 템플릿."""
    items = ""
    for a in announcements:
        source_color = "#1b63d5" if "LH" in a.get("source", "") else "#e85b2a"
        badge = a.get("type", "")
        period = a.get("period", "")
        url = a.get("url", "#")
        items += f"""
        <div style="margin:12px 0;padding:16px;background:#f4f8ff;
                    border-radius:8px;border-left:4px solid {source_color};">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
            <span style="background:{source_color};color:#fff;font-size:11px;
                         padding:2px 8px;border-radius:4px;">{a.get('source','')}</span>
            <span style="background:#eee;color:#555;font-size:11px;
                         padding:2px 8px;border-radius:4px;">{badge}</span>
          </div>
          <h3 style="margin:0 0 4px;font-size:15px;color:#1a1a1a;">{a['title']}</h3>
          <p style="margin:0 0 6px;font-size:13px;color:#555;">
            {"📅 " + period if period else ""}
          </p>
          <a href="{url}" style="font-size:12px;color:{source_color};text-decoration:none;">
            공고 바로보기 →
          </a>
        </div>
        """

    return f"""
    <div style="font-family:'Apple SD Gothic Neo',sans-serif;
                max-width:600px;margin:0 auto;color:#1a1a1a;">
      <div style="background:#1a1a1a;padding:24px;border-radius:12px 12px 0 0;">
        <h1 style="color:#fff;margin:0;font-size:20px;">청년정책 AI</h1>
        <p style="color:#aaa;margin:4px 0 0;font-size:13px;">🏠 LH·HUG 신규 주택 공고 알림</p>
      </div>
      <div style="padding:24px;border:1px solid #eee;
                  border-top:none;border-radius:0 0 12px 12px;">
        <p style="font-size:15px;margin:0 0 4px;">신규 주택 청약·임대 공고가 올라왔습니다.</p>
        <p style="font-size:13px;color:#888;margin:0 0 20px;">
          총 <strong>{len(announcements)}건</strong>의 새 공고
        </p>
        {items}
        <div style="margin-top:24px;text-align:center;">
          <a href="http://localhost:3000"
             style="background:#1b63d5;color:#fff;padding:10px 24px;
                    border-radius:8px;text-decoration:none;font-size:14px;">
            챗봇에서 자세히 보기
          </a>
        </div>
        <p style="margin-top:16px;font-size:11px;color:#aaa;text-align:center;">
          알림을 끄려면 챗봇 → 내 정보 → 알림 해제
        </p>
      </div>
    </div>
    """


def build_policy_email(policies: list) -> str:
    items = ""
    for p in policies:
        items += f"""
        <div style="margin:12px 0;padding:16px;background:#f8f8f8;
                    border-radius:8px;border-left:4px solid #4a7cff;">
          <h3 style="margin:0 0 6px;font-size:15px;color:#1a1a1a;">{p['title']}</h3>
          <p style="margin:0;font-size:13px;color:#555;line-height:1.6;">
            {p['content'][:250]}...
          </p>
          <span style="font-size:11px;color:#888;">#{p.get('category','')}</span>
        </div>
        """

    return f"""
    <div style="font-family:'Apple SD Gothic Neo',sans-serif;
                max-width:600px;margin:0 auto;color:#1a1a1a;">
      <div style="background:#1a1a1a;padding:24px;border-radius:12px 12px 0 0;">
        <h1 style="color:#fff;margin:0;font-size:20px;">청년정책 AI</h1>
        <p style="color:#aaa;margin:4px 0 0;font-size:13px;">맞춤 정책 알림</p>
      </div>
      <div style="padding:24px;border:1px solid #eee;
                  border-top:none;border-radius:0 0 12px 12px;">
        <p style="font-size:15px;margin:0 0 16px;">
          오늘의 맞춤 청년정책을 알려드립니다.
        </p>
        {items}
        <div style="margin-top:24px;text-align:center;">
          <a href="http://localhost:3000"
             style="background:#4a7cff;color:#fff;padding:10px 24px;
                    border-radius:8px;text-decoration:none;font-size:14px;">
            챗봇에서 자세히 보기
          </a>
        </div>
        <p style="margin-top:16px;font-size:11px;color:#aaa;text-align:center;">
          알림을 끄려면 챗봇 → 내 정보 → 알림 해제
        </p>
      </div>
    </div>
    """
