"""
app.py — Streamlit UI (FRONTEND 계층)

실행: python -X utf8 -m streamlit run frontend/app.py
      (week14-final-demo/minseon/ 위치에서 실행)
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

import streamlit as st

from backend.graph import run
from backend.tools.policy_loader import _load_all_docs
from frontend.session_manager import (
    new_session, get_all, save_session, rename_session, delete_session,
    sign_in, sign_up, sign_out,
)

# ── 페이지 설정 ──────────────────────────────────────────────────
st.set_page_config(
    page_title="청년정책 AI",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
  html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif !important; }
  .stApp { background: #F5F3EF; }

  /* ── 말풍선 ── */
  .bubble { padding:14px 18px; border-radius:16px; margin:8px 0;
            max-width:76%; line-height:1.7; font-size:14px; word-break:break-word; }
  .bubble.user { background:#4F7EFF; color:#fff !important; margin-left:auto;
                 border-bottom-right-radius:4px; }
  .bubble.user * { color:#fff !important; }
  .bubble.ai   { background:#fff; color:#1A1A1A !important;
                 border:1px solid #E8E4DC; border-bottom-left-radius:4px; }
  .bubble.ai * { color:#1A1A1A !important; }
  .msg-row { display:flex; gap:10px; align-items:flex-end; margin:12px 0; }
  .msg-row.user { flex-direction:row-reverse; }
  .avatar { width:34px; height:34px; border-radius:50%; display:flex;
            align-items:center; justify-content:center;
            font-size:12px; font-weight:700; flex-shrink:0; background:#E8E4DC; }

  /* ── 실행 trace ── */
  .trace-box { background:#F0EDE7; border:1px solid #DDD9D0; border-radius:10px;
               padding:10px 14px; margin:4px 0 10px 44px; font-size:12px; color:#6B5F52; }
  .trace-step { display:flex; gap:8px; align-items:flex-start;
                padding:3px 0; border-bottom:1px solid #E5E0D8; }
  .trace-step:last-child { border-bottom:none; }
  .badge-node { border-radius:4px; padding:1px 7px; font-size:10px; font-weight:700;
                color:#fff; white-space:nowrap; flex-shrink:0; margin-top:1px; }
  .bg-blue   { background:#5C7FD4; }
  .bg-green  { background:#5C9E62; }
  .bg-orange { background:#C4845A; }
  .bg-purple { background:#8B5CD4; }

  /* ── 탭 ── */
  .stTabs [data-baseweb="tab-list"] { background:#EDE9E0; border-radius:10px; padding:4px; }
  .stTabs [data-baseweb="tab"] { border-radius:8px; font-size:13px; font-weight:600; }
  .stTabs [aria-selected="true"]  { background:#8B7355 !important; color:#fff !important; }
  .stTabs [aria-selected="false"] { color:#7C6E5A !important; }
  .stTabs [aria-selected="true"]  p,
  .stTabs [aria-selected="true"]  span { color:#fff !important; }
  .stTabs [aria-selected="false"] p,
  .stTabs [aria-selected="false"] span { color:#3A3228 !important; }

  /* ── 일반 버튼 ── */
  .stButton > button {
    background:#fff !important; color:#3A3228 !important;
    font-weight:600 !important; font-size:13px !important;
    border:1.5px solid #DDD9D0 !important; border-radius:10px !important;
  }
  .stButton > button:hover {
    background:#ffffff !important; border-color:#8B7355 !important;
  }

  /* ── 카테고리 버튼 ── */
  .cat-icon-row .stButton > button {
    background:#2A2A2A !important;
    border:1.5px solid #E0DDD6 !important;
    border-radius:50px !important;
    height:52px !important;
    padding:6px 4px !important;
    font-size:13px !important;
    font-weight:600 !important;
  }
  .cat-icon-row .stButton > button:hover,
  .cat-icon-row .stButton > button:hover p,
  .cat-icon-row .stButton > button:hover span,
  .cat-icon-row .stButton > button:hover div {
    background:#F0EDE7 !important;
    border-color:#8B7355 !important;
    color:#3A3228 !important;
  }
  .cat-icon-row .stButton > button,
  .cat-icon-row .stButton > button p,
  .cat-icon-row .stButton > button span,
  .cat-icon-row .stButton > button div {
    color:#ffffff !important;
    text-align:center !important;
  }

  /* ── 글자색 전반 ── */
  .stApp, .stApp p, .stApp span, .stApp div,
  .stApp label, .stApp h1, .stApp h2, .stApp h3,
  .stApp li, .stApp strong, .stApp small { color:#3A3228 !important; }
  .stTextInput label, [data-testid="stWidgetLabel"] { color:#3A3228 !important; }
  .stTextInput input::placeholder { color:#B0A89E !important; }
  .stTextInput input { background:#fff !important; color:#3A3228 !important; }
  .stChatInput > div { background:#fff !important; border-radius:14px !important;
                       border:1px solid #DDD9D0 !important; }
  .streamlit-expanderHeader { font-size:14px !important; font-weight:600 !important;
                               color:#3A3228 !important; }

  /* ── 사이드바 ── */
  [data-testid="stSidebar"] { background:#EDE9E0 !important; }
  [data-testid="stSidebar"] * { color:#3A3228 !important; }
  [data-testid="stSidebar"] .stButton > button {
    background:#fff !important; border:1px solid #DDD9D0 !important;
    color:#3A3228 !important; font-size:13px !important;
  }

  /* ── 로그인 버튼 ── */
  .auth-login .stButton > button {
    background:#4F7EFF !important; color:#fff !important;
    border:none !important; border-radius:20px !important;
    padding:4px 20px !important; font-size:13px !important;
    height:36px !important;
  }
  .auth-login .stButton > button:hover { background:#3A6FEF !important; }
  .auth-login .stButton > button p,
  .auth-login .stButton > button span { color:#fff !important; }
  .auth-out .stButton > button {
    border-radius:20px !important; font-size:12px !important;
    height:34px !important; padding:4px 14px !important;
  }

  #MainMenu, footer, header { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ── 세션 상태 초기화 ─────────────────────────────────────────────
if "current_sid" not in st.session_state:
    sid = new_session("첫 번째 대화")
    st.session_state.update({
        "current_sid": sid,
        "messages":    [],
        "traces":      [],
        "logged_in":   False,
        "user_name":   "",
        "show_login":  False,
    })
if "rename_mode" not in st.session_state:
    st.session_state["rename_mode"] = None

TRACE_NODE_CLASS = {
    "agent_node":      "bg-blue",
    "tool_dispatcher": "bg-purple",
    "grade_docs_node": "bg-orange",
    "rewrite_node":    "bg-orange",
    "generate_node":   "bg-green",
}

CATEGORIES = ["일자리", "진로", "창업", "주거", "금융", "교육", "마음건강", "신체건강", "문화/예술", "생활지원"]

CATEGORY_QUESTIONS = {
    "일자리":    "취업 준비생이나 구직자를 위한 일자리 지원 정책 추천해줘",
    "진로":      "진로 탐색이나 직업훈련, 자격증 지원 정책 알려줘",
    "창업":      "청년 창업 지원 정책 어떤 게 있어?",
    "주거":      "청년 월세 지원이나 주거 지원 정책 알려줘",
    "금융":      "청년도약계좌나 금융 지원 정책 추천해줘",
    "교육":      "국가장학금이나 학자금 지원 받을 수 있는 조건 알려줘",
    "마음건강":  "청년 심리 상담이나 마음건강 지원 정책 알려줘",
    "신체건강":  "청년 건강검진이나 의료비 지원 정책 알려줘",
    "문화/예술": "청년 문화, 여가, 예술 관련 지원 정책 알려줘",
    "생활지원":  "청년 생활비 지원이나 복지 혜택 알려줘",
}

# ════════════════════════════════════════════════════════════════
# 헤더 (제목 + 로그인 상태)
# ════════════════════════════════════════════════════════════════
col_title, col_auth = st.columns([7, 3])

with col_title:
    st.markdown(
        "<h1 style='font-size:1.4rem;font-weight:700;color:#3A3228;margin:10px 0 4px;'>"
        "청년정책 AI</h1>",
        unsafe_allow_html=True,
    )

with col_auth:
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    if st.session_state["logged_in"]:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(
                f"<div style='font-size:13px;font-weight:600;padding:9px 0;text-align:right;'>"
                f"{st.session_state['user_name']}</div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown('<div class="auth-out">', unsafe_allow_html=True)
            if st.button("로그아웃", key="logout_btn"):
                sign_out()
                st.session_state.update({"logged_in": False, "user_name": "", "show_login": False})
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                "<div style='font-size:13px;color:#9B8E7E;padding:9px 0;text-align:right;'>비로그인</div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown('<div class="auth-login">', unsafe_allow_html=True)
            if st.button("로그인", key="login_open_btn"):
                st.session_state["show_login"] = not st.session_state.get("show_login", False)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ── 로그인 폼 ────────────────────────────────────────────────────
if st.session_state.get("show_login") and not st.session_state["logged_in"]:
    _, form_col, _ = st.columns([5, 3, 2])
    with form_col:
        st.markdown(
            "<div style='background:#fff;border:1px solid #E8E4DC;border-radius:12px;padding:20px 24px;'>",
            unsafe_allow_html=True,
        )
        # 로그인 / 회원가입 탭
        login_tab, signup_tab = st.tabs(["로그인", "회원가입"])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input("이메일", placeholder="example@email.com")
                pw    = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")
                if st.form_submit_button("로그인", use_container_width=True):
                    if email and pw:
                        try:
                            res = sign_in(email, pw)
                            st.session_state.update({
                                "logged_in":  True,
                                "user_name":  res["user"].email.split("@")[0],
                                "show_login": False,
                            })
                            st.rerun()
                        except Exception as e:
                            st.error(f"로그인 실패: 이메일 또는 비밀번호를 확인해주세요.")
                    else:
                        st.warning("이메일과 비밀번호를 입력해주세요.")

        with signup_tab:
            with st.form("signup_form"):
                su_email = st.text_input("이메일", placeholder="example@email.com", key="su_email")
                su_pw    = st.text_input("비밀번호", type="password", placeholder="6자 이상", key="su_pw")
                su_pw2   = st.text_input("비밀번호 확인", type="password", placeholder="비밀번호 재입력", key="su_pw2")
                if st.form_submit_button("회원가입", use_container_width=True):
                    if not (su_email and su_pw):
                        st.warning("이메일과 비밀번호를 입력해주세요.")
                    elif su_pw != su_pw2:
                        st.error("비밀번호가 일치하지 않습니다.")
                    elif len(su_pw) < 6:
                        st.error("비밀번호는 6자 이상이어야 합니다.")
                    else:
                        try:
                            sign_up(su_email, su_pw)
                            st.success("회원가입 완료! 이메일을 확인해 인증 후 로그인해주세요.")
                        except Exception:
                            st.error("이미 사용 중인 이메일입니다.")
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='border:none;border-top:1px solid #E8E4DC;margin:4px 0 16px;'>",
            unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# 사이드바: 멀티세션 관리
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        "<div style='font-size:1rem;font-weight:700;margin-bottom:14px;'>대화 세션</div>",
        unsafe_allow_html=True,
    )

    if st.button("+ 새 대화", use_container_width=True):
        save_session(st.session_state["current_sid"],
                     st.session_state["messages"], st.session_state["traces"])
        sid = new_session()
        st.session_state.update({"current_sid": sid, "messages": [], "traces": [], "rename_mode": None})
        st.rerun()

    st.markdown("<hr style='border:none;border-top:1px solid #DDD9D0;margin:10px 0;'>",
                unsafe_allow_html=True)

    all_sessions = get_all()
    current_sid  = st.session_state["current_sid"]

    for sid, sess in sorted(all_sessions.items(), key=lambda x: x[1].get("created_at", ""), reverse=True):
        is_cur = sid == current_sid

        if st.session_state["rename_mode"] == sid:
            new_name = st.text_input("이름 변경", value=sess["name"], key=f"ri_{sid}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("저장", key=f"rs_{sid}", use_container_width=True):
                    rename_session(sid, new_name.strip() or sess["name"])
                    st.session_state["rename_mode"] = None
                    st.rerun()
            with c2:
                if st.button("취소", key=f"rc_{sid}", use_container_width=True):
                    st.session_state["rename_mode"] = None
                    st.rerun()
        else:
            c_name, c_edit, c_del = st.columns([5, 1, 1])
            with c_name:
                label = f"> {sess['name']}" if is_cur else sess["name"]
                if st.button(label, key=f"s_{sid}", use_container_width=True):
                    if not is_cur:
                        save_session(current_sid, st.session_state["messages"], st.session_state["traces"])
                        loaded = all_sessions.get(sid, {})
                        st.session_state.update({
                            "current_sid": sid,
                            "messages":    loaded.get("messages", []),
                            "traces":      loaded.get("traces", []),
                        })
                        st.rerun()
            with c_edit:
                if st.button("수정", key=f"e_{sid}"):
                    st.session_state["rename_mode"] = sid
                    st.rerun()
            with c_del:
                if st.button("삭제", key=f"d_{sid}"):
                    delete_session(sid)
                    if is_cur:
                        remaining = get_all()
                        if remaining:
                            first = next(iter(remaining))
                            st.session_state.update({
                                "current_sid": first,
                                "messages":    remaining[first].get("messages", []),
                                "traces":      remaining[first].get("traces", []),
                            })
                        else:
                            new_sid = new_session()
                            st.session_state.update({"current_sid": new_sid, "messages": [], "traces": []})
                    st.rerun()

# ════════════════════════════════════════════════════════════════
# 탭 (챗봇 + 카테고리)
# ════════════════════════════════════════════════════════════════
tab_chat, tab_category = st.tabs(["챗봇", "카테고리"])

# ════════════════════════════════════════════════════════════════
# Tab 1: 챗봇
# ════════════════════════════════════════════════════════════════
with tab_chat:

    # 카테고리 빠른 탐색 버튼 (10개 한 줄)
    st.markdown('<div class="cat-icon-row">', unsafe_allow_html=True)
    cols = st.columns(10)
    for i, cat in enumerate(CATEGORIES):
        with cols[i]:
            if st.button(cat, key=f"qcat_{cat}", use_container_width=True,
                         help=CATEGORY_QUESTIONS[cat]):
                st.session_state["_pending_question"] = CATEGORY_QUESTIONS[cat]
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr style='border:none;border-top:1px solid #E8E4DC;margin:10px 0;'>",
                unsafe_allow_html=True)

    # 카테고리 버튼 클릭 처리
    if "_pending_question" in st.session_state:
        pending = st.session_state.pop("_pending_question")
        st.session_state["messages"].append({"role": "user", "content": pending})
        with st.spinner("검색 중..."):
            result = run(pending)
        answer = result.get("answer", "답변을 생성하지 못했습니다.")
        trace  = result.get("execution_trace", [])
        st.session_state["messages"].append({"role": "assistant", "content": answer})
        st.session_state["traces"].append(trace)
        save_session(st.session_state["current_sid"], st.session_state["messages"], st.session_state["traces"])
        st.rerun()

    # 초기 화면
    if not st.session_state["messages"]:
        st.markdown("""
        <div style="text-align:center;padding:40px 20px;color:#9B8E7E;">
          <div style="font-size:1rem;font-weight:600;color:#5A4F44;margin-bottom:10px;">무엇이든 물어보세요</div>
          <div style="font-size:13px;line-height:2;color:#7C6E5A;">
            "청년도약계좌 가입 조건이 어떻게 돼?"<br>
            "청년도약계좌랑 희망적금 중 뭐가 나아?"<br>
            "취업 관련 정책 어떤 게 있어?"
          </div>
        </div>
        """, unsafe_allow_html=True)

    # 대화 렌더링
    for i, msg in enumerate(st.session_state["messages"]):
        role, content = msg["role"], msg["content"]
        if role == "user":
            st.markdown(f"""
            <div class="msg-row user">
              <div class="avatar">나</div>
              <div class="bubble user">{content}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-row">
              <div class="avatar">AI</div>
              <div class="bubble ai">{content}</div>
            </div>""", unsafe_allow_html=True)

            pass

    # 입력
    if prompt := st.chat_input("청년정책에 대해 질문하세요..."):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.spinner("검색 중..."):
            result = run(prompt)
        answer = result.get("answer", "답변을 생성하지 못했습니다.")
        trace  = result.get("execution_trace", [])
        st.session_state["messages"].append({"role": "assistant", "content": answer})
        st.session_state["traces"].append(trace)
        save_session(st.session_state["current_sid"], st.session_state["messages"], st.session_state["traces"])
        st.rerun()


# ════════════════════════════════════════════════════════════════
# Tab 2: 카테고리 탐색
# ════════════════════════════════════════════════════════════════
CAT_COLOR = {
    "일자리":    "#5C9E62",
    "진로":      "#5C7FD4",
    "창업":      "#D4855C",
    "주거":      "#5AAFC4",
    "금융":      "#9B5CD4",
    "교육":      "#7B5CD4",
    "마음건강":  "#C45A8A",
    "신체건강":  "#E05C5C",
    "문화/예술": "#D4A55C",
    "생활지원":  "#6B8E6B",
}

with tab_category:
    @st.cache_data(ttl=300)
    def _cached_docs():
        return _load_all_docs()

    all_docs = _cached_docs()

    if "selected_cat" not in st.session_state:
        st.session_state["selected_cat"] = None
    selected = st.session_state["selected_cat"]

    st.markdown(
        "<div style='font-size:13px;color:#5A4F44;margin-bottom:14px;'>"
        "카테고리를 선택하면 해당 정책 목록을 볼 수 있어요.</div>",
        unsafe_allow_html=True,
    )

    # 카테고리 버튼 (5+5 두 줄)
    st.markdown('<div class="cat-icon-row">', unsafe_allow_html=True)
    for row_cats in [CATEGORIES[:5], CATEGORIES[5:]]:
        cols = st.columns(5)
        for col, cat in zip(cols, row_cats):
            is_sel = selected == cat
            label  = f"> {cat}" if is_sel else cat
            with col:
                if st.button(label, key=f"catbtn_{cat}", use_container_width=True):
                    st.session_state["selected_cat"] = None if is_sel else cat
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr style='border:none;border-top:1px solid #E8E4DC;margin:14px 0;'>",
                unsafe_allow_html=True)

    if selected:
        color = CAT_COLOR.get(selected, "#8B7355")
        docs  = [d for d in all_docs if d["category"] == selected]

        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:14px;'>"
            f"<span style='background:{color};color:#fff;border-radius:20px;padding:4px 16px;"
            f"font-size:14px;font-weight:700;'>{selected}</span>"
            f"<span style='color:#8B7355;font-size:13px;'>총 {len(docs)}개 정책</span></div>",
            unsafe_allow_html=True,
        )

        search_q = st.text_input("이름으로 검색", placeholder="예: 청년도약, 월세, 자격증...",
                                  key="cat_search", label_visibility="collapsed")
        if search_q:
            docs = [d for d in docs if search_q.lower() in d["title"].lower()]
            st.caption(f"'{search_q}' 검색 결과: {len(docs)}개")

        for doc in docs:
            title   = doc["title"]
            content = doc["content"].strip()
            preview = next(
                (l.strip()[:80] for l in content.splitlines() if l.strip() and not l.strip().startswith("#")),
                "",
            )
            with st.expander(f"**{title}**" + (f"  —  {preview}..." if preview else "")):
                col_c, col_b = st.columns([4, 1])
                with col_c:
                    st.markdown(
                        f"<div style='font-size:13px;color:#3A3228;line-height:1.7;white-space:pre-wrap;'>"
                        f"{content[:600]}{'...' if len(content) > 600 else ''}</div>",
                        unsafe_allow_html=True,
                    )
                with col_b:
                    if st.button("질문하기", key=f"ask_{title[:20]}", use_container_width=True):
                        q = f"{title}에 대해 자세히 알려줘"
                        st.session_state["messages"].append({"role": "user", "content": q})
                        with st.spinner("검색 중..."):
                            result = run(q)
                        st.session_state["messages"].append({
                            "role": "assistant",
                            "content": result.get("answer", "답변을 생성하지 못했습니다."),
                        })
                        st.session_state["traces"].append(result.get("execution_trace", []))
                        save_session(st.session_state["current_sid"], st.session_state["messages"],
                                     st.session_state["traces"])
                        st.session_state["selected_cat"] = None
                        st.rerun()
    else:
        total = len(all_docs)
        st.markdown(
            f"<div style='text-align:center;padding:30px 20px;color:#9B8E7E;'>"
            f"<div style='font-size:14px;font-weight:600;color:#5A4F44;margin-bottom:6px;'>"
            f"카테고리를 선택해서 정책을 탐색하세요</div>"
            f"<div style='font-size:13px;'>전체 {total}개 정책 · {len(CATEGORIES)}개 카테고리</div></div>",
            unsafe_allow_html=True,
        )
