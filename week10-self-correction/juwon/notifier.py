"""
notifier.py - 분석 결과 외부 발송 모듈

1. send_gmail()       : Gmail SMTP로 HTML 이메일 발송
2. upload_github_readme(): GitHub API로 TREND_REPORT.md 업로드/업데이트
"""

import base64
import json
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from dotenv import load_dotenv

load_dotenv()


# ── Gmail ────────────────────────────────────────────────────
def send_gmail(report: dict, to_email: str = "") -> str:
    """
    Gmail App Password를 이용한 SMTP 발송.

    .env 필요:
        GMAIL_USER=yoonjuwon0618@gmail.com
        GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx  (Google 앱 비밀번호)
    """
    gmail_user     = os.getenv("GMAIL_USER", "").strip()
    gmail_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()

    if not gmail_user or not gmail_password:
        return "error: .env에 GMAIL_USER / GMAIL_APP_PASSWORD 없음"

    recipient = to_email or gmail_user
    subject   = f"[GitHub 트렌드] {datetime.now().strftime('%Y-%m-%d')} 분석 리포트"
    body_html = _build_email_html(report)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = gmail_user
    msg["To"]      = recipient
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, recipient, msg.as_string())
        return f"success: {recipient}로 발송 완료"
    except Exception as e:
        return f"error: {e}"


def _build_email_html(report: dict) -> str:
    repos    = report.get("repos", [])[:10]
    stats    = report.get("language_stats", {})
    insights = report.get("insights", [])
    analysis = report.get("analysis", "")
    score    = report.get("quality_score", "-")
    date     = datetime.now().strftime("%Y-%m-%d")

    repo_rows = "".join([
        f"<tr><td><a href='{r['url']}'>{r['name']}</a></td>"
        f"<td>{r.get('language','?')}</td>"
        f"<td>⭐ {r.get('stars',0):,}</td></tr>"
        for r in repos
    ])

    insight_items = "".join([f"<li>{i}</li>" for i in insights])
    lang_items    = "".join([f"<li>{k}: {v}개</li>" for k, v in list(stats.items())[:5]])

    return f"""
    <html><body style="font-family:sans-serif;max-width:700px;margin:auto">
    <h1 style="color:#0d1117;border-bottom:2px solid #58a6ff;padding-bottom:8px">
        📊 GitHub 트렌드 분석 리포트 — {date}
    </h1>
    <p style="color:#888">AI 품질 점수: <strong>{score}/100</strong></p>

    <h2>🔥 트렌딩 레포 TOP 10</h2>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
      <tr style="background:#f0f0f0"><th>레포</th><th>언어</th><th>스타</th></tr>
      {repo_rows}
    </table>

    <h2>📈 언어 분포</h2><ul>{lang_items}</ul>

    <h2>💡 핵심 인사이트</h2><ul>{insight_items}</ul>

    <h2>🤖 AI 분석</h2>
    <div style="background:#f8f8f8;padding:12px;border-radius:6px;white-space:pre-wrap">{analysis}</div>

    <hr>
    <p style="color:#888;font-size:12px">GitHub Tech Trend Analyzer · Week 10 Self-Correction</p>
    </body></html>
    """


# ── GitHub README ─────────────────────────────────────────────
def upload_github_readme(report: dict, repo: str = "") -> str:
    """
    GitHub API로 TREND_REPORT.md 생성/업데이트.

    .env 필요:
        GITHUB_TOKEN=ghp_...
        GITHUB_TREND_REPO=owner/repo-name  (예: juwon/trend-reports)
    """
    token      = os.getenv("GITHUB_TOKEN", "").strip()
    target_repo = repo or os.getenv("GITHUB_TREND_REPO", "").strip()

    if not token:
        return "error: .env에 GITHUB_TOKEN 없음"
    if not target_repo:
        return "error: .env에 GITHUB_TREND_REPO 없음 (예: juwon/trend-reports)"

    content_md = _build_readme_markdown(report)
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
        return f"success: {html_url}"
    return f"error: {put_resp.status_code} — {put_resp.text[:120]}"


def _build_readme_markdown(report: dict) -> str:
    date     = datetime.now().strftime("%Y-%m-%d %H:%M")
    repos    = report.get("repos", [])[:10]
    stats    = report.get("language_stats", {})
    insights = report.get("insights", [])
    analysis = report.get("analysis", "")
    score    = report.get("quality_score", "-")
    history  = report.get("reflect_history", [])

    repo_lines = "\n".join([
        f"| [{r['name']}]({r['url']}) | {r.get('language','?')} | ⭐ {r.get('stars',0):,} |"
        for r in repos
    ])
    lang_lines    = "\n".join([f"- {k}: {v}개" for k, v in list(stats.items())[:5]])
    insight_lines = "\n".join([f"- {i}" for i in insights])
    history_lines = "\n".join([
        f"- 시도 {h['attempt']}: {h['score']}점 — {h['feedback'][:60]}"
        for h in history
    ]) or "- 기록 없음"

    return f"""# 📊 GitHub 트렌드 분석 리포트

> 생성일시: {date}  |  AI 품질 점수: **{score}/100**

## 🔥 트렌딩 레포 TOP 10

| 레포 | 언어 | 스타 |
|------|------|------|
{repo_lines}

## 📈 언어 분포

{lang_lines}

## 💡 핵심 인사이트

{insight_lines}

## 🤖 AI 분석

{analysis}

## 🔄 Self-Correction 이력

{history_lines}

---
*GitHub Tech Trend Analyzer · Week 10 Self-Correction*
"""
