"""
app.py
──────
week13 Evaluation — Streamlit 대시보드

탭 구성:
  Tab 1 🧪 평가 실행  — 데이터셋 확인 + 평가 실행 버튼
  Tab 2 📊 결과 대시보드 — RAGAS 지표 + 질문별 상세 분석
"""

import os
import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from dataset import TEST_DATASET
from evaluator import run_evaluation, load_latest_result

# ── 페이지 설정 ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="청년정책 RAG 평가 | Week 13",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
  html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif !important; }
  .stApp { background: #F5F3EF; }

  .metric-card {
    background: #fff; border-radius: 12px; padding: 20px 24px;
    border: 1px solid #E8E4DC; text-align: center;
  }
  .metric-label { font-size: 12px; color: #8B7355; font-weight: 600; margin-bottom: 4px; }
  .metric-value { font-size: 2rem; font-weight: 700; color: #3A3228; }
  .metric-desc  { font-size: 11px; color: #9B8E7E; margin-top: 4px; }

  .score-good   { color: #5C9E62 !important; }
  .score-mid    { color: #C4845A !important; }
  .score-bad    { color: #C45A5A !important; }

  .stTabs [data-baseweb="tab-list"] { background: #EDE9E0; border-radius: 10px; padding: 4px; }
  .stTabs [data-baseweb="tab"]      { border-radius: 8px; font-size: 13px; font-weight: 600; }
  .stTabs [aria-selected="true"]    { background: #8B7355 !important; color: #fff !important; }
  .stTabs [aria-selected="false"]   { color: #7C6E5A !important; }

  /* ── 카테고리 카드 ── */
  .cat-section { margin-bottom: 20px; }
  .cat-header {
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 10px;
  }
  .cat-badge {
    border-radius: 20px; padding: 4px 14px;
    font-size: 13px; font-weight: 700; color: #fff;
    white-space: nowrap;
  }
  .cat-count {
    font-size: 12px; color: #9B8E7E;
  }
  .q-list { display: flex; flex-direction: column; gap: 6px; }
  .q-item {
    background: #fff; border: 1px solid #E8E4DC; border-radius: 8px;
    padding: 10px 16px; font-size: 13px; color: #3A3228;
    display: flex; align-items: center; gap: 10px;
  }
  .q-num {
    font-size: 11px; color: #9B8E7E; font-weight: 600;
    min-width: 18px;
  }

  #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    "<h1 style='font-size:1.5rem;font-weight:700;color:#3A3228;margin-bottom:4px;'>"
    "📊 청년정책 Agentic RAG — 평가 대시보드</h1>"
    "<p style='color:#7C6E5A;font-size:13px;margin-bottom:20px;'>"
    "Week 13 · RAGAS + LangSmith 정량 평가</p>",
    unsafe_allow_html=True,
)

# LangSmith 설정 상태 표시
ls_key = os.getenv("LANGCHAIN_API_KEY", "")
ls_on  = bool(ls_key) and os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
ls_badge = (
    f"<span style='background:#5C9E62;color:#fff;border-radius:4px;padding:2px 8px;"
    f"font-size:11px;font-weight:700;'>✓ LangSmith 연결됨 ({os.getenv('LANGCHAIN_PROJECT','default')})</span>"
    if ls_on else
    "<span style='background:#9B8E7E;color:#fff;border-radius:4px;padding:2px 8px;"
    "font-size:11px;'>.env에 LANGCHAIN_API_KEY 미설정 — 로컬 평가만 실행</span>"
)
st.markdown(ls_badge, unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

tab_run, tab_result = st.tabs(["🧪 평가 실행", "📊 결과 대시보드"])


# ════════════════════════════════════════════════════════════════════════════
# Tab 1: 평가 실행
# ════════════════════════════════════════════════════════════════════════════
with tab_run:
    st.markdown("### 📋 테스트 데이터셋 (10개 질문)")
    st.caption("카테고리별로 조건·금액·비교·중복수혜 등 다양한 유형을 포함합니다.")

    # 카테고리별 색상
    CAT_COLOR = {
        "금융":   "#5C7FD4",
        "취업":   "#5C9E62",
        "복지":   "#C4845A",
        "장학금": "#9B5CD4",
        "주거":   "#5AAFC4",
        "창업":   "#D4855C",
    }
    CAT_EMOJI = {
        "금융": "💰", "취업": "💼", "복지": "🤲",
        "장학금": "📚", "주거": "🏠", "창업": "🚀",
    }

    # 카테고리별 그룹핑
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for item in TEST_DATASET:
        groups[item["category"]].append(item)

    # 카테고리 2열 레이아웃으로 표시
    cat_list = list(groups.keys())
    for i in range(0, len(cat_list), 2):
        cols = st.columns(2)
        for j, cat in enumerate(cat_list[i:i+2]):
            items  = groups[cat]
            color  = CAT_COLOR.get(cat, "#8B7355")
            emoji  = CAT_EMOJI.get(cat, "📌")
            with cols[j]:
                # 카테고리 헤더
                st.markdown(
                    f'<div class="cat-section">'
                    f'<div class="cat-header">'
                    f'<span class="cat-badge" style="background:{color};">{emoji} {cat}</span>'
                    f'<span class="cat-count">{len(items)}개 질문</span>'
                    f'</div>'
                    f'<div class="q-list">',
                    unsafe_allow_html=True,
                )
                for idx, item in enumerate(items, 1):
                    st.markdown(
                        f'<div class="q-item">'
                        f'<span class="q-num">Q{idx}</span>'
                        f'{item["question"]}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown('</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ▶ 평가 시작")
    st.markdown(
        "<div style='background:#F0EDE7;border-radius:8px;padding:12px 16px;"
        "font-size:13px;color:#5A4F44;margin-bottom:16px;'>"
        "10개 질문을 week12 Agentic RAG에 실행하고 RAGAS 4개 지표를 계산합니다.<br>"
        "⏱ 예상 소요 시간: <b>3~8분</b> (OpenAI API 호출 포함)</div>",
        unsafe_allow_html=True,
    )

    if st.button("🚀 평가 실행", use_container_width=True, type="primary"):
        progress_bar  = st.progress(0)
        status_text   = st.empty()
        log_container = st.container()

        def on_progress(current, total, item_id):
            pct = int(current / total * 60)  # 0~60%는 RAG 실행
            progress_bar.progress(pct)
            status_text.markdown(
                f"**[{current+1}/{total}]** `{item_id}` 질문 처리 중..."
            )

        with st.spinner(""):
            result = run_evaluation(TEST_DATASET, progress_callback=on_progress)

        progress_bar.progress(100)
        status_text.markdown("✅ **평가 완료!**")

        scores = result.get("ragas_scores", {})
        if scores:
            st.success(
                f"Faithfulness: **{scores.get('faithfulness', 0):.3f}** | "
                f"Answer Relevancy: **{scores.get('answer_relevancy', 0):.3f}** | "
                f"Context Precision: **{scores.get('context_precision', 0):.3f}** | "
                f"Context Recall: **{scores.get('context_recall', 0):.3f}**"
            )
        elif result.get("ragas_error"):
            st.warning(f"RAGAS 오류: {result['ragas_error']}")

        st.info("📊 **결과 대시보드** 탭에서 상세 분석을 확인하세요.")


# ════════════════════════════════════════════════════════════════════════════
# Tab 2: 결과 대시보드
# ════════════════════════════════════════════════════════════════════════════
with tab_result:
    result = load_latest_result()

    if result is None:
        st.info("아직 평가 결과가 없습니다. **평가 실행** 탭에서 먼저 실행해 주세요.")
        st.stop()

    ts      = result.get("timestamp", "")[:19].replace("T", " ")
    scores  = result.get("ragas_scores", {})
    records = result.get("records", [])
    per_rec = result.get("per_record_scores", [])

    st.markdown(f"<div style='color:#8B7355;font-size:12px;margin-bottom:16px;'>마지막 평가: {ts}</div>", unsafe_allow_html=True)

    # ── 전체 RAGAS 지표 카드 ──────────────────────────────────────────────
    METRIC_META = {
        "faithfulness":      ("충실성",    "답변이 검색 문서에 근거하는 정도"),
        "answer_relevancy":  ("답변 관련성", "답변이 질문에 얼마나 관련있는가"),
        "context_precision": ("컨텍스트 정밀도", "검색된 문서 중 관련 문서 비율"),
        "context_recall":    ("컨텍스트 재현율", "정답에 필요한 정보를 검색했는가"),
    }

    if scores:
        st.markdown("### 📈 전체 RAGAS 지표")
        cols = st.columns(4)
        for i, (key, (label, desc)) in enumerate(METRIC_META.items()):
            v = scores.get(key, 0)
            color_cls = "score-good" if v >= 0.7 else ("score-mid" if v >= 0.4 else "score-bad")
            cols[i].markdown(
                f'<div class="metric-card">'
                f'<div class="metric-label">{label}</div>'
                f'<div class="metric-value {color_cls}">{v:.3f}</div>'
                f'<div class="metric-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # 레이더 차트
        st.markdown("<br>", unsafe_allow_html=True)
        radar_keys   = list(METRIC_META.keys())
        radar_vals   = [scores.get(k, 0) for k in radar_keys]
        radar_labels = [METRIC_META[k][0] for k in radar_keys]

        fig = go.Figure(go.Scatterpolar(
            r=radar_vals + [radar_vals[0]],
            theta=radar_labels + [radar_labels[0]],
            fill="toself",
            fillcolor="rgba(92,127,212,0.2)",
            line=dict(color="#5C7FD4", width=2),
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=False,
            height=340,
            margin=dict(l=40, r=40, t=20, b=20),
            paper_bgcolor="#F5F3EF",
            plot_bgcolor="#F5F3EF",
        )
        col_radar, col_bar = st.columns([1, 1])
        col_radar.plotly_chart(fig, use_container_width=True)

        # 바 차트
        bar_fig = px.bar(
            x=radar_labels,
            y=radar_vals,
            color=radar_vals,
            color_continuous_scale=["#C45A5A", "#C4845A", "#5C9E62"],
            range_color=[0, 1],
            labels={"x": "", "y": "점수"},
            text=[f"{v:.3f}" for v in radar_vals],
        )
        bar_fig.update_traces(textposition="outside")
        bar_fig.update_layout(
            height=340,
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            yaxis=dict(range=[0, 1.1]),
            paper_bgcolor="#F5F3EF",
            plot_bgcolor="#F5F3EF",
            coloraxis_showscale=False,
        )
        col_bar.plotly_chart(bar_fig, use_container_width=True)

    elif result.get("ragas_error"):
        st.warning(f"RAGAS 평가 오류: {result['ragas_error']}")

    # ── 질문별 RAG 실행 결과 ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔍 질문별 상세 결과")
    st.caption(f"총 {len(records)}개 질문 · 평균 응답시간: {sum(r['latency_s'] for r in records)/len(records):.1f}s")

    per_rec_map = {r["id"]: r for r in per_rec}

    for rec in records:
        rid    = rec["id"]
        pscores = per_rec_map.get(rid, {})

        # 질문 헤더
        with st.expander(f"**[{rec['category']}] {rec['question']}** — ⏱ {rec['latency_s']}s"):
            c1, c2 = st.columns([1, 1])

            with c1:
                st.markdown("**💬 RAG 답변**")
                st.markdown(
                    f"<div style='background:#fff;border:1px solid #E8E4DC;border-radius:8px;"
                    f"padding:12px;font-size:13px;color:#3A3228;line-height:1.7;'>"
                    f"{rec['answer'][:600]}{'...' if len(rec['answer'])>600 else ''}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("**📌 정답 (Ground Truth)**")
                st.markdown(
                    f"<div style='background:#F0EDE7;border-radius:8px;"
                    f"padding:12px;font-size:13px;color:#5A4F44;line-height:1.7;'>"
                    f"{rec['ground_truth']}</div>",
                    unsafe_allow_html=True,
                )

            with c2:
                st.markdown("**📄 검색된 컨텍스트**")
                for i, ctx in enumerate(rec["contexts"][:3], 1):
                    st.markdown(
                        f"<div style='background:#fff;border:1px solid #DDD9D0;border-radius:6px;"
                        f"padding:8px 12px;font-size:12px;color:#5A4F44;margin-bottom:6px;'>"
                        f"<b>[{i}]</b> {ctx[:200]}...</div>",
                        unsafe_allow_html=True,
                    )

                if pscores:
                    st.markdown("**📊 개별 RAGAS 점수**")
                    score_df = pd.DataFrame([{
                        "지표":   label,
                        "점수":   pscores.get(key, "-"),
                    } for key, (label, _) in METRIC_META.items()])
                    st.dataframe(score_df, hide_index=True, use_container_width=True)

    # ── 실패 사례 분석 ──────────────────────────────────────────────────
    if per_rec:
        st.markdown("---")
        st.markdown("### ⚠ 실패 사례 분석 (하위 3개)")

        sorted_recs = sorted(
            per_rec,
            key=lambda r: (
                r.get("faithfulness", 1) +
                r.get("answer_relevancy", 1) +
                r.get("context_precision", 1) +
                r.get("context_recall", 1)
            )
        )[:3]

        for r in sorted_recs:
            avg = sum([
                r.get("faithfulness", 0),
                r.get("answer_relevancy", 0),
                r.get("context_precision", 0),
                r.get("context_recall", 0),
            ]) / 4
            orig = next((rec for rec in records if rec["id"] == r["id"]), {})
            st.markdown(
                f"<div style='background:#FFF0EE;border:1px solid #E8C4C0;border-radius:8px;"
                f"padding:14px 18px;margin-bottom:10px;'>"
                f"<b>[{r['id']}]</b> {orig.get('question','')}<br>"
                f"<span style='font-size:12px;color:#8B4040;'>평균 점수: {avg:.3f} | "
                f"충실성: {r.get('faithfulness',0):.3f} | "
                f"답변관련성: {r.get('answer_relevancy',0):.3f} | "
                f"컨텍스트정밀도: {r.get('context_precision',0):.3f} | "
                f"컨텍스트재현율: {r.get('context_recall',0):.3f}</span></div>",
                unsafe_allow_html=True,
            )

    # ── 카테고리별 평균 지표 ──────────────────────────────────────────────
    if per_rec:
        st.markdown("---")
        st.markdown("### 📂 카테고리별 평균 점수")

        cat_map: dict[str, list] = {}
        per_rec_map2 = {r["id"]: r for r in per_rec}
        for rec in records:
            cat  = rec["category"]
            ps   = per_rec_map2.get(rec["id"], {})
            if not ps:
                continue
            avg  = sum([ps.get(k, 0) for k in ["faithfulness","answer_relevancy","context_precision","context_recall"]]) / 4
            cat_map.setdefault(cat, []).append(avg)

        cat_avg = {cat: round(sum(vs)/len(vs), 3) for cat, vs in cat_map.items()}
        st.bar_chart(cat_avg)

    # ── LangSmith 링크 ───────────────────────────────────────────────────
    if ls_on:
        project = os.getenv("LANGCHAIN_PROJECT", "default")
        st.markdown("---")
        st.markdown(
            f"<div style='background:#EEF4FF;border:1px solid #C5D5F5;border-radius:8px;"
            f"padding:14px 18px;font-size:13px;color:#3A3A6A;'>"
            f"🔗 <b>LangSmith 트레이싱 활성화됨</b><br>"
            f"프로젝트 <code>{project}</code>에서 RAGAS LLM 호출 내역을 확인할 수 있습니다.<br>"
            f"<a href='https://smith.langchain.com' target='_blank'>smith.langchain.com</a>에서 확인하세요.</div>",
            unsafe_allow_html=True,
        )
