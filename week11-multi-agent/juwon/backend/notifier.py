"""
notifier.py - 분석 결과 외부 발송 모듈 (Week 11 Multi-Agent 버전)

1. send_gmail()            : Gmail SMTP로 HTML 이메일 발송
2. upload_github_readme()  : GitHub API로 TREND_REPORT.md 업로드/업데이트
"""

import base64
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from dotenv import load_dotenv

load_dotenv()


# ── Gmail ────────────────────────────────────────────────────
def send_gmail(content: str, language: str = "전체", period: str = "weekly") -> bool:
    gmail_user     = os.getenv("GMAIL_USER", "").strip()
    gmail_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()

    if not gmail_user or not gmail_password:
        print("[notify] 오류: .env에 GMAIL_USER / GMAIL_APP_PASSWORD 없음")
        return False

    subject  = f"[GitHub 트렌드] {datetime.now().strftime('%Y-%m-%d')} 분석 리포트 ({language} / {period})"
    body_html = _build_email_html(content, language, period)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = gmail_user
    msg["To"]      = gmail_user
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, gmail_user, msg.as_string())
        print(f"[notify] 메일 전송 완료 → {gmail_user}")
        return True
    except Exception as e:
        print(f"[notify] 메일 전송 실패: {e}")
        return False


def _build_email_html(content: str, language: str, period: str) -> str:
    date = datetime.now().strftime("%Y-%m-%d")
    return f"""
    <html><body style="font-family:sans-serif;max-width:700px;margin:auto">
    <h1 style="color:#0d1117;border-bottom:2px solid #58a6ff;padding-bottom:8px">
        📊 GitHub 트렌드 분석 리포트 — {date}
    </h1>
    <p style="color:#888">언어: <strong>{language}</strong> | 기간: <strong>{period}</strong></p>

    <h2>⚖️ Judge 최종 결정</h2>
    <div style="background:#f8f8f8;padding:12px;border-radius:6px;white-space:pre-wrap;font-size:14px">
{content}
    </div>

    <hr>
    <p style="color:#888;font-size:12px">GitHub Tech Trend Analyzer · Week 11 Multi-Agent Debate</p>
    </body></html>
    """


# ── GitHub README ─────────────────────────────────────────────
def upload_github_readme(content: str, language: str = "전체", period: str = "weekly") -> bool:
    token       = os.getenv("GITHUB_TOKEN", "").strip()
    target_repo = os.getenv("GITHUB_TREND_REPO", "").strip()

    if not token:
        print("[notify] 오류: .env에 GITHUB_TOKEN 없음")
        return False
    if not target_repo:
        print("[notify] 오류: .env에 GITHUB_TREND_REPO 없음")
        return False

    content_md = _build_readme_markdown(content, language, period)
    encoded    = base64.b64encode(content_md.encode("utf-8")).decode("utf-8")

    url     = f"https://api.github.com/repos/{target_repo}/contents/TREND_REPORT.md"
    headers = {
        "Authorization": f"token {token}",
        "Accept":        "application/vnd.github.v3+json",
    }

    get_resp = requests.get(url, headers=headers, timeout=10)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

    payload: dict = {
        "message": f"trend report {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": encoded,
    }
    if sha:
        payload["sha"] = sha

    put_resp = requests.put(url, headers=headers, json=payload, timeout=10)
    if put_resp.status_code in (200, 201):
        html_url = put_resp.json().get("content", {}).get("html_url", "")
        print(f"[notify] GitHub README 업로드 완료 → {html_url}")
        return True

    print(f"[notify] GitHub README 업로드 실패: {put_resp.status_code} — {put_resp.text[:120]}")
    return False


def _build_readme_markdown(content: str, language: str, period: str) -> str:
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""# 📊 GitHub 트렌드 분석 리포트

> 생성일시: {date}  |  언어: **{language}**  |  기간: **{period}**

## ⚖️ Judge 최종 결정

{content}

---
*GitHub Tech Trend Analyzer · Week 11 Multi-Agent Debate*
"""
