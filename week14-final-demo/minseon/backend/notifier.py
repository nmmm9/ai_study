"""
notifier.py — Gmail SMTP 이메일 발송 (무료)

.env 필요:
  GMAIL_USER=본인@gmail.com
  GMAIL_PASS=앱비밀번호16자리
"""

import smtplib
import ssl
import os


def send_email(to: str, subject: str, html: str) -> bool:
    gmail_user = os.environ.get("SMTP_USER", "") or os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("SMTP_PASSWORD", "") or os.environ.get("GMAIL_PASS", "")
    if not gmail_user or not gmail_pass:
        print("[notifier] SMTP_USER / SMTP_PASSWORD 설정 없음")
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

        print(f"[notifier] 발송 완료 → {to}")
        return True

    except Exception as e:
        print(f"[notifier] 발송 실패 {to}: {e}")
        return False


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
