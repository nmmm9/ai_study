"""
app.py
──────
청년정책 AI 상담사 — LangGraph 버전 Streamlit UI

실행:
    python -X utf8 -m streamlit run app.py
"""

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

st.set_page_config(
    page_title="청년정책 AI 챗봇",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp { background: #f7f7f7; }

/* 전체 텍스트 색상 강제 */
.stApp, .stApp p, .stApp span, .stApp div,
.stApp li, .stApp h1, .stApp h2, .stApp h3,
.stApp label, .stApp strong { color: #1a1a1a !important; }

/* 채팅 메시지 */
[data-testid="stChatMessage"] { color: #1a1a1a !important; }
[data-testid="stChatMessage"] * { color: #1a1a1a !important; }
[data-testid="stChatMessageContent"] * { color: #1a1a1a !important; }

/* st.status 내부 */
[data-testid="stStatusWidget"] * { color: #1a1a1a !important; }
[data-testid="stExpander"] * { color: #1a1a1a !important; }

/* 사이드바 */
[data-testid="stSidebar"] { background: #fff; border-right: 1px solid #e0e0e0; }
[data-testid="stSidebar"] * { color: #1a1a1a !important; }

/* 헤더 */
.header { text-align: center; padding: 1.5rem 0 0.5rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; }
.header p  { font-size: 0.9rem; }

/* 노드 배지 */
.node-badge {
    display: inline-block; border-radius: 3px;
    padding: 0.2rem 0.6rem; font-size: 0.78rem;
    margin: 0.1rem; font-family: monospace;
    background: #e5e7eb; color: #374151 !important;
}
.node-badge.active { background: #2563eb; color: #fff !important; }
.node-badge.done   { background: #16a34a; color: #fff !important; }

/* 버튼 */
.stButton > button {
    background: #fff !important; color: #1a1a1a !important;
    border: 1px solid #ccc !important; border-radius: 3px !important;
}
.stButton > button[data-testid="baseButton-primary"] {
    background: #1a1a1a !important; color: #fff !important;
    border-color: #1a1a1a !important;
}

/* 탭 */
.stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid #1a1a1a !important; }
.stTabs [aria-selected="true"] { background: #1a1a1a !important; color: #fff !important; }
</style>
""", unsafe_allow_html=True)

# ── 노드 메타 ───────────────────────────────────────────────────
NODE_META = {
    "parse_query_node": {"icon": "🔍", "label": "질문 분석"},
    "profile_node":     {"icon": "👤", "label": "조건 파악"},
    "search_node":      {"icon": "📄", "label": "정책 검색"},
    "recommend_node":   {"icon": "✨", "label": "맞춤 추천"},
}

# ── 예시 질문 ───────────────────────────────────────────────────
EXAMPLES = [
    "청년도약계좌 신청 자격이 어떻게 돼?",
    "나 25살 대학생인데 받을 수 있는 장학금 추천해줘",
    "취업 준비 중인데 지원받을 수 있는 정책 알려줘",
    "청년 월세 지원 어떻게 신청해?",
    "국가장학금이랑 근로장학금 차이가 뭐야?",
    "주거 관련 청년 지원 정책 뭐가 있어?",
]

# ── 세션 상태 ────────────────────────────────────────────────────
for k, v in [("messages", []), ("running", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── 사이드바 ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 청년정책 AI 챗봇")
    st.markdown("---")
    st.markdown("#### 예시 질문")
    for ex in EXAMPLES:
        if st.button(ex, use_container_width=True, key=f"ex_{ex}"):
            st.session_state["pending_query"] = ex
            st.rerun()

    st.markdown("---")
    from tools.policy_loader import get_policy_count, get_all_policy_titles
    count  = get_policy_count()
    titles = get_all_policy_titles()
    st.markdown(f"#### 보유 정책 ({count}개)")
    for t in titles:
        st.markdown(f"- {t}")

    st.markdown("---")
    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── 헤더 ────────────────────────────────────────────────────────
st.markdown("""
<div class="header">
    <h1>청년정책 AI 챗봇</h1>
    <p>LangGraph 기반 · 장학금 · 취업 · 주거 · 금융 정책 안내</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

tab_chat, tab_graph = st.tabs(["정책 상담", "그래프 구조"])

# ════════════════════════════════════════════════════════════════
# TAB 1 — 정책 상담
# ════════════════════════════════════════════════════════════════
with tab_chat:

    # 이전 대화 출력
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.markdown(msg["content"])
            else:
                # 실행 추적
                if msg.get("trace"):
                    with st.expander("실행 추적", expanded=False):
                        for step in msg["trace"]:
                            meta = NODE_META.get(step["node"], {"icon": "🔧", "label": step["node"]})
                            st.markdown(
                                f'<span class="node-badge done">'
                                f'{meta["icon"]} {meta["label"]}</span> '
                                f'<span style="font-size:0.8rem;color:#555">'
                                f'{step["summary"]}</span>',
                                unsafe_allow_html=True,
                            )
                st.markdown(msg["content"])

    # 입력 처리
    pending = st.session_state.pop("pending_query", None)
    user_input = st.chat_input(
        "청년정책에 대해 무엇이든 물어보세요",
        disabled=st.session_state.running,
    ) or pending

    if user_input and not st.session_state.running:
        st.session_state.running = True
        st.session_state.messages.append({"role": "user", "content": user_input})

        from graph import stream_run

        accumulated = ""
        last_trace  = []

        with st.chat_message("assistant"):
            # 실행 추적을 st.status로 표시
            with st.status("분석 중...", expanded=True) as status:
                try:
                    for node_name, updates in stream_run(user_input):
                        meta = NODE_META.get(node_name, {"icon": "🔧", "label": node_name})
                        trace = updates.get("execution_trace", [])
                        summary = trace[-1]["summary"] if trace else ""
                        st.write(f"{meta['icon']} **{meta['label']}** — {summary}")

                        if updates.get("recommendation"):
                            accumulated = updates["recommendation"]

                        last_trace = trace

                    status.update(label="분석 완료!", state="complete", expanded=False)

                except Exception as e:
                    import traceback
                    status.update(label="오류 발생", state="error")
                    st.error(f"오류: {e}")
                    st.code(traceback.format_exc())

            # 답변 출력
            if accumulated:
                st.markdown(accumulated)
            else:
                st.warning("답변을 생성하지 못했습니다. 다시 시도해주세요.")

        st.session_state.messages.append({
            "role":    "assistant",
            "content": accumulated,
            "trace":   last_trace,
        })
        st.session_state.running = False
        st.rerun()

    if not st.session_state.messages:
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**질문 유형 자동 분류**\n- 특정 정책 문의\n- 맞춤 추천 요청")
        with c2:
            st.markdown("**조건부 분기**\n- 프로필 수집 필요 여부\n- 검색 결과 없으면 재시도")
        with c3:
            st.markdown("**실시간 추적**\n- 어떤 노드가 실행됐는지\n- 각 단계 결과 요약")

# ════════════════════════════════════════════════════════════════
# TAB 2 — 그래프 구조
# ════════════════════════════════════════════════════════════════
with tab_graph:
    st.markdown("### LangGraph 워크플로우 구조")

    try:
        from graph import graph as policy_graph
        png = policy_graph.get_graph().draw_mermaid_png()
        st.image(png, caption="청년정책 에이전트 그래프")
    except Exception:
        pass

    st.markdown("#### Mermaid 코드")
    st.caption("[mermaid.live](https://mermaid.live) 에 붙여넣어 시각화하세요.")
    from graph import get_mermaid
    st.code(get_mermaid(), language="text")

    st.markdown("---")
    st.markdown("#### 조건부 엣지")
    st.markdown("""
| 출발 노드 | 조건 | 이동 |
|----------|------|------|
| `parse_query_node` | 일반 추천 요청 ("추천해줘") | → `profile_node` |
| `parse_query_node` | 특정 정책 문의 ("청년도약계좌가 뭐야?") | → `search_node` (프로필 생략) |
| `search_node` | 결과 0개 & 재시도 1회 미만 | → `search_node` (전체 DB 재검색) |
| `search_node` | 결과 1개 이상 | → `recommend_node` |
""")
