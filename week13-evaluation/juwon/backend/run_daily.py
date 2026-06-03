"""
run_daily.py - GitHub Actions 일일 자동 실행 스크립트

컴퓨터가 꺼져있어도 GitHub 서버에서 매일 자동으로 실행됨.

실행: python run_daily.py
필요한 환경변수 (.env 또는 GitHub Secrets):
  OPENAI_API_KEY        - OpenAI API 키
  GITHUB_TOKEN          - GitHub 토큰
  GMAIL_USER            - Gmail 주소
  GMAIL_APP_PASSWORD    - Gmail 앱 비밀번호
  GITHUB_TREND_REPO     - 업로드할 레포 (예: username/trend-reports)
  MY_GITHUB_USERNAME    - 내 GitHub 유저네임 (선택)
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from compare import compare_reports
from graph import run_analysis
from my_github import analyze_my_github
from notifier import send_gmail, upload_github_readme
from storage import load_latest_history


def build_email_content(report: dict, my_analysis: dict | None) -> str:
    judge = report.get("judge_decision", "")

    my_section = ""
    if my_analysis and "error" not in my_analysis:
        langs = ", ".join(my_analysis.get("overlap_langs", [])[:5])
        my_section = f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧑‍💻 내 GitHub vs 트렌드 비교
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GitHub: @{my_analysis['username']}
내 레포: {my_analysis['my_repo_count']}개  |  트렌드 일치도: {my_analysis['match_pct']}%
겹치는 언어: {langs or '없음'}

{my_analysis['analysis']}
"""

    return judge + my_section


def run_daily():
    print("=" * 50)
    print("[daily] GitHub 트렌드 일일 분석 시작")
    print("=" * 50)

    # 1. 트렌드 분석
    print("\n[1/4] 트렌드 분석 중...")
    previous = load_latest_history()
    report   = run_analysis(language="", period="daily")
    prev_repos           = previous.get("repos", []) if previous else []
    report["comparison"] = compare_reports(report.get("repos", []), prev_repos)
    print(f"      완료 — 레포 {len(report.get('repos', []))}개 수집")

    # 2. 내 GitHub 분석
    my_username = os.getenv("MY_GITHUB_USERNAME", "").strip()
    my_analysis = None
    if my_username:
        print(f"\n[2/4] 내 GitHub 분석 중... (@{my_username})")
        my_analysis = analyze_my_github(my_username, report)
        if "error" in my_analysis:
            print(f"      경고: {my_analysis['error']}")
            my_analysis = None
        else:
            print(f"      완료 — 트렌드 일치도 {my_analysis['match_pct']}%")
    else:
        print("\n[2/4] MY_GITHUB_USERNAME 미설정 — 스킵")

    # 3. 이메일 발송
    print("\n[3/4] 이메일 발송 중...")
    content = build_email_content(report, my_analysis)
    ok = send_gmail(content, "전체", "daily")
    print(f"      {'✅ 완료' if ok else '❌ 실패 (.env 설정 확인)'}")

    # 4. GitHub 업로드
    print("\n[4/4] GitHub README 업로드 중...")
    ok = upload_github_readme(content, "전체", "daily")
    print(f"      {'✅ 완료' if ok else '❌ 실패 (.env 설정 확인)'}")

    print("\n" + "=" * 50)
    print("[daily] 완료!")
    print("=" * 50)


if __name__ == "__main__":
    run_daily()
