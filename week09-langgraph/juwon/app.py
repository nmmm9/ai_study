"""
app.py - GitHub Tech Trend Analyzer (Streamlit 대시보드)

실행: streamlit run app.py

기능:
- 언어/기간 필터링
- LangGraph 실행 (수집→검증→분석→비교→리포트)
- 트렌딩 레포 목록
- 언어 분포 차트
- AI 트렌드 분석 및 인사이트
- 이전 기록과 비교
- 분석 히스토리
"""

import os
import threading
from datetime import datetime

import streamlit as st
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from graph import run_analysis, get_graph_ascii, get_graph_mermaid
from storage import load_all_history, load_latest_history

load_dotenv()

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="GitHub Tech Trend Analyzer",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
    .repo-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 6px 0;
    }
    .repo-card a { color: #58a6ff; text-decoration: none; font-weight: bold; }
    .repo-card a:hover { text-decoration: underline; }
    .lang-tag {
        background: #21262d;
        color: #8b949e;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 12px;
        margin-right: 6px;
    }
    .insight-item {
        background: #0d1117;
        border-left: 3px solid #58a6ff;
        padding: 8px 14px;
        margin: 6px 0;
        border-radius: 4px;
        font-size: 14px;
    }
    .section-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .node-flow {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px;
        font-family: monospace;
        font-size: 13px;
        color: #58a6ff;
    }
</style>
""", unsafe_allow_html=True)

LANGUAGES = ["전체", "Python", "JavaScript", "TypeScript", "Rust", "Go",
             "Java", "C++", "Swift", "Kotlin", "C", "Ruby", "PHP"]
PERIODS   = {"오늘": "daily", "이번 주": "weekly", "이번 달": "monthly"}

# ── 스케줄러 ────────────────────────────────────────────────
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None


def start_scheduler(hour: int, minute: int, language: str, period: str):
    if st.session_state.scheduler:
        st.session_state.scheduler.shutdown(wait=False)

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: run_analysis(language=language, period=period),
        "cron", hour=hour, minute=minute,
    )
    scheduler.start()
    st.session_state.scheduler = scheduler


# ── 사이드바 ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 분석 설정")

    selected_lang   = st.selectbox("언어 필터", LANGUAGES)
    selected_period = st.selectbox("기간", list(PERIODS.keys()))

    st.divider()
    run_btn = st.button("🔍 분석 시작", type="primary", use_container_width=True)

    st.divider()
    st.markdown("### 📅 자동 실행")
    auto_run = st.toggle("매일 자동 분석 활성화")
    if auto_run:
        run_time = st.time_input(
            "실행 시간",
            value=datetime.strptime("09:00", "%H:%M").time(),
        )
        if st.button("스케줄 저장", use_container_width=True):
            lang   = "" if selected_lang == "전체" else selected_lang
            period = PERIODS[selected_period]
            start_scheduler(run_time.hour, run_time.minute, lang, period)
            st.success(f"매일 {run_time.strftime('%H:%M')} 자동 실행 설정됨")

    st.divider()
    st.markdown("### 📜 분석 기록")
    history = load_all_history()
    if history:
        for date in sorted(history.keys(), reverse=True)[:7]:
            st.markdown(f"- `{date}`")
    else:
        st.caption("기록 없음")


# ── 헤더 ────────────────────────────────────────────────────
st.markdown("# 📊 GitHub Tech Trend Analyzer")
st.markdown("*LangGraph로 구동되는 GitHub 기술 트렌드 분석 에이전트*")

# ── 그래프 시각화 ────────────────────────────────────────────
with st.expander("🔀 LangGraph 그래프 구조 시각화", expanded=False):
    tab_mermaid, tab_ascii = st.tabs(["Mermaid 다이어그램", "ASCII 아트"])

    with tab_mermaid:
        mermaid_code = get_graph_mermaid()
        st.code(mermaid_code, language="text")
        st.caption("위 코드를 https://mermaid.live 에 붙여넣으면 다이어그램으로 확인 가능")

    with tab_ascii:
        ascii_art = get_graph_ascii()
        st.code(ascii_art, language=None)
        st.caption("조건 분기: validate → retry 시 collect로 되돌아감")

st.divider()

# ── 분석 실행 ────────────────────────────────────────────────
if run_btn:
    lang   = "" if selected_lang == "전체" else selected_lang
    period = PERIODS[selected_period]

    with st.status("LangGraph 실행 중...", expanded=True) as status:
        st.write("📡 [collect]  GitHub API 데이터 수집 중...")
        st.write("✅ [validate] 데이터 검증 중...")
        st.write("🤖 [analyze]  AI 트렌드 분석 중...")
        st.write("📊 [compare]  이전 기록과 비교 중...")
        st.write("💾 [report]   리포트 저장 중...")

        report = run_analysis(language=lang, period=period)
        status.update(label="✅ 분석 완료!", state="complete")

    st.session_state["report"] = report


# ── 결과 표시 ────────────────────────────────────────────────
report = st.session_state.get("report") or load_latest_history()

if not report:
    st.info("👈 왼쪽 사이드바에서 **분석 시작** 버튼을 눌러주세요!")
    st.stop()

repos      = report.get("repos", [])
stats      = report.get("language_stats", {})
topics     = report.get("top_topics", {})
analysis   = report.get("analysis", "")
insights   = report.get("insights", [])
comparison = report.get("comparison", "")

# 메트릭
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("수집된 레포", f"{len(repos)}개")
with col2:
    top_lang = list(stats.keys())[0] if stats else "-"
    st.metric("1위 언어", top_lang)
with col3:
    total_stars = sum(r.get("stars", 0) for r in repos)
    st.metric("총 스타 수", f"{total_stars:,}")
with col4:
    period_label = {"daily": "오늘", "weekly": "이번 주", "monthly": "이번 달"}.get(
        report.get("period", "weekly"), "이번 주"
    )
    st.metric("분석 기간", period_label)

st.divider()

# 트렌딩 레포 + 차트
left, right = st.columns([1.6, 1])

with left:
    st.markdown("### 🔥 트렌딩 레포")
    for repo in repos[:12]:
        desc = repo.get("description", "")[:90]
        lang = repo.get("language", "Unknown")
        stars = repo.get("stars", 0)
        st.markdown(f"""
        <div class="repo-card">
            <a href="{repo['url']}" target="_blank">{repo['name']}</a>
            &nbsp;
            <span class="lang-tag">{lang}</span>
            ⭐ {stars:,}
            <br>
            <small style="color:#8b949e">{desc or "설명 없음"}</small>
        </div>
        """, unsafe_allow_html=True)

with right:
    st.markdown("### 📈 언어 분포")
    if stats:
        st.bar_chart(stats)

    st.markdown("### 🏷️ 인기 토픽")
    if topics:
        topic_str = "  ".join([
            f"`{t}` {c}" for t, c in list(topics.items())[:8]
        ])
        st.markdown(topic_str)

    st.markdown("### 💡 핵심 인사이트")
    for insight in insights:
        st.markdown(
            f'<div class="insight-item">· {insight}</div>',
            unsafe_allow_html=True,
        )

st.divider()

# AI 분석 + 비교
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### 🤖 AI 트렌드 분석")
    st.markdown(analysis)

with col_b:
    st.markdown("### 📊 이전 대비 변화")
    st.markdown(comparison)
