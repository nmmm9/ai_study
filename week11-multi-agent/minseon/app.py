"""
app.py — 청년정책 AI 챗봇 (week11 멀티에이전트)
실행: python -X utf8 -m streamlit run app.py
"""

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

st.set_page_config(
    page_title="청년정책 AI",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ── 전체 레이아웃 ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #f0f2f5 !important;
}
.stApp { background: #f0f2f5 !important; }
[data-testid="stHeader"] { display: none; }
[data-testid="stSidebar"] { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── 채팅 래퍼 ── */
.chat-wrapper {
    max-width: 800px;
    margin: 0 auto;
    padding: 0 24px 140px;
    min-height: 100vh;
}

/* ── 상단 헤더 ── */
.top-bar {
    position: sticky; top: 0; z-index: 100;
    background: rgba(240,242,245,.92);
    backdrop-filter: blur(12px);
    padding: 16px 0 12px;
    margin-bottom: 8px;
    text-align: center;
}
.top-bar h2 {
    font-size: 1.1rem; font-weight: 600;
    color: #111 !important; margin: 0;
}
.top-bar span {
    font-size: 0.78rem; color: #888 !important;
}

/* ── 메시지 버블 ── */
.msg-row {
    display: flex; margin: 10px 0; align-items: flex-end; gap: 10px;
}
.msg-row.user { flex-direction: row-reverse; }

.avatar {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 700; flex-shrink: 0;
}
.avatar.ai   { background: #111; color: #fff; }
.avatar.user { background: #0057ff; color: #fff; }

.bubble {
    max-width: 74%; padding: 14px 18px;
    border-radius: 18px; font-size: 0.93rem;
    line-height: 1.7; word-break: keep-all;
}
/* 흰 배경 → 검정 글자 */
.bubble.ai {
    background: #ffffff;
    color: #111111 !important;
    border-radius: 4px 18px 18px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,.1);
}
.bubble.ai  * { color: #111111 !important; }
.bubble.ai table { border-collapse:collapse; width:100%; margin:8px 0; font-size:.85rem; }
.bubble.ai th { background:#f4f4f4; padding:7px 11px; text-align:left; color:#111 !important; }
.bubble.ai td { padding:7px 11px; border-bottom:1px solid #eee; color:#111 !important; }
.bubble.ai h3 { font-size:.95rem; margin:12px 0 5px; color:#111 !important; }
.bubble.ai ul { padding-left:18px; margin:5px 0; }
.bubble.ai strong { font-weight:700; color:#111 !important; }

/* 파란 배경 → 흰 글자 */
.bubble.user {
    background: #0057ff;
    color: #ffffff !important;
    border-radius: 18px 18px 4px 18px;
}
.bubble.user, .bubble.user *,
.bubble.user p, .bubble.user span,
.bubble.user div, .bubble.user strong { color: #ffffff !important; }

/* ── 관련 사이트 링크 ── */
.site-links {
    display: flex; flex-wrap: wrap; gap: 7px;
    margin-top: 10px; padding-top: 10px;
    border-top: 1px solid #f0f0f0;
}
.site-link {
    display: inline-flex; align-items: center; gap: 4px;
    background: #f4f6ff; border: 1px solid #d0d9ff;
    border-radius: 20px; padding: 4px 12px;
    font-size: .78rem; color: #0057ff !important;
    text-decoration: none; transition: .15s;
}
.site-link:hover { background: #e0e8ff; }

/* ── 분석 중 표시 ── */
.thinking-row { display:flex; align-items:flex-end; gap:8px; margin:6px 0; }
.thinking-bubble {
    background:#fff; border-radius:4px 18px 18px 18px;
    padding:14px 20px; box-shadow:0 1px 3px rgba(0,0,0,.08);
    display:flex; gap:5px; align-items:center;
}
.dot {
    width:7px; height:7px; border-radius:50%; background:#ccc;
    animation: bounce .9s infinite;
}
.dot:nth-child(2) { animation-delay:.15s; }
.dot:nth-child(3) { animation-delay:.3s; }
@keyframes bounce {
    0%,60%,100% { transform:translateY(0); }
    30%          { transform:translateY(-6px); background:#0057ff; }
}

/* ── 입력창 ── */
.input-area {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: rgba(240,242,245,.95);
    backdrop-filter: blur(12px);
    padding: 14px 16px 20px;
    z-index: 200;
}
.input-inner {
    max-width: 780px; margin: 0 auto;
    display: flex; gap: 10px; align-items: center;
}

/* Streamlit 입력 오버라이드 */
[data-testid="stChatInput"] {
    position: fixed !important; bottom: 14px !important;
    left: 50% !important; transform: translateX(-50%) !important;
    width: min(780px, calc(100vw - 32px)) !important;
    background: #fff !important;
    border-radius: 24px !important;
    border: 1.5px solid #e0e0e0 !important;
    box-shadow: 0 2px 12px rgba(0,0,0,.08) !important;
    z-index: 9999 !important;
}
[data-testid="stChatInput"] textarea {
    color: #111111 !important;
    font-size: 0.95rem !important;
    background: #ffffff !important;
}
[data-testid="stChatInput"] > div {
    background: #ffffff !important;
}
[data-testid="stChatInput"] {
    background: #ffffff !important;
}
[data-testid="stChatInputSubmitButton"] { color: #0057ff !important; }

/* ── 예시 질문 칩 ── */
.chip-row { display:flex; flex-wrap:wrap; gap:8px; margin:16px 0; justify-content:center; }
.chip {
    background:#fff; border:1.5px solid #e0e0e0;
    border-radius:20px; padding:8px 16px;
    font-size:.85rem; color:#333 !important;
    cursor:pointer; transition:.15s;
    box-shadow: 0 1px 3px rgba(0,0,0,.05);
}
.chip:hover { border-color:#0057ff; color:#0057ff !important; }

/* ── 상태 배지 ── */
.status-bar {
    text-align:center; margin: 8px 0 16px;
    font-size:.78rem; color:#aaa !important;
}
.status-dot {
    display:inline-block; width:7px; height:7px;
    border-radius:50%; background:#22c55e;
    margin-right:5px; vertical-align:middle;
}

/* ── 초기 화면 ── */
.welcome {
    text-align:center; padding:60px 20px 30px;
}
.welcome h1 { font-size:2rem; font-weight:700; color:#111 !important; margin-bottom:8px; }
.welcome p  { font-size:1rem; color:#777 !important; margin:0; }
.welcome-icon { font-size:3rem; margin-bottom:16px; }

/* 기타 숨기기 */
#MainMenu, footer, header { visibility:hidden; }
[data-testid="stChatMessage"] { background:transparent !important; padding:0 !important; }
[data-testid="stChatMessage"] > div { padding:0 !important; }
</style>
""", unsafe_allow_html=True)

# ── 세션 초기화 ──────────────────────────────────────────────────
for k, v in [
    ("messages", []),
    ("graph_messages", []),
    ("user_profile", {}),
    ("profile_complete", False),
    ("final_answer", ""),
    ("selected_agents", []),
    ("is_thinking", False),
]:
    if k not in st.session_state:
        st.session_state[k] = v

EXAMPLES = [
    "취업 준비 중인데 받을 수 있는 지원 알려줘",
    "장학금 종류 추천해줘",
    "청년 월세 지원 받고 싶어",
    "금융 혜택 뭐가 있어?",
]

AGENT_LABELS = {
    "scholarship": "장학금",
    "employment":  "취업",
    "housing":     "주거",
    "finance":     "금융",
}

# 키워드 → 관련 사이트 매핑
SITE_MAP = [
    (["장학금", "학자금", "등록금", "국가장학", "근로장학"],
     [("🎓 국가장학금", "https://www.kosaf.go.kr"),
      ("📚 한국장학재단", "https://www.kosaf.go.kr/ko/scholar.do")]),
    (["취업", "일자리", "고용", "채용", "인턴", "취준"],
     [("💼 고용24", "https://www.work24.go.kr"),
      ("🏢 청년일자리", "https://www.work.go.kr/youth")]),
    (["주거", "월세", "전세", "청약", "주택"],
     [("🏠 청약홈", "https://www.applyhome.co.kr"),
      ("🏡 마이홈", "https://www.myhome.go.kr")]),
    (["적금", "도약계좌", "금융", "저축"],
     [("💰 서민금융진흥원", "https://www.kinfa.or.kr")]),
    (["청년", "정책", "지원"],
     [("🌐 온통청년", "https://www.youthcenter.go.kr"),
      ("📋 복지로", "https://www.bokjiro.go.kr")]),
]

def get_site_links(content: str) -> list[tuple]:
    """답변 내용에서 관련 사이트 추출."""
    links = []
    seen  = set()
    lower = content.lower()
    for keywords, sites in SITE_MAP:
        if any(kw in lower for kw in keywords):
            for name, url in sites:
                if url not in seen:
                    seen.add(url)
                    links.append((name, url))
    return links[:5]  # 최대 5개


def render_message(role: str, content: str):
    """메시지 버블 렌더링."""
    import re
    if role == "user":
        safe = content.replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(f"""
        <div class="msg-row user">
            <div class="bubble user">{safe}</div>
            <div class="avatar user">나</div>
        </div>""", unsafe_allow_html=True)
    else:
        # 마크다운 → HTML 변환
        html = content.replace("<", "&lt;").replace(">", "&gt;")
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'### (.+)',  r'<h3>\1</h3>', html)
        html = re.sub(r'## (.+)',   r'<h3>\1</h3>', html)
        html = re.sub(r'# (.+)',    r'<h3>\1</h3>', html)
        html = re.sub(r'\n- (.+)',  r'<br>• \1',    html)
        html = html.replace('\n', '<br>')

        # 관련 사이트 링크
        links     = get_site_links(content)
        links_html = ""
        if links:
            link_tags = "".join(
                f'<a class="site-link" href="{url}" target="_blank">{name}</a>'
                for name, url in links
            )
            links_html = f'<div class="site-links">{link_tags}</div>'

        st.markdown(f"""
        <div class="msg-row ai">
            <div class="avatar ai">AI</div>
            <div class="bubble ai">{html}{links_html}</div>
        </div>""", unsafe_allow_html=True)


def render_thinking():
    st.markdown("""
    <div class="thinking-row">
        <div class="avatar ai">AI</div>
        <div class="thinking-bubble">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    </div>""", unsafe_allow_html=True)


# ── 헤더 ─────────────────────────────────────────────────────────
st.markdown("""
<div class="top-bar">
    <h2>청년정책 AI</h2>
    <span><span class="status-dot"></span>멀티에이전트 · 온통청년 1,895개 정책 연동</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

# ── 초기 화면 ─────────────────────────────────────────────────────
if not st.session_state["messages"]:
    st.markdown("""
    <div class="welcome">
        <div class="welcome-icon">💬</div>
        <h1>무엇을 도와드릴까요?</h1>
        <p>나이와 지역을 알려주시면 딱 맞는 청년 지원 정책을 찾아드립니다</p>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="chip-row">', unsafe_allow_html=True)
    cols = st.columns(len(EXAMPLES))
    for i, ex in enumerate(EXAMPLES):
        with cols[i]:
            if st.button(ex, key=f"chip_{i}", use_container_width=True):
                st.session_state["pending"] = ex
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── 대화 히스토리 ─────────────────────────────────────────────────
for msg in st.session_state["messages"]:
    render_message(msg["role"], msg["content"])

# ── 분석 중 표시 ─────────────────────────────────────────────────
if st.session_state["is_thinking"]:
    render_thinking()

st.markdown('</div>', unsafe_allow_html=True)

# ── 입력 처리 ─────────────────────────────────────────────────────
pending    = st.session_state.pop("pending", None)
user_input = st.chat_input("메시지를 입력하세요") or pending

if user_input and not st.session_state["is_thinking"]:
    from graph import run_step

    # 사용자 메시지 추가
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.session_state["graph_messages"].append({"role": "user", "content": user_input})
    st.session_state["is_thinking"] = True
    st.rerun()

# 분석 실행 (is_thinking 상태일 때)
if st.session_state["is_thinking"]:
    from graph import run_step

    try:
        result = run_step(
            messages=st.session_state["graph_messages"],
            user_profile=st.session_state["user_profile"],
            profile_complete=st.session_state["profile_complete"],
        )

        new_msgs = result.get("messages", [])
        # 마지막 assistant 메시지 추출
        assistant_reply = next(
            (m["content"] for m in reversed(new_msgs) if m["role"] == "assistant"),
            None,
        )

        final = result.get("final_answer", "")
        reply = final or assistant_reply or ""

        if reply:
            st.session_state["messages"].append({"role": "assistant", "content": reply})

        st.session_state["graph_messages"]   = result.get("messages", [])
        st.session_state["user_profile"]     = result.get("user_profile", {})
        st.session_state["profile_complete"] = result.get("profile_complete", False)
        st.session_state["selected_agents"]  = result.get("selected_agents", [])

    except Exception as e:
        st.session_state["messages"].append({
            "role": "assistant",
            "content": f"오류가 발생했습니다. 다시 시도해주세요.\n\n```\n{e}\n```",
        })

    st.session_state["is_thinking"] = False
    st.rerun()
