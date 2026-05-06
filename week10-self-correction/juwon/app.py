"""
app.py - GitHub Tech Trend Analyzer v2 (Self-Correction 버전)

실행: streamlit run app.py

추가된 기능:
- 품질 점수 게이지 (reflect 결과)
- Self-Correction 이력 타임라인
- Gmail 발송 상태
- GitHub README 업로드 상태
"""

import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from graph import run_analysis, get_graph_ascii, get_graph_mermaid
from storage import load_all_history, load_latest_history

load_dotenv()

st.set_page_config(
    page_title="GitHub Trend Analyzer v2",
    page_icon="🔄",
    layout="wide",
)

st.markdown("""
<style>
    .repo-card {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 8px; padding: 12px 16px; margin: 6px 0;
    }
    .repo-card a { color: #58a6ff; text-decoration: none; font-weight: bold; }
    .repo-card a:hover { text-decoration: underline; }
    .lang-tag {
        background: #21262d; color: #8b949e;
        border-radius: 12px; padding: 2px 10px;
        font-size: 12px; margin-right: 6px;
    }
    .insight-item {
        background: #0d1117; border-left: 3px solid #58a6ff;
        padding: 8px 14px; margin: 6px 0;
        border-radius: 4px; font-size: 14px;
    }
    .reflect-pass {
        background: #0d2a0d; border-left: 3px solid #3fb950;
        padding: 8px 14px; margin: 4px 0; border-radius: 4px;
    }
    .reflect-fail {
        background: #2a0d0d; border-left: 3px solid #f85149;
        padding: 8px 14px; margin: 4px 0; border-radius: 4px;
    }
    .notify-badge {
        display: inline-block; padding: 3px 10px;
        border-radius: 12px; font-size: 12px; margin: 3px;
    }
</style>
""", unsafe_allow_html=True)

LANGUAGES = ["전체", "Python", "JavaScript", "TypeScript", "Rust", "Go",
             "Java", "C++", "Swift", "Kotlin", "C", "Ruby", "PHP"]
PERIODS   = {"오늘": "daily", "이번 주": "weekly", "이번 달": "monthly"}

# ── 사이드바 ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 분석 설정")

    selected_lang   = st.selectbox("언어 필터", LANGUAGES)
    selected_period = st.selectbox("기간", list(PERIODS.keys()))

    st.divider()
    run_btn = st.button("🔍 분석 시작", type="primary", use_container_width=True)

    st.divider()
    st.markdown("### 📬 알림 설정")
    st.caption(".env 파일에 아래 항목을 추가하세요")
    st.code("""GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
GITHUB_TREND_REPO=owner/repo-name""", language="bash")

    st.divider()
    st.markdown("### 📜 분석 기록")
    history = load_all_history()
    if history:
        for date in sorted(history.keys(), reverse=True)[:7]:
            score = history[date].get("quality_score", "-")
            st.markdown(f"- `{date}` — 점수: **{score}**")
    else:
        st.caption("기록 없음")


# ── 헤더 ────────────────────────────────────────────────────
st.markdown("# 🔄 GitHub Tech Trend Analyzer v2")
st.markdown("*Self-Correction이 적용된 GitHub 기술 트렌드 분석 에이전트*")

# ── 그래프 시각화 ────────────────────────────────────────────
with st.expander("🔀 LangGraph 그래프 구조", expanded=False):
    tab_mermaid, tab_ascii = st.tabs(["Mermaid 다이어그램", "ASCII 아트"])
    with tab_mermaid:
        st.code(get_graph_mermaid(), language="text")
        st.caption("위 코드를 https://mermaid.live 에 붙여넣으면 다이어그램으로 확인 가능")
    with tab_ascii:
        st.code(get_graph_ascii(), language=None)

st.divider()

# ── 분석 실행 ────────────────────────────────────────────────
if run_btn:
    lang   = "" if selected_lang == "전체" else selected_lang
    period = PERIODS[selected_period]

    with st.status("LangGraph 실행 중...", expanded=True) as status:
        st.write("📡 [collect]   GitHub API 데이터 수집 중...")
        st.write("✅ [validate]  데이터 검증 중...")
        st.write("🤖 [generate]  AI 트렌드 분석 생성 중...")
        st.write("🔍 [reflect]   품질 자동 검토 중...")
        st.write("📊 [compare]   이전 기록과 비교 중...")
        st.write("📬 [notify]    Gmail 발송 + README 업로드 중...")
        st.write("💾 [report]    리포트 저장 중...")

        report = run_analysis(language=lang, period=period)
        status.update(label="✅ 분석 완료!", state="complete")

    st.session_state["report"] = report


# ── 결과 표시 ────────────────────────────────────────────────
report = st.session_state.get("report") or load_latest_history()

if not report:
    st.info("👈 왼쪽 사이드바에서 **분석 시작** 버튼을 눌러주세요!")
    st.stop()

repos           = report.get("repos", [])
stats           = report.get("language_stats", {})
topics          = report.get("top_topics", {})
analysis        = report.get("analysis", "")
insights        = report.get("insights", [])
comparison      = report.get("comparison", "")
quality_score   = report.get("quality_score", 0)
reflect_history = report.get("reflect_history", [])
notify_status   = report.get("notify_status", "")

# ── 메트릭 ──────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("수집된 레포", f"{len(repos)}개")
with col2:
    top_lang = list(stats.keys())[0] if stats else "-"
    st.metric("1위 언어", top_lang)
with col3:
    total_stars = sum(r.get("stars", 0) for r in repos)
    st.metric("총 스타 수", f"{total_stars:,}")
with col4:
    st.metric("AI 품질 점수", f"{quality_score}/100")
with col5:
    attempts = len(reflect_history)
    st.metric("재생성 횟수", f"{attempts}회")

st.divider()

# ── Self-Correction 이력 ─────────────────────────────────────
if reflect_history:
    with st.expander("🔄 Self-Correction 이력", expanded=True):
        for item in reflect_history:
            attempt  = item.get("attempt", "?")
            sc       = item.get("score", 0)
            feedback = item.get("feedback", "")
            css_cls  = "reflect-pass" if sc >= 70 else "reflect-fail"
            icon     = "✅" if sc >= 70 else "❌"
            st.markdown(
                f'<div class="{css_cls}">'
                f'{icon} <strong>시도 {attempt}</strong> — 점수: {sc}/100'
                f'<br><small>{feedback}</small></div>',
                unsafe_allow_html=True,
            )

        # 점수 추이 차트
        if len(reflect_history) > 1:
            scores = {f"시도 {h['attempt']}": h["score"] for h in reflect_history}
            st.bar_chart(scores)

# ── 알림 상태 ────────────────────────────────────────────────
if notify_status:
    with st.expander("📬 알림 발송 상태", expanded=True):
        for part in notify_status.split(" | "):
            if "success" in part:
                st.success(part)
            elif "error" in part:
                st.error(part)
            else:
                st.info(part)

st.divider()

# ── 트렌딩 레포 + 차트 ───────────────────────────────────────
left, right = st.columns([1.6, 1])

with left:
    st.markdown("### 🔥 트렌딩 레포")
    for repo in repos[:12]:
        desc  = repo.get("description", "")[:90]
        lang  = repo.get("language", "Unknown")
        stars = repo.get("stars", 0)
        st.markdown(f"""
        <div class="repo-card">
            <a href="{repo['url']}" target="_blank">{repo['name']}</a>
            &nbsp;<span class="lang-tag">{lang}</span> ⭐ {stars:,}
            <br><small style="color:#8b949e">{desc or "설명 없음"}</small>
        </div>
        """, unsafe_allow_html=True)

with right:
    st.markdown("### 📈 언어 분포")
    if stats:
        st.bar_chart(stats)

    st.markdown("### 🏷️ 인기 토픽")
    if topics:
        topic_str = "  ".join([f"`{t}` {c}" for t, c in list(topics.items())[:8]])
        st.markdown(topic_str)

    st.markdown("### 💡 핵심 인사이트")
    for insight in insights:
        st.markdown(
            f'<div class="insight-item">· {insight}</div>',
            unsafe_allow_html=True,
        )

st.divider()

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("### 🤖 AI 트렌드 분석")
    st.markdown(analysis)
with col_b:
    st.markdown("### 📊 이전 대비 변화")
    st.markdown(comparison)
