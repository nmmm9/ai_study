"""
app.py
──────
week12 Agentic RAG — Streamlit UI

기능:
  - 로그인 / 비로그인 선택
  - Tab 1: 챗봇 (Agentic RAG, 로그인 시 프로필 자동 반영)
  - Tab 2: 내 프로필 (정보 수정, 이메일 수신 토글, 즉시 알림 테스트)
  - Tab 3: 알림 이력 (발송 기록)
  - APScheduler 매일 09:00 자동 이메일 발송
"""

import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import user_db
from graph import run, run_notify
from tools.policy_loader import get_category_stats, CATEGORY_EMOJI, get_policies_by_category, _load_all_docs

# ── 스케줄러 (백그라운드) ────────────────────────────────────────
@st.cache_resource
def _start_scheduler():
    from scheduler import get_scheduler
    return get_scheduler()

_start_scheduler()

# ── 페이지 설정 ──────────────────────────────────────────────────
st.set_page_config(
    page_title="청년정책 Agentic RAG",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
  html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif !important; }
  .stApp { background: #F5F3EF; }

  /* ── 로그인 박스 ── */
  .login-box {
    max-width: 480px; margin: 60px auto 0;
    background: #fff; border-radius: 14px;
    padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border: 1px solid #E8E4DC;
  }
  .login-box h2 { font-size: 1.4rem; font-weight: 700; color: #3A3228; margin-bottom: 6px; }
  .login-box p  { font-size: 13px; color: #7C6E5A; margin-bottom: 24px; }

  /* ── 말풍선 ── */
  .bubble { padding: 14px 18px; border-radius: 16px; margin: 8px 0;
            max-width: 76%; line-height: 1.7; font-size: 14px; word-break: break-word; }
  .bubble.user { background: #4F7EFF; color: #fff !important; margin-left: auto;
                 border-bottom-right-radius: 4px; }
  .bubble.user * { color: #fff !important; }
  .bubble.ai   { background: #fff; color: #1A1A1A !important;
                 border: 1px solid #E8E4DC; border-bottom-left-radius: 4px; }
  .bubble.ai * { color: #1A1A1A !important; }

  .msg-row { display: flex; gap: 10px; align-items: flex-end; margin: 12px 0; }
  .msg-row.user { flex-direction: row-reverse; }
  .avatar { width: 34px; height: 34px; border-radius: 50%; display: flex;
            align-items: center; justify-content: center;
            font-size: 16px; flex-shrink: 0; background: #E8E4DC; }

  /* ── Trace 박스 ── */
  .trace-box { background: #F0EDE7; border: 1px solid #DDD9D0; border-radius: 10px;
               padding: 10px 14px; margin: 4px 0 10px 44px; font-size: 12px; color: #6B5F52; }
  .trace-step { display: flex; gap: 8px; align-items: flex-start;
                padding: 3px 0; border-bottom: 1px solid #E5E0D8; }
  .trace-step:last-child { border-bottom: none; }
  .badge-node { border-radius: 4px; padding: 1px 7px;
                font-size: 10px; font-weight: 700; color: #fff;
                white-space: nowrap; flex-shrink: 0; margin-top: 1px; }
  .bg-blue   { background: #5C7FD4; }
  .bg-green  { background: #5C9E62; }
  .bg-orange { background: #C4845A; }

  /* ── 프로필 카드 ── */
  .profile-card { background: #fff; border-radius: 10px; padding: 20px 24px;
                  border: 1px solid #E8E4DC; margin-bottom: 14px; }
  .profile-card h4 { font-size: 14px; font-weight: 700; color: #3A3228; margin-bottom: 12px; }

  /* ── 로그 아이템 ── */
  .log-item { background: #fff; border: 1px solid #E8E4DC; border-radius: 10px;
              padding: 14px 18px; margin-bottom: 10px; font-size: 13px; color: #5A4F44; }
  .log-item .log-time { font-size: 11px; color: #9B8E7E; margin-bottom: 4px; }

  /* ── 탭 ── */
  .stTabs [data-baseweb="tab-list"] { background: #EDE9E0; border-radius: 10px; padding: 4px; }
  .stTabs [data-baseweb="tab"] { border-radius: 8px; font-size: 13px; font-weight: 600; }
  .stTabs [aria-selected="true"] { background: #8B7355 !important; color: #fff !important; }
  .stTabs [aria-selected="false"] { color: #7C6E5A !important; }

  /* ── 전체 글자색 기본값 ── */
  .stApp, .stApp p, .stApp span, .stApp div,
  .stApp label, .stApp h1, .stApp h2, .stApp h3,
  .stApp li, .stApp strong, .stApp small { color: #3A3228 !important; }

  /* ── 입력 라벨·힌트 ── */
  .stTextInput label, .stNumberInput label,
  .stSelectbox label, .stCheckbox label,
  .stCheckbox span, .stRadio label,
  [data-testid="stWidgetLabel"] { color: #3A3228 !important; }

  /* ── 입력창 placeholder ── */
  .stTextInput input::placeholder { color: #B0A89E !important; }

  /* ── 탭 글자 ── */
  .stTabs [data-baseweb="tab"] p,
  .stTabs [data-baseweb="tab"] span { color: #3A3228 !important; }
  .stTabs [aria-selected="true"] p,
  .stTabs [aria-selected="true"] span { color: #fff !important; }

  /* ── 버튼 ── */
  .stButton > button {
    color: #3A3228 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
  }

  /* 입력 필드 */
  .stTextInput input, .stNumberInput input { background: #fff !important; color: #3A3228 !important; }
  .stChatInput > div { background: #fff !important; border-radius: 14px !important;
                       border: 1px solid #DDD9D0 !important; }

  #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── 세션 초기화 ──────────────────────────────────────────────────
for k, v in [
    ("page", "start"),      # "start" | "main"
    ("user", None),         # 로그인된 user dict 또는 None
    ("messages", []),
    ("traces", []),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ════════════════════════════════════════════════════════════════
# 시작 화면 (로그인 / 비로그인 선택)
# ════════════════════════════════════════════════════════════════
if st.session_state["page"] == "start":
    st.markdown("""
    <div style="text-align:center;padding:60px 20px 0;">
      <div style="font-size:3rem;margin-bottom:12px;">🤖</div>
      <h1 style="font-size:1.8rem;font-weight:700;color:#3A3228;margin-bottom:6px;">청년정책 Agentic RAG</h1>
      <p style="color:#7C6E5A;font-size:14px;">정보 부족 시 스스로 검색하는 지능형 AI</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("**시작하기**")
        st.markdown("<p>로그인하면 맞춤 추천 + 이메일 알림을 받을 수 있습니다.</p>", unsafe_allow_html=True)

        tab_login, tab_register, tab_guest = st.tabs(["로그인", "회원가입", "비로그인"])

        # ── 로그인 ──
        with tab_login:
            email_in = st.text_input("이메일", key="login_email", placeholder="example@gmail.com")
            if st.button("로그인", use_container_width=True, key="btn_login"):
                u = user_db.get_user(email_in.strip())
                if u:
                    st.session_state["user"] = u
                    st.session_state["page"] = "main"
                    st.rerun()
                else:
                    st.error("등록된 이메일이 없습니다. 회원가입해주세요.")

        # ── 회원가입 ──
        with tab_register:
            r_name   = st.text_input("이름",   key="reg_name")
            r_email  = st.text_input("이메일", key="reg_email", placeholder="example@gmail.com")
            r_age    = st.number_input("나이",  min_value=15, max_value=39, value=24, key="reg_age")
            r_region = st.selectbox("거주 지역", ["서울", "경기", "인천", "부산", "대구", "대전",
                                                   "광주", "울산", "세종", "강원", "충북", "충남",
                                                   "전북", "전남", "경북", "경남", "제주"], key="reg_region")
            r_interval = st.selectbox("알림 주기", ["weekly", "daily"], key="reg_interval")
            r_allow  = st.checkbox("이메일 정책 알림 수신 동의", value=True, key="reg_allow")
            if st.button("회원가입", use_container_width=True, key="btn_register"):
                if not r_name or not r_email:
                    st.warning("이름과 이메일을 입력해주세요.")
                else:
                    user_db.register_user(
                        name=r_name, email=r_email.strip(),
                        age=r_age, region=r_region,
                        email_allowed=r_allow, interval=r_interval,
                    )
                    u = user_db.get_user(r_email.strip())
                    st.session_state["user"] = u
                    st.session_state["page"] = "main"
                    st.rerun()

        # ── 비로그인 ──
        with tab_guest:
            st.info("로그인 없이 챗봇만 이용합니다. 이메일 알림은 받을 수 없습니다.")
            if st.button("비로그인으로 시작", use_container_width=True, key="btn_guest"):
                st.session_state["user"] = None
                st.session_state["page"] = "main"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()


# ════════════════════════════════════════════════════════════════
# 메인 앱
# ════════════════════════════════════════════════════════════════
user = st.session_state.get("user")

# ── 상단 헤더 ────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([5, 1])
with col_h1:
    greeting = f"안녕하세요, **{user['name']}**님! 👋" if user else "**청년정책 Agentic RAG** 🤖"
    st.markdown(f"<h2 style='margin:16px 0 4px;font-size:1.3rem;color:#3A3228;'>{greeting}</h2>", unsafe_allow_html=True)
with col_h2:
    if st.button("← 로그아웃" if user else "← 처음으로", use_container_width=True):
        st.session_state["page"] = "start"
        st.session_state["user"] = None
        st.session_state["messages"] = []
        st.session_state["traces"]   = []
        st.rerun()

# ── 탭 구성 ─────────────────────────────────────────────────────
if user:
    tab_chat, tab_category, tab_profile, tab_log = st.tabs(["💬 챗봇", "📂 카테고리", "👤 내 프로필", "📧 알림 이력"])
else:
    tab_chat, tab_category = st.tabs(["💬 챗봇", "📂 카테고리"])
    tab_profile = tab_log = None

# ════════════════════════════════════════════════════════════════
# Tab 1: 챗봇
# ════════════════════════════════════════════════════════════════
TRACE_NODE_CLASS = {
    "agent_node":       "bg-blue",
    "search_tool_node": "bg-green",
    "grade_docs_node":  "bg-orange",
    "rewrite_node":     "bg-orange",
    "generate_node":    "bg-green",
}

with tab_chat:
    # 로그인된 경우 프로필 힌트
    if user:
        st.markdown(
            f"<div style='background:#F0EDE7;border-radius:8px;padding:8px 16px;font-size:12px;"
            f"color:#6B5F52;margin-bottom:12px;'>🧑 프로필 자동 반영 중 — "
            f"{user['age']}세 · {user['region']} · {user['email']}</div>",
            unsafe_allow_html=True,
        )

    # ── 카테고리 빠른 탐색 ──────────────────────────────────────────
    @st.cache_data(ttl=300)
    def _cat_stats():
        return get_category_stats()

    cat_stats = _cat_stats()
    CATEGORY_QUESTIONS = {
        "장학금":   "국가장학금이나 학자금 지원 받을 수 있는 조건 알려줘",
        "금융":     "청년도약계좌나 금융 지원 정책 추천해줘",
        "주거":     "청년 월세 지원이나 주거 지원 정책 알려줘",
        "취업":     "취업 준비생이 받을 수 있는 지원 정책 추천해줘",
        "창업":     "청년 창업 지원 정책 어떤 게 있어?",
        "건강문화": "청년 건강, 문화, 여가 관련 지원 정책 알려줘",
        "참여":     "청년 위원회나 네트워크 참여 프로그램 알려줘",
        "복지":     "청년 생활 지원, 복지 혜택 알려줘",
    }

    st.markdown(
        "<div style='font-size:12px;color:#8B7355;font-weight:600;margin-bottom:6px;'>카테고리별 탐색</div>",
        unsafe_allow_html=True,
    )
    cat_cols = st.columns(len(CATEGORY_QUESTIONS))
    for i, (cat, question) in enumerate(CATEGORY_QUESTIONS.items()):
        with cat_cols[i]:
            if st.button(
                cat,
                key=f"cat_{cat}",
                use_container_width=True,
                help=question,
            ):
                st.session_state["_pending_question"] = question

    st.markdown("<hr style='border:none;border-top:1px solid #E8E4DC;margin:10px 0;'>", unsafe_allow_html=True)

    # 카테고리 버튼 클릭 시 질문 자동 전송
    if "_pending_question" in st.session_state:
        pending = st.session_state.pop("_pending_question")
        full_q = f"[나이:{user['age']}세, 지역:{user['region']}] {pending}" if user else pending
        st.session_state["messages"].append({"role": "user", "content": pending})
        with st.spinner("에이전트가 판단 중..."):
            result = run(full_q)
        answer = result.get("answer", "답변을 생성하지 못했습니다.")
        trace  = result.get("execution_trace", [])
        retry  = result.get("retry_count", 0)
        if retry > 0:
            rewritten = result.get("rewritten_question", "")
            answer = f"_(검색 쿼리를 {retry}회 개선: **{rewritten}**)_\n\n" + answer
        st.session_state["messages"].append({"role": "assistant", "content": answer})
        st.session_state["traces"].append(trace)
        st.rerun()

    # 초기 화면
    if not st.session_state["messages"]:
        st.markdown("""
        <div style="text-align:center;padding:40px 20px;color:#9B8E7E;">
          <div style="font-size:2.5rem;margin-bottom:12px;">🔍</div>
          <div style="font-size:1rem;font-weight:600;color:#5A4F44;margin-bottom:8px;">무엇이든 물어보세요</div>
          <div style="font-size:13px;line-height:1.9;">
            "청년도약계좌 조건이 어떻게 돼?"<br>
            "서울 22살 취업 준비생이 받을 수 있는 정책은?"<br>
            "청년내일채움공제랑 청년도약계좌 같이 가입 가능해?"
          </div>
        </div>
        """, unsafe_allow_html=True)

    # 대화 렌더링
    for i, msg in enumerate(st.session_state["messages"]):
        role    = msg["role"]
        content = msg["content"]
        if role == "user":
            st.markdown(f"""
            <div class="msg-row user">
              <div class="avatar">나</div>
              <div class="bubble user">{content}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-row">
              <div class="avatar">🤖</div>
              <div class="bubble ai">{content}</div>
            </div>""", unsafe_allow_html=True)
            if i < len(st.session_state["traces"]):
                trace = st.session_state["traces"][i]
                if trace:
                    steps = ""
                    for s in trace:
                        node  = s.get("node", "")
                        cls   = TRACE_NODE_CLASS.get(node, "bg-blue")
                        steps += (f'<div class="trace-step">'
                                  f'<span class="badge-node {cls}">{node}</span>'
                                  f'<span>{s.get("summary","")}</span></div>')
                    st.markdown(
                        f'<div class="trace-box"><div style="font-weight:700;font-size:11px;'
                        f'color:#8B7355;margin-bottom:6px;">⚙ 실행 추적 (Agentic RAG)</div>{steps}</div>',
                        unsafe_allow_html=True,
                    )

    # 입력
    if prompt := st.chat_input("청년정책에 대해 질문하세요..."):
        # 로그인 사용자면 프로필 맥락 주입
        if user:
            full_prompt = f"[나이:{user['age']}세, 지역:{user['region']}] {prompt}"
        else:
            full_prompt = prompt

        st.session_state["messages"].append({"role": "user", "content": prompt})

        with st.spinner("에이전트가 판단 중..."):
            result = run(full_prompt)

        answer = result.get("answer", "답변을 생성하지 못했습니다.")
        trace  = result.get("execution_trace", [])
        retry  = result.get("retry_count", 0)

        if retry > 0:
            rewritten = result.get("rewritten_question", "")
            answer = f"_(검색 쿼리를 {retry}회 개선: **{rewritten}**)_\n\n" + answer

        st.session_state["messages"].append({"role": "assistant", "content": answer})
        st.session_state["traces"].append(trace)
        st.rerun()


# ════════════════════════════════════════════════════════════════
# Tab 2: 카테고리 탐색
# ════════════════════════════════════════════════════════════════
CAT_COLOR = {
    "금융":     "#5C7FD4",
    "취업":     "#5C9E62",
    "주거":     "#5AAFC4",
    "장학금":   "#9B5CD4",
    "창업":     "#D4855C",
    "건강문화": "#C45A8A",
    "참여":     "#8B7355",
    "복지":     "#6B8E6B",
}

with tab_category:
    @st.cache_data(ttl=300)
    def _all_docs_cached():
        return _load_all_docs()

    all_docs = _all_docs_cached()
    cat_stats = get_category_stats()

    # 선택된 카테고리 상태
    if "selected_cat" not in st.session_state:
        st.session_state["selected_cat"] = None

    selected = st.session_state["selected_cat"]

    # ── 카테고리 그리드 ───────────────────────────────────────────
    st.markdown(
        "<div style='font-size:13px;color:#5A4F44;margin-bottom:14px;'>"
        "카테고리를 선택하면 해당 정책 목록을 볼 수 있어요.</div>",
        unsafe_allow_html=True,
    )

    cat_cols = st.columns(4)
    cat_order = ["금융", "취업", "주거", "장학금", "창업", "건강문화", "참여", "복지"]
    for i, cat in enumerate(cat_order):
        is_sel = selected == cat
        with cat_cols[i % 4]:
            if st.button(
                f"{'▶ ' if is_sel else ''}{cat}",
                key=f"catbtn_{cat}",
                use_container_width=True,
            ):
                st.session_state["selected_cat"] = None if selected == cat else cat
                st.rerun()

    st.markdown("<hr style='border:none;border-top:1px solid #E8E4DC;margin:14px 0;'>", unsafe_allow_html=True)

    # ── 선택된 카테고리 정책 목록 ─────────────────────────────────
    if selected:
        color  = CAT_COLOR.get(selected, "#8B7355")
        emoji  = CATEGORY_EMOJI.get(selected, "📌")
        docs   = [d for d in all_docs if d["category"] == selected]

        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:14px;'>"
            f"<span style='background:{color};color:#fff;border-radius:20px;padding:4px 16px;"
            f"font-size:14px;font-weight:700;'>{emoji} {selected}</span>"
            f"<span style='color:#8B7355;font-size:13px;'>총 {len(docs)}개 정책</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # 검색 필터
        search_q = st.text_input("🔍 이름으로 검색", placeholder="예: 청년도약, 월세, 자격증...",
                                  key="cat_search", label_visibility="collapsed")
        if search_q:
            docs = [d for d in docs if search_q.lower() in d["title"].lower()]
            st.caption(f"'{search_q}' 검색 결과: {len(docs)}개")

        # 정책 카드 목록
        for doc in docs:
            title   = doc["title"]
            content = doc["content"].strip()
            preview = ""
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    preview = line[:80]
                    break

            with st.expander(f"**{title}**" + (f"  —  {preview}..." if preview else "")):
                col_content, col_btn = st.columns([4, 1])
                with col_content:
                    st.markdown(
                        f"<div style='font-size:13px;color:#3A3228;line-height:1.7;"
                        f"white-space:pre-wrap;'>{content[:600]}"
                        f"{'...' if len(content)>600 else ''}</div>",
                        unsafe_allow_html=True,
                    )
                with col_btn:
                    if st.button("💬 질문하기", key=f"ask_{title[:20]}", use_container_width=True):
                        question = f"{title}에 대해 자세히 알려줘"
                        st.session_state["messages"].append({"role": "user", "content": question})
                        full_q = f"[나이:{user['age']}세, 지역:{user['region']}] {question}" if user else question
                        with st.spinner("검색 중..."):
                            result = run(full_q)
                        answer = result.get("answer", "답변을 생성하지 못했습니다.")
                        trace  = result.get("execution_trace", [])
                        st.session_state["messages"].append({"role": "assistant", "content": answer})
                        st.session_state["traces"].append(trace)
                        st.session_state["selected_cat"] = None
                        st.rerun()
    else:
        # 선택 전 전체 통계 표시
        st.markdown(
            "<div style='text-align:center;padding:30px 20px;color:#9B8E7E;'>"
            "<div style='font-size:2rem;margin-bottom:8px;'>📂</div>"
            "<div style='font-size:14px;font-weight:600;color:#5A4F44;margin-bottom:6px;'>카테고리를 선택해서 정책을 탐색하세요</div>"
            f"<div style='font-size:13px;'>전체 {sum(cat_stats.values())}개 정책 · {len(cat_stats)}개 카테고리</div>"
            "</div>",
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════
# Tab 3: 내 프로필
# ════════════════════════════════════════════════════════════════
if tab_profile and user:
    with tab_profile:
        st.markdown("<br>", unsafe_allow_html=True)

        # ── 정보 수정 ──
        st.markdown('<div class="profile-card"><h4>📋 기본 정보 수정</h4>', unsafe_allow_html=True)
        p_name   = st.text_input("이름",   value=user["name"],   key="p_name")
        p_age    = st.number_input("나이", min_value=15, max_value=39, value=user["age"], key="p_age")
        p_region = st.selectbox("거주 지역",
                                ["서울", "경기", "인천", "부산", "대구", "대전",
                                 "광주", "울산", "세종", "강원", "충북", "충남",
                                 "전북", "전남", "경북", "경남", "제주"],
                                index=["서울", "경기", "인천", "부산", "대구", "대전",
                                       "광주", "울산", "세종", "강원", "충북", "충남",
                                       "전북", "전남", "경북", "경남", "제주"].index(user["region"])
                                if user["region"] in ["서울", "경기", "인천", "부산", "대구", "대전",
                                                      "광주", "울산", "세종", "강원", "충북", "충남",
                                                      "전북", "전남", "경북", "경남", "제주"] else 0,
                                key="p_region")
        if st.button("저장", key="btn_save_profile"):
            user_db.update_user(email=user["email"], name=p_name, age=p_age, region=p_region)
            st.session_state["user"] = user_db.get_user(user["email"])
            st.success("저장되었습니다.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # ── 이메일 수신 설정 ──
        st.markdown('<div class="profile-card"><h4>📧 이메일 알림 설정</h4>', unsafe_allow_html=True)
        current_allowed = bool(user.get("email_allowed", 1))
        new_allowed = st.toggle("이메일 정책 알림 수신", value=current_allowed, key="toggle_email")
        if new_allowed != current_allowed:
            user_db.update_email_allowed(user["email"], new_allowed)
            st.session_state["user"] = user_db.get_user(user["email"])
            st.rerun()

        st.caption(f"알림 주기: **{user.get('notify_interval', 'weekly')}** | "
                   f"마지막 알림: {user.get('last_notified') or '없음'}")
        st.markdown("</div>", unsafe_allow_html=True)

        # ── 즉시 알림 테스트 ──
        st.markdown('<div class="profile-card"><h4>🚀 즉시 알림 테스트</h4>', unsafe_allow_html=True)
        st.caption("Agentic RAG가 지금 바로 맞춤 정책을 검색해서 이메일로 발송합니다.")
        if st.button("지금 바로 이메일 받기", use_container_width=True, key="btn_test_notify"):
            with st.spinner("Agentic RAG 실행 중..."):
                run_notify(
                    name=user["name"], email=user["email"],
                    age=user["age"],   region=user["region"],
                    send_notification=True,
                )
            st.success(f"✅ {user['email']} 으로 발송 완료!")
        st.markdown("</div>", unsafe_allow_html=True)

        # ── 회원 탈퇴 ──
        with st.expander("⚠ 회원 탈퇴"):
            if st.button("탈퇴하기", key="btn_delete"):
                user_db.delete_user(user["email"])
                st.session_state["page"] = "start"
                st.session_state["user"] = None
                st.rerun()


# ════════════════════════════════════════════════════════════════
# Tab 3: 알림 이력
# ════════════════════════════════════════════════════════════════
if tab_log and user:
    with tab_log:
        st.markdown("<br>", unsafe_allow_html=True)
        logs = user_db.get_notification_log(user["email"], limit=10)
        if not logs:
            st.info("아직 발송된 알림이 없습니다.")
        else:
            st.caption(f"최근 {len(logs)}건의 알림 이력")
            for log in logs:
                import json
                try:
                    titles = json.loads(log.get("policies", "[]"))
                except Exception:
                    titles = []
                preview = titles[0][:80] + "..." if titles else "내용 없음"
                st.markdown(
                    f'<div class="log-item">'
                    f'<div class="log-time">📅 {log["sent_at"]}</div>'
                    f'{preview}</div>',
                    unsafe_allow_html=True,
                )
