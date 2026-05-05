"""
app.py
──────
week10 청년정책 알림 에이전트 — Streamlit UI

흐름:
  1. 로그인/회원가입 페이지 (이름·이메일·나이·지역·이메일수신허용)
  2. 로그인 성공 → 메인 앱
       Tab 챗봇    : 사용자 프로필 자동 반영 맞춤 정책 상담
       Tab 내 프로필: 정보 수정 + 이메일 수신 허용/거부 토글
       Tab 그래프   : LangGraph 구조 시각화

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
    page_title="청년정책 AI",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp { background:#f7f7f7; }
.stApp, .stApp p, .stApp span, .stApp div,
.stApp li, .stApp h1, .stApp h2, .stApp h3,
.stApp label, .stApp strong { color:#1a1a1a !important; }
[data-testid="stChatMessage"] * { color:#1a1a1a !important; }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid #e0e0e0; }
[data-testid="stSidebar"] * { color:#1a1a1a !important; }

/* 사이드바 입력 필드 글자색 */
[data-testid="stSidebar"] input { color:#ffffff !important; }
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] span { color:#ffffff !important; }
[data-testid="stSidebar"] .stNumberInput input { color:#ffffff !important; }

.login-box {
    max-width:480px; margin:60px auto 0; background:#fff;
    border-radius:10px; padding:40px; box-shadow:0 2px 12px rgba(0,0,0,.08);
}
.header { text-align:center; padding:0.5rem 0 1rem; }
.header h1 { font-size:1.8rem; font-weight:700; }
.header p  { font-size:0.9rem; color:#555 !important; }

.node-badge {
    display:inline-block; border-radius:3px;
    padding:0.2rem 0.6rem; font-size:0.78rem; margin:0.1rem;
    font-family:monospace; background:#e5e7eb; color:#374151 !important;
}
.node-badge.done { background:#16a34a; color:#fff !important; }

.profile-card {
    background:#fff; border-radius:8px; padding:18px 24px;
    border:1px solid #e5e7eb; margin-bottom:12px;
}

.stButton > button {
    background:#fff !important; color:#1a1a1a !important;
    border:1px solid #ccc !important; border-radius:4px !important;
}
.stTabs [aria-selected="true"] {
    background:#1a1a1a !important; color:#fff !important;
}
/* 탭 글자 — 선택/미선택 모두 흰색 */
.stTabs [data-baseweb="tab"] * { color:#ffffff !important; }
.stTabs [data-baseweb="tab-list"] { background:#1a1a1a !important; border-radius:6px 6px 0 0; }
.stTabs [aria-selected="true"]  { background:#4a4a4a !important; }
.stTabs [aria-selected="false"] { background:#1a1a1a !important; }

/* 입력 필드 글자 흰색 */
input { color:#ffffff !important; }
.stSelectbox div[data-baseweb="select"] span { color:#ffffff !important; }
.stRadio label p { color:#1a1a1a !important; }
.stCheckbox label p { color:#1a1a1a !important; }
.stFormSubmitButton button { color:#ffffff !important; }
</style>
""", unsafe_allow_html=True)

REGIONS = [
    "서울", "경기", "인천", "부산", "대구", "광주", "대전",
    "울산", "세종", "강원", "충북", "충남", "전북", "전남",
    "경북", "경남", "제주",
]

NODE_META = {
    "chat_parse_node":     {"icon": "🔍", "label": "질문 분석"},
    "chat_profile_node":   {"icon": "👤", "label": "프로필 반영"},
    "chat_search_node":    {"icon": "📄", "label": "정책 검색"},
    "chat_recommend_node": {"icon": "✨", "label": "맞춤 답변"},
    "profile_build_node":  {"icon": "👤", "label": "조건 분석"},
    "search_node":         {"icon": "📄", "label": "정책 검색"},
    "match_node":          {"icon": "🔎", "label": "조건 매칭"},
    "notify_node":         {"icon": "📧", "label": "이메일 발송"},
}

EXAMPLES = [
    "나한테 맞는 정책 추천해줘",
    "청년도약계좌 신청 자격이 어떻게 돼?",
    "취업 준비 중인데 받을 수 있는 지원 알려줘",
    "청년 월세 지원 어떻게 신청해?",
    "장학금 종류가 어떤 게 있어?",
]

# ── 스케줄러 (1회만 초기화) ──────────────────────────────────────
@st.cache_resource
def _init_scheduler():
    try:
        from scheduler import get_scheduler
        return get_scheduler()
    except Exception as e:
        print(f"[scheduler] 초기화 실패: {e}")
        return None

_init_scheduler()

# ════════════════════════════════════════════════════════════════
# 로그인 / 회원가입 페이지
# ════════════════════════════════════════════════════════════════

def show_login_page():
    import user_db as db

    st.markdown("""
    <div class="header" style="margin-top:40px">
        <h1>청년정책 AI</h1>
        <p>나이·지역을 등록하면 맞춤 정책을 챗봇이 안내하고<br>이메일로 자동 알림을 보내드립니다.</p>
    </div>
    """, unsafe_allow_html=True)

    col_center = st.columns([1, 2, 1])[1]

    with col_center:

        # ── 비로그인 바로 시작 ───────────────────────────────────
        st.markdown("")
        if st.button("비로그인으로 바로 시작", use_container_width=True, type="primary"):
            st.session_state["user"]     = {"guest": True, "name": "게스트"}
            st.session_state["messages"] = []
            st.rerun()

        st.markdown("<div style='text-align:center;color:#aaa;margin:12px 0'>── 또는 ──</div>",
                    unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["기존 회원 로그인", "신규 회원가입"])

        # ── 로그인 ──────────────────────────────────────────────
        with tab_login:
            st.markdown("")
            login_email = st.text_input("이메일", placeholder="example@gmail.com", key="login_email")
            if st.button("로그인", use_container_width=True, key="login_btn"):
                if not login_email or "@" not in login_email:
                    st.error("올바른 이메일을 입력해주세요.")
                else:
                    user = db.get_user(login_email.strip())
                    if user:
                        st.session_state["user"] = user
                        st.session_state["messages"] = []
                        st.rerun()
                    else:
                        st.error("등록되지 않은 이메일입니다. 회원가입 탭을 이용해주세요.")

        # ── 회원가입 ────────────────────────────────────────────
        with tab_register:
            st.markdown("")
            with st.form("register_form"):
                r_name    = st.text_input("이름 *", placeholder="홍길동")
                r_email   = st.text_input("이메일 *", placeholder="example@gmail.com")
                r_age     = st.number_input("나이 *", min_value=15, max_value=39, value=25)
                r_region  = st.selectbox("지역 *", REGIONS)
                r_allowed = st.checkbox(
                    "이메일 수신 허용",
                    value=True,
                    help="체크하면 매주 맞춤 정책을 이메일로 받습니다.",
                )
                r_interval = st.radio(
                    "알림 주기",
                    ["weekly", "daily"],
                    format_func=lambda x: "주 1회" if x == "weekly" else "매일",
                    horizontal=True,
                    disabled=not r_allowed,
                )
                submitted = st.form_submit_button("가입 완료", use_container_width=True)

            if submitted:
                if not r_name or not r_email:
                    st.error("이름과 이메일은 필수입니다.")
                elif "@" not in r_email:
                    st.error("올바른 이메일 주소를 입력해주세요.")
                else:
                    db.register_user(
                        name=r_name.strip(),
                        email=r_email.strip(),
                        age=r_age,
                        region=r_region,
                        email_allowed=r_allowed,
                        interval=r_interval,
                    )
                    user = db.get_user(r_email.strip())
                    st.session_state["user"]     = user
                    st.session_state["messages"] = []
                    st.success(f"{r_name}님, 환영합니다!")
                    st.rerun()


# ════════════════════════════════════════════════════════════════
# 메인 앱 (로그인된 상태)
# ════════════════════════════════════════════════════════════════

def show_main_app():
    import user_db as db

    user = st.session_state["user"]

    # ── 사이드바 ──────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"### {user['name']}님")
        st.markdown(f"**나이**: {user['age']}세")
        st.markdown(f"**지역**: {user['region']}")
        if user.get("email_allowed"):
            st.success("이메일 수신 ON")
        else:
            st.warning("이메일 수신 OFF")
        st.markdown("---")

        # ── 최신 정책 자동 수집 ────────────────────────────────
        from tools.web_searcher import has_tavily_key, fetch_latest_policies, get_web_meta
        from tools.policy_fetcher import has_api_key, fetch_and_save, get_fetch_meta

        st.markdown("#### 최신 정책 자동 수집")

        # Tavily 웹 검색 (실시간)
        if has_tavily_key():
            web_meta = get_web_meta()
            if web_meta:
                st.caption(f"웹 검색: {web_meta['fetched_at'][:10]} ({web_meta['count']}개)")
            if st.button("실시간 웹 검색", use_container_width=True,
                         key="web_fetch_btn", type="primary"):
                with st.spinner("최신 청년정책 웹 검색 중... (약 30초)"):
                    new_docs = fetch_latest_policies(
                        age=user["age"],
                        region=user["region"],
                    )
                    import tools.policy_loader as _pl
                    _pl._doc_cache = None
                if new_docs:
                    st.success(f"웹에서 {len(new_docs)}개 정책 수집!")
                else:
                    st.warning("수집 결과 없음")
        else:
            st.caption("Tavily: .env에 TAVILY_API_KEY 입력시 실시간 검색")

        # 공공데이터포털 API
        if has_api_key():
            pub_meta = get_fetch_meta()
            if pub_meta:
                st.caption(f"공공API: {pub_meta['fetched_at'][:10]} ({pub_meta['count']}개)")
            if st.button("공공데이터 수집", use_container_width=True,
                         key="fetch_btn"):
                with st.spinner(f"{user['region']} 지역 정책 수집 중..."):
                    new_docs = fetch_and_save(
                        age=user["age"], region=user["region"], max_count=200,
                    )
                    import tools.policy_loader as _pl
                    _pl._doc_cache = None
                st.success(f"{len(new_docs)}개 수집 완료!" if new_docs else "결과 없음")
        else:
            st.caption("공공데이터포털: .env에 PUBLIC_DATA_API_KEY 입력시 사용")

        st.markdown("---")

        # ── RAG 벡터 DB 상태 ──────────────────────────────────
        from tools.embedder import is_store_built, get_store_stats, build_vector_store
        from tools.policy_loader import get_all_docs
        from tools.policy_fetcher import get_fetched_docs

        st.markdown("#### RAG 벡터 DB")
        stats = get_store_stats()
        fetched_count = len(get_fetched_docs())
        if stats["built"]:
            st.success(
                f"빌드 완료\n"
                f"- 문서 {stats['doc_count']}개 "
                f"(수집 {fetched_count}개 포함)\n"
                f"- 청크 {stats['chunk_count']}개\n"
                f"- {stats['file_size_kb']} KB"
            )
            if st.button("재빌드", use_container_width=True, key="rebuild_btn"):
                with st.spinner("임베딩 생성 중... (약 10~30초)"):
                    build_vector_store(get_all_docs())
                st.success("재빌드 완료!")
                st.rerun()
        else:
            st.warning("벡터 DB 없음\n(키워드 검색 사용 중)")
            if st.button("벡터 DB 빌드", use_container_width=True,
                         key="build_btn", type="primary"):
                with st.spinner("정책 문서 임베딩 중... (약 10~30초)"):
                    build_vector_store(get_all_docs())
                st.success("빌드 완료! 이제 RAG 검색을 사용합니다.")
                st.rerun()

        st.markdown("---")

        # 예시 질문
        st.markdown("#### 예시 질문")
        for ex in EXAMPLES:
            if st.button(ex, use_container_width=True, key=f"ex_{ex}"):
                st.session_state["pending_query"] = ex
                st.rerun()

        st.markdown("---")
        if st.button("로그아웃", use_container_width=True):
            del st.session_state["user"]
            del st.session_state["messages"]
            st.rerun()

    # ── 헤더 ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="header">
        <h1>청년정책 AI</h1>
        <p>{user['name']}님({user['age']}세 · {user['region']}) 맞춤 정책 상담 및 자동 알림</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    tab_chat, tab_profile, tab_graph = st.tabs(["챗봇 상담", "내 프로필", "그래프 구조"])

    # ════════════════════════════════════════════════════════════
    # TAB 1: 챗봇 상담
    # ════════════════════════════════════════════════════════════
    with tab_chat:
        from graph import run_chat

        # 세션 메시지 초기화
        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        if "running" not in st.session_state:
            st.session_state["running"] = False

        # 프로필 안내 배너
        st.info(
            f"나이({user['age']}세)·지역({user['region']}) 정보가 자동으로 반영됩니다. "
            "자유롭게 청년정책에 대해 질문해보세요.",
            icon=None,
        )

        # 이전 대화 출력
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                if msg["role"] == "user":
                    st.markdown(msg["content"])
                else:
                    if msg.get("trace"):
                        with st.expander("실행 추적", expanded=False):
                            for step in msg["trace"]:
                                meta = NODE_META.get(step["node"], {"icon": "🔧", "label": step["node"]})
                                st.markdown(
                                    f'<span class="node-badge done">{meta["icon"]} {meta["label"]}</span>'
                                    f'<span style="font-size:0.8rem;margin-left:8px">{step["summary"]}</span>',
                                    unsafe_allow_html=True,
                                )
                    st.markdown(msg["content"])

        # 입력 처리
        pending    = st.session_state.pop("pending_query", None)
        user_input = st.chat_input(
            "청년정책에 대해 무엇이든 물어보세요",
            disabled=st.session_state["running"],
        ) or pending

        if user_input and not st.session_state["running"]:
            st.session_state["running"] = True
            st.session_state["messages"].append({"role": "user", "content": user_input})

            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("AI가 정책을 검색하고 있습니다..."):
                    try:
                        # 로그인된 사용자 프로필을 자동 주입
                        final_state = run_chat(
                            user_query=user_input,
                            logged_in_user=user,
                        )
                        recommendation = final_state.get("recommendation", "")
                        last_trace     = final_state.get("execution_trace", [])

                        if last_trace:
                            with st.expander("실행 추적", expanded=False):
                                for step in last_trace:
                                    meta = NODE_META.get(step["node"], {"icon": "🔧", "label": step["node"]})
                                    st.markdown(
                                        f'<span class="node-badge done">{meta["icon"]} {meta["label"]}</span>'
                                        f'<span style="font-size:0.8rem;margin-left:8px">{step["summary"]}</span>',
                                        unsafe_allow_html=True,
                                    )

                        if recommendation:
                            st.markdown(recommendation)
                        else:
                            st.warning("답변을 생성하지 못했습니다. 다시 시도해주세요.")

                    except Exception as e:
                        import traceback
                        last_trace     = []
                        recommendation = ""
                        st.error(f"오류: {e}")
                        st.code(traceback.format_exc())

            st.session_state["messages"].append({
                "role":    "assistant",
                "content": recommendation,
                "trace":   last_trace,
            })
            st.session_state["running"] = False

        # 첫 방문 안내
        if not st.session_state["messages"]:
            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**{user['age']}세 맞춤 정책**\n"
                            "나이 조건을 자동으로 적용해 가장 적합한 정책을 찾아드립니다.")
            with c2:
                st.markdown(f"**{user['region']} 지역 필터**\n"
                            "지역 특화 정책과 전국 공통 정책을 함께 안내합니다.")
            with c3:
                st.markdown("**실시간 추적**\n"
                            "어떤 노드가 실행되었는지 각 단계별 결과를 확인할 수 있습니다.")

    # ════════════════════════════════════════════════════════════
    # TAB 2: 내 프로필
    # ════════════════════════════════════════════════════════════
    with tab_profile:
        # 최신 정보 갱신
        fresh_user = db.get_user(user["email"]) or user
        st.session_state["user"] = fresh_user
        user = fresh_user

        st.markdown("### 내 프로필")
        col_info, col_edit = st.columns([1, 1], gap="large")

        with col_info:
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown(f"**이름**: {user['name']}")
            st.markdown(f"**이메일**: {user['email']}")
            st.markdown(f"**나이**: {user['age']}세")
            st.markdown(f"**지역**: {user['region']}")
            st.markdown(f"**알림 주기**: {'주 1회' if user.get('notify_interval') == 'weekly' else '매일'}")
            last = user.get("last_notified") or "없음"
            st.markdown(f"**마지막 이메일**: {last}")
            st.markdown('</div>', unsafe_allow_html=True)

            # 이메일 수신 허용/거부 토글
            st.markdown("---")
            st.markdown("#### 이메일 알림 설정")
            allowed_now = bool(user.get("email_allowed"))
            new_allowed = st.toggle(
                "이메일 수신 허용",
                value=allowed_now,
                help="OFF 하면 자동 이메일이 발송되지 않습니다.",
            )
            if new_allowed != allowed_now:
                db.update_email_allowed(user["email"], new_allowed)
                st.session_state["user"] = db.get_user(user["email"])
                st.success("이메일 설정이 변경되었습니다.")
                st.rerun()

            if new_allowed:
                st.success("현재 이메일 알림이 켜져 있습니다.")
                # 즉시 발송 버튼
                if st.button("지금 바로 이메일 받기", use_container_width=True):
                    from graph import run_notify
                    with st.spinner("정책 검색 및 이메일 발송 중..."):
                        state = run_notify(
                            name=user["name"],
                            email=user["email"],
                            age=user["age"],
                            region=user["region"],
                            send_notification=True,
                        )
                    if state.get("email_sent"):
                        st.success(f"{user['email']}로 이메일을 발송했습니다!")
                    else:
                        st.warning("발송 실패. .env의 SMTP 설정을 확인하세요.")
            else:
                st.warning("현재 이메일 알림이 꺼져 있습니다.")

        with col_edit:
            st.markdown("#### 정보 수정")
            with st.form("edit_form"):
                e_name   = st.text_input("이름", value=user["name"])
                e_age    = st.number_input("나이", min_value=15, max_value=39, value=user["age"])
                e_region = st.selectbox(
                    "지역",
                    REGIONS,
                    index=REGIONS.index(user["region"]) if user["region"] in REGIONS else 0,
                )
                e_interval = st.radio(
                    "알림 주기",
                    ["weekly", "daily"],
                    index=0 if user.get("notify_interval") == "weekly" else 1,
                    format_func=lambda x: "주 1회" if x == "weekly" else "매일",
                    horizontal=True,
                )
                save_btn = st.form_submit_button("저장", use_container_width=True)

            if save_btn:
                db.update_user(user["email"], e_name, e_age, e_region)
                # interval 업데이트
                import sqlite3
                from pathlib import Path
                with sqlite3.connect(db.DB_PATH) as con:
                    con.execute(
                        "UPDATE users SET notify_interval=? WHERE email=?",
                        (e_interval, user["email"]),
                    )
                st.session_state["user"] = db.get_user(user["email"])
                st.success("정보가 저장되었습니다.")
                st.rerun()

            st.markdown("---")
            st.markdown("#### 발송 이력")
            logs = db.get_notification_log(user["email"], limit=5)
            if logs:
                import json as _json
                for log in logs:
                    policies = _json.loads(log.get("policies") or "[]")
                    with st.expander(f"{log['sent_at']}"):
                        if policies:
                            for p in policies:
                                st.markdown(f"- {p}")
                        else:
                            st.caption("정책 목록 없음")
            else:
                st.caption("발송 이력이 없습니다.")

            st.markdown("---")
            if st.button("회원 탈퇴", type="secondary"):
                db.delete_user(user["email"])
                del st.session_state["user"]
                del st.session_state["messages"]
                st.rerun()

    # ════════════════════════════════════════════════════════════
    # TAB 3: 그래프 구조
    # ════════════════════════════════════════════════════════════
    with tab_graph:
        from graph import chat_graph, notify_graph, get_chat_mermaid, get_notify_mermaid

        st.markdown("### LangGraph 워크플로우 구조")

        g_chat, g_notify = st.columns(2, gap="large")

        with g_chat:
            st.markdown("#### 챗봇 그래프")
            try:
                png = chat_graph.get_graph().draw_mermaid_png()
                st.image(png, caption="chat_graph")
            except Exception:
                pass
            st.code(get_chat_mermaid(), language="text")

        with g_notify:
            st.markdown("#### 알림 그래프")
            try:
                png = notify_graph.get_graph().draw_mermaid_png()
                st.image(png, caption="notify_graph")
            except Exception:
                pass
            st.code(get_notify_mermaid(), language="text")

        st.markdown("---")
        st.markdown("""
#### 노드 역할

| 그래프 | 노드 | 역할 |
|--------|------|------|
| 챗봇 | `chat_parse_node` | 질문 유형·카테고리·키워드 분석 |
| 챗봇 | `chat_profile_node` | 로그인 사용자 프로필 주입 또는 LLM 추출 |
| 챗봇 | `chat_search_node` | 정책 DB 키워드 검색 |
| 챗봇 | `chat_recommend_node` | GPT-4o 맞춤 답변 생성 |
| 알림 | `profile_build_node` | 나이·지역 → 검색 키워드 |
| 알림 | `search_node` | 정책 DB 검색 |
| 알림 | `match_node` | GPT-4o 조건 매칭 + HTML 본문 생성 |
| 알림 | `notify_node` | Gmail SMTP 발송 + DB 갱신 |
""")


# ════════════════════════════════════════════════════════════════
# 진입점
# ════════════════════════════════════════════════════════════════

def show_guest_app():
    """비로그인 챗봇 — 나이·지역 임시 입력 후 바로 상담."""
    from graph import run_chat

    # ── 사이드바 ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### 비로그인 모드")
        st.caption("나이·지역을 입력하면 더 정확한 추천을 받을 수 있습니다.")
        st.markdown("")

        g_age    = st.number_input("나이 (선택)", min_value=15, max_value=39,
                                   value=st.session_state.get("g_age", 25), key="g_age")
        g_region = st.selectbox("지역 (선택)", ["선택 안 함"] + REGIONS,
                                index=0, key="g_region")

        st.markdown("---")
        st.markdown("#### 예시 질문")
        for ex in EXAMPLES:
            if st.button(ex, use_container_width=True, key=f"gex_{ex}"):
                st.session_state["pending_query"] = ex
                st.rerun()

        st.markdown("---")
        if st.button("로그인 / 회원가입", use_container_width=True):
            del st.session_state["user"]
            st.session_state["messages"] = []
            st.rerun()

    # ── 헤더 ──────────────────────────────────────────────────
    st.markdown("""
    <div class="header">
        <h1>청년정책 AI</h1>
        <p>청년정책 무엇이든 물어보세요 · 비로그인 모드</p>
    </div>
    """, unsafe_allow_html=True)

    st.info("로그인하면 이메일 자동 알림·맞춤 추천 기능을 사용할 수 있습니다.", icon=None)
    st.markdown("---")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "running" not in st.session_state:
        st.session_state["running"] = False

    # 이전 대화 출력
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.markdown(msg["content"])
            else:
                if msg.get("trace"):
                    with st.expander("실행 추적", expanded=False):
                        for step in msg["trace"]:
                            meta = NODE_META.get(step["node"], {"icon": "🔧", "label": step["node"]})
                            st.markdown(
                                f'<span class="node-badge done">{meta["icon"]} {meta["label"]}</span>'
                                f'<span style="font-size:0.8rem;margin-left:8px">{step["summary"]}</span>',
                                unsafe_allow_html=True,
                            )
                st.markdown(msg["content"])

    # 입력
    pending    = st.session_state.pop("pending_query", None)
    user_input = st.chat_input(
        "청년정책에 대해 무엇이든 물어보세요",
        disabled=st.session_state["running"],
    ) or pending

    if user_input and not st.session_state["running"]:
        st.session_state["running"] = True
        st.session_state["messages"].append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("AI가 정책을 검색하고 있습니다..."):
                try:
                    # 나이·지역 임시 프로필 구성
                    region_val = g_region if g_region != "선택 안 함" else None
                    guest_profile = {}
                    if g_age:    guest_profile["age"]    = g_age
                    if region_val: guest_profile["region"] = region_val

                    final_state = run_chat(
                        user_query=user_input,
                        logged_in_user={"name": "게스트",
                                        "age":    g_age,
                                        "region": region_val or "",
                                        "email":  ""} if (g_age or region_val) else None,
                    )
                    recommendation = final_state.get("recommendation", "")
                    last_trace     = final_state.get("execution_trace", [])

                    if last_trace:
                        with st.expander("실행 추적", expanded=False):
                            for step in last_trace:
                                meta = NODE_META.get(step["node"], {"icon": "🔧", "label": step["node"]})
                                st.markdown(
                                    f'<span class="node-badge done">{meta["icon"]} {meta["label"]}</span>'
                                    f'<span style="font-size:0.8rem;margin-left:8px">{step["summary"]}</span>',
                                    unsafe_allow_html=True,
                                )
                    if recommendation:
                        st.markdown(recommendation)
                    else:
                        st.warning("답변을 생성하지 못했습니다. 다시 시도해주세요.")

                except Exception as e:
                    import traceback
                    last_trace     = []
                    recommendation = ""
                    st.error(f"오류: {e}")
                    st.code(traceback.format_exc())

        st.session_state["messages"].append({
            "role": "assistant", "content": recommendation, "trace": last_trace,
        })
        st.session_state["running"] = False


# ── 진입점 ────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state["user"] is None:
    show_login_page()
elif st.session_state["user"].get("guest"):
    show_guest_app()
else:
    show_main_app()
