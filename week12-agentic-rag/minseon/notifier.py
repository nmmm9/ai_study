"""
notifier.py
───────────
Gmail SMTP 이메일 발송

.env에 다음 설정이 필요합니다:
  SMTP_USER     = your_gmail@gmail.com
  SMTP_PASSWORD = 앱_비밀번호_16자리   (구글 앱 비밀번호, 일반 비밀번호 아님)
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """HTML 이메일 발송. 성공하면 True 반환."""
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pw   = os.getenv("SMTP_PASSWORD", "")

    if not smtp_user or not smtp_pw:
        print("[notifier] SMTP_USER / SMTP_PASSWORD가 .env에 없습니다.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = smtp_user
    msg["To"]      = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(smtp_user, smtp_pw)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"[notifier] 이메일 발송 완료 → {to_email}")
        return True
    except Exception as e:
        print(f"[notifier] 발송 실패: {e}")
        return False


def build_email_html(
    name: str,
    age: int,
    region: str,
    recommendation: str,
) -> str:
    """정책 추천 이메일 HTML 본문 생성."""
    return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: 'Malgun Gothic', sans-serif; background:#f5f5f5; margin:0; padding:20px; }}
    .container {{ max-width:640px; margin:0 auto; background:#fff;
                  border-radius:8px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,.1); }}
    .header {{ background:#1a1a2e; color:#fff; padding:28px 32px; }}
    .header h1 {{ margin:0; font-size:22px; }}
    .header p  {{ margin:6px 0 0; font-size:13px; color:#aaa; }}
    .badge {{ display:inline-block; background:#e8f4fd; color:#1565c0;
              border-radius:4px; padding:3px 10px; font-size:12px; margin-top:10px; }}
    .body {{ padding:28px 32px; color:#333; line-height:1.7; }}
    .body h3 {{ color:#1a1a2e; border-left:4px solid #1565c0; padding-left:10px; }}
    .footer {{ background:#f0f0f0; padding:16px 32px; font-size:11px; color:#888; }}
    a {{ color:#1565c0; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>청년정책 맞춤 알림</h1>
      <p>AI가 {name}님의 조건에 맞는 정책을 골랐습니다</p>
      <span class="badge">나이: {age}세</span>
      <span class="badge" style="margin-left:6px;">지역: {region}</span>
    </div>
    <div class="body">
      {recommendation}
    </div>
    <div class="footer">
      이 메일은 청년정책 자동 알림 에이전트가 발송했습니다.
      수신 거부는 서비스 내 <b>구독 취소</b>를 이용하세요.
    </div>
  </div>
</body>
</html>
"""
