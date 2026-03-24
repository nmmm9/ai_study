"""
6주차 Streamlit UI - 실제 서비스 스타일
백엔드: week05 AdvancedRAGPipeline
로그인/회원가입: Supabase Auth
채팅 저장: Supabase DB

실행: streamlit run app.py
"""

import os
import sys
import uuid
import json
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

sys.path.append(str(Path(__file__).resolve().parent))
from rag_pipeline import AdvancedRAGPipeline, DocumentLoader, extract_metadata_with_parents

from supabase import create_client
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 페이지 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="취업 상담 AI",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
/* ── 기본 ── */
#MainMenu, header, footer { visibility: hidden; }

.stApp { background: #171717; color: #ececec; }
.stApp p, .stApp span, .stApp div, .stApp li,
.stApp h1, .stApp h2, .stApp h3, .stApp label,
.stApp small, .stMarkdown, .stMarkdown * { color: #ececec !important; }

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li { color: #ececec !important; }

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: #111111;
    border-right: 1px solid #2a2a2a;
}
[data-testid="stSidebar"] * { color: #ececec !important; }

/* ── 메인 영역 ── */
.main .block-container {
    max-width: 820px;
    margin: 0 auto;
    padding-top: 2rem;
    padding-bottom: 7rem;
}

/* ── 채팅 입력창 ── */
[data-testid="stChatInput"] textarea {
    background: #2a2a2a !important;
    border: 1px solid #3a3a3a !important;
    border-radius: 16px !important;
    color: #ececec !important;
    font-size: 15px !important;
    padding: 14px 18px !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #10a37f !important;
    box-shadow: 0 0 0 3px rgba(16,163,127,0.15) !important;
}

/* ── 메시지 ── */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: #1e1e1e;
    border: 1px solid #2a2a2a;
    border-radius: 16px;
    padding: 14px 18px;
    margin-bottom: 12px;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    background: transparent;
    padding: 4px 0;
    margin-bottom: 4px;
}

/* ── 버튼 기본 ── */
.stButton button {
    background: #1e1e1e;
    color: #ececec !important;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    font-size: 13px;
    transition: all 0.18s ease;
    text-align: left;
}
.stButton button:hover {
    background: #2a2a2a !important;
    border-color: #3a3a3a !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

/* ── 새 채팅 버튼 ── */
.new-chat-btn button {
    background: linear-gradient(135deg, #10a37f, #0d8c6d) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px;
    box-shadow: 0 2px 8px rgba(16,163,127,0.3) !important;
}
.new-chat-btn button:hover {
    background: linear-gradient(135deg, #12b48d, #0f9b78) !important;
    box-shadow: 0 4px 16px rgba(16,163,127,0.4) !important;
}

/* ── 활성 대화 ── */
.chat-active button {
    background: #2a2a2a !important;
    border-color: #10a37f !important;
    border-left: 3px solid #10a37f !important;
}

/* ── 액션 버튼 (복사, 재생성, 피드백) ── */
.action-btn button {
    background: transparent !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #8e8ea0 !important;
    font-size: 12px !important;
    padding: 2px 8px !important;
    min-height: 28px !important;
}
.action-btn button:hover {
    background: #2a2a2a !important;
    color: #ececec !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ── 피드백 선택됨 ── */
.feedback-active button {
    background: rgba(16,163,127,0.15) !important;
    border-color: #10a37f !important;
    color: #10a37f !important;
}

/* ── 출처 카드 ── */
.source-card {
    background: #1e1e1e;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 10px 14px;
    margin: 4px 0;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: border-color 0.2s;
}
.source-card:hover { border-color: #10a37f; }
.source-num {
    background: #10a37f;
    color: white !important;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    flex-shrink: 0;
}
.source-text { color: #ececec !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #1e1e1e !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
}
[data-testid="stExpanderDetails"] { background: #1e1e1e !important; }

/* ── 입력 폼 ── */
.stTextInput input {
    background: #1e1e1e !important;
    color: #ececec !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
}
.stTextInput input:focus { border-color: #10a37f !important; }

/* ── 탭 ── */
[data-testid="stTab"] { color: #8e8ea0 !important; }
[aria-selected="true"] { color: #10a37f !important; border-bottom-color: #10a37f !important; }

/* ── 구분선 ── */
hr { border-color: #2a2a2a !important; margin: 12px 0 !important; }

/* ── 캡션 ── */
.stCaption, [data-testid="stCaptionContainer"] p { color: #8e8ea0 !important; font-size: 12px !important; }

/* ── 환영 화면 ── */
.welcome-title {
    font-size: 2.2rem;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(135deg, #ececec, #10a37f);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}
.welcome-sub {
    text-align: center;
    color: #8e8ea0 !important;
    font-size: 15px;
    margin-bottom: 40px;
}

/* ── 추천 카드 ── */
.stButton [data-testid="stBaseButton-secondary"] {
    background: #1e1e1e !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 14px !important;
    text-align: left !important;
    padding: 16px !important;
    height: auto !important;
    white-space: pre-wrap !important;
    line-height: 1.5 !important;
}

/* ── 상태 표시 ── */
.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #10a37f;
    border-radius: 50%;
    animation: pulse 1.2s ease-in-out infinite;
    margin-right: 6px;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.4; transform: scale(0.8); }
}

/* ── 로그인 화면 ── */
.auth-title {
    font-size: 2.2rem;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(135deg, #ececec 40%, #10a37f);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}
.auth-sub { text-align: center; color: #8e8ea0; margin-bottom: 28px; }

/* ── 토큰 배지 ── */
.token-badge {
    background: #1e1e1e;
    border: 1px solid #2a2a2a;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    color: #8e8ea0 !important;
    display: inline-block;
}

/* ── 공고 카드 ── */
.job-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 14px;
    padding: 14px 16px;
    margin: 6px 0;
    transition: border-color 0.2s, transform 0.15s;
}
.job-card:hover { border-color: #10a37f; transform: translateY(-1px); }
.job-card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.job-rank {
    background: linear-gradient(135deg, #10a37f, #0d8c6d);
    color: white !important;
    border-radius: 8px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 700;
    flex-shrink: 0;
}
.job-company { font-weight: 700; font-size: 14px; color: #ececec !important; }
.job-section {
    font-size: 12px;
    color: #10a37f !important;
    background: rgba(16,163,127,0.1);
    border-radius: 6px;
    padding: 2px 8px;
    margin-left: auto;
}
.job-snippet {
    font-size: 12px;
    color: #8e8ea0 !important;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.job-source { font-size: 11px; color: #555 !important; margin-top: 6px; }

/* ── 북마크 ── */
.bookmark-active button {
    background: rgba(255,193,7,0.15) !important;
    border-color: #ffc107 !important;
    color: #ffc107 !important;
}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 복사 버튼 컴포넌트 (JavaScript)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def copy_button(text: str, key: str):
    escaped = text.replace("\\", "\\\\").replace("`", "\\`").replace("\n", "\\n").replace('"', '\\"')
    components.html(f"""
    <button id="btn_{key}" onclick="
        navigator.clipboard.writeText(`{escaped}`).then(() => {{
            const b = document.getElementById('btn_{key}');
            b.textContent = '✓ 복사됨';
            b.style.color = '#10a37f';
            b.style.borderColor = '#10a37f';
            setTimeout(() => {{ b.textContent = '📋 복사'; b.style.color = '#8e8ea0'; b.style.borderColor = '#2a2a2a'; }}, 2000);
        }});
    " style="
        background: transparent;
        color: #8e8ea0;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 3px 10px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s;
        font-family: inherit;
    " onmouseover="this.style.background='#2a2a2a'; this.style.color='#ececec';"
       onmouseout="this.style.background='transparent'; this.style.color='#8e8ea0';">
        📋 복사
    </button>
    """, height=32)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Supabase Auth
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def auth_login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return res.user, None
    except Exception as e:
        return None, str(e)


def auth_signup(email, password):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        return res.user, None
    except Exception as e:
        return None, str(e)


def auth_logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.clear()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Supabase 채팅 히스토리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def load_history(user_id: str) -> dict:
    try:
        res = (supabase.table("conversations")
               .select("*").eq("user_id", user_id)
               .order("updated_at", desc=True).execute())
        convs = {}
        for row in res.data:
            convs[row["id"]] = {
                "title":      row["title"],
                "messages":   row["messages"],
                "created_at": row.get("created_at", "")[:16].replace("T", " "),
            }
        if not convs:
            cid = str(uuid.uuid4())
            convs[cid] = {"title": "새 대화", "messages": [], "created_at": datetime.now().strftime("%m/%d %H:%M")}
        return convs
    except Exception:
        cid = str(uuid.uuid4())
        return {cid: {"title": "새 대화", "messages": [], "created_at": datetime.now().strftime("%m/%d %H:%M")}}


def save_conversation(user_id: str, cid: str, conv: dict):
    try:
        supabase.table("conversations").upsert({
            "id":         cid,
            "user_id":    user_id,
            "title":      conv["title"],
            "messages":   conv["messages"],
            "updated_at": datetime.now().isoformat(),
        }).execute()
    except Exception:
        pass


def delete_conversation_db(cid: str):
    try:
        supabase.table("conversations").delete().eq("id", cid).execute()
    except Exception:
        pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 로그인 / 회원가입 화면
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown('<div class="auth-title">💼 취업 상담 AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-sub">AI 기반 취업공고 분석 서비스</div>', unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["로그인", "회원가입"])
        with tab_login:
            email    = st.text_input("이메일", key="login_email", placeholder="example@email.com")
            password = st.text_input("비밀번호", type="password", key="login_pw", placeholder="••••••••")
            if st.button("로그인", use_container_width=True, key="login_btn"):
                if email and password:
                    user, err = auth_login(email, password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error(f"로그인 실패: {err}")
                else:
                    st.warning("이메일과 비밀번호를 입력하세요.")

        with tab_signup:
            email    = st.text_input("이메일", key="signup_email", placeholder="example@email.com")
            password = st.text_input("비밀번호 (6자 이상)", type="password", key="signup_pw", placeholder="••••••••")
            if st.button("회원가입", use_container_width=True, key="signup_btn"):
                if email and password:
                    user, err = auth_signup(email, password)
                    if user:
                        st.success("✅ 가입 완료! 로그인 탭에서 로그인하세요.")
                    else:
                        st.error(f"가입 실패: {err}")
                else:
                    st.warning("이메일과 비밀번호를 입력하세요.")
    st.stop()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 파일 업로드 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UPLOADS_DIR    = Path(__file__).parent / "uploads"
BOOKMARKS_FILE = Path(__file__).parent / "bookmarks.json"


# ── 북마크 함수 ───────────────────────────────────────────────
def load_bookmarks() -> list[dict]:
    if BOOKMARKS_FILE.exists():
        try:
            return json.loads(BOOKMARKS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def save_bookmark(bid: str, question: str, answer: str, citations: list[str]):
    bms = load_bookmarks()
    if not any(b["id"] == bid for b in bms):
        bms.append({
            "id": bid, "question": question, "answer": answer,
            "citations": citations, "saved_at": datetime.now().strftime("%m/%d %H:%M"),
        })
        BOOKMARKS_FILE.write_text(json.dumps(bms, ensure_ascii=False, indent=2), encoding="utf-8")

def delete_bookmark(bid: str):
    bms = [b for b in load_bookmarks() if b["id"] != bid]
    BOOKMARKS_FILE.write_text(json.dumps(bms, ensure_ascii=False, indent=2), encoding="utf-8")

UPLOADS_DIR
UPLOADS_LIST = Path(__file__).parent / "uploaded_files.json"
UPLOADS_DIR.mkdir(exist_ok=True)

BASE_DOC = str(Path(__file__).resolve().parent / "job_postings.md")
CRAWLED_DOC = str(Path(__file__).parent / "job_postings_crawled.md")


def get_uploaded_file_list() -> list[str]:
    if UPLOADS_LIST.exists():
        try:
            return json.loads(UPLOADS_LIST.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_uploaded_file_list(files: list[str]) -> None:
    UPLOADS_LIST.write_text(json.dumps(files, ensure_ascii=False, indent=2), encoding="utf-8")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RAG 파이프라인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _build_pipeline(paths: list[str]) -> AdvancedRAGPipeline:
    pipeline   = AdvancedRAGPipeline()
    all_chunks = []
    for path in paths:
        if not Path(path).exists():
            continue
        raw    = DocumentLoader.load(path)
        chunks = extract_metadata_with_parents(raw, path, child_size=200, parent_size=600)
        all_chunks.extend(chunks)
    if all_chunks:
        pipeline.store.build(all_chunks)
    return pipeline


@st.cache_resource(show_spinner="AI 초기화 중...")
def get_pipeline(extra_files: tuple = ()) -> AdvancedRAGPipeline:
    base_docs = [BASE_DOC]
    if Path(CRAWLED_DOC).exists():
        base_docs.append(CRAWLED_DOC)
    return _build_pipeline(base_docs + list(extra_files))


def reload_pipeline():
    get_pipeline.clear()
    st.session_state._extra_files = tuple(get_uploaded_file_list())


if "_extra_files" not in st.session_state:
    st.session_state._extra_files = tuple(get_uploaded_file_list())

pipeline = get_pipeline(st.session_state._extra_files)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 세션 상태 초기화
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
user_id = st.session_state.user.id

if "conversations" not in st.session_state:
    st.session_state.conversations = load_history(user_id)
    st.session_state.current_chat  = list(st.session_state.conversations.keys())[0]

if "current_chat" not in st.session_state:
    st.session_state.current_chat = list(st.session_state.conversations.keys())[0]

if "pending_input"   not in st.session_state: st.session_state.pending_input   = None
if "editing_title"   not in st.session_state: st.session_state.editing_title   = None
if "regenerate"      not in st.session_state: st.session_state.regenerate      = False
if "filter_stack"    not in st.session_state: st.session_state.filter_stack    = ""
if "filter_career"   not in st.session_state: st.session_state.filter_career   = "전체"


def current_messages():
    return st.session_state.conversations[st.session_state.current_chat]["messages"]


def add_new_chat():
    cid  = str(uuid.uuid4())
    conv = {"title": "새 대화", "messages": [], "created_at": datetime.now().strftime("%m/%d %H:%M")}
    st.session_state.conversations[cid] = conv
    st.session_state.current_chat = cid
    save_conversation(user_id, cid, conv)
    pipeline.reset()


def delete_chat(cid: str):
    convs = st.session_state.conversations
    delete_conversation_db(cid)
    del convs[cid]
    if not convs:
        add_new_chat()
        return
    st.session_state.current_chat = list(convs.keys())[0]
    pipeline.reset()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 사이드바
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown("## 💼 취업 상담 AI")
    st.caption(f"👤 {st.session_state.user.email}")
    st.divider()

    st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
    if st.button("✏️  새 채팅", use_container_width=True):
        add_new_chat()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("**대화 목록**")

    for cid, conv in list(st.session_state.conversations.items()):
        is_active = cid == st.session_state.current_chat
        is_editing = st.session_state.editing_title == cid
        msg_count = len([m for m in conv["messages"] if m["role"] == "user"])

        if is_active:
            st.markdown('<div class="chat-active">', unsafe_allow_html=True)

        if is_editing:
            # 제목 인라인 수정
            new_title = st.text_input(
                "제목 수정",
                value=conv["title"],
                key=f"title_input_{cid}",
                label_visibility="collapsed",
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("저장", key=f"save_title_{cid}", use_container_width=True):
                    conv["title"] = new_title
                    save_conversation(user_id, cid, conv)
                    st.session_state.editing_title = None
                    st.toast("제목이 저장됐어요!", icon="✅")
                    st.rerun()
            with c2:
                if st.button("취소", key=f"cancel_title_{cid}", use_container_width=True):
                    st.session_state.editing_title = None
                    st.rerun()
        else:
            label = conv["title"][:22] + ("..." if len(conv["title"]) > 22 else "")
            col_btn, col_edit, col_del = st.columns([4, 1, 1])
            with col_btn:
                if st.button(f"💬 {label}", key=f"conv_{cid}", use_container_width=True,
                             help=f"{conv.get('created_at','')}  ·  질문 {msg_count}개"):
                    st.session_state.current_chat = cid
                    pipeline.reset()
                    pipeline.history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in conv["messages"]
                    ]
                    st.rerun()
            with col_edit:
                if st.button("✎", key=f"edit_{cid}", help="제목 수정"):
                    st.session_state.editing_title = cid
                    st.rerun()
            with col_del:
                if st.button("✕", key=f"del_{cid}", help="삭제"):
                    delete_chat(cid)
                    st.rerun()

        if is_active:
            st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # 파일 업로드
    st.markdown("**📁 공고 파일 추가**")
    uploaded = st.file_uploader("md 파일", type=["md"], label_visibility="collapsed")
    if uploaded:
        save_path = UPLOADS_DIR / uploaded.name
        if not save_path.exists():
            save_path.write_bytes(uploaded.read())
            files = get_uploaded_file_list()
            if str(save_path) not in files:
                files.append(str(save_path))
                save_uploaded_file_list(files)
            reload_pipeline()
            st.toast(f"✅ {uploaded.name} 추가됨!")
            st.rerun()
        else:
            st.info(f"이미 등록: {uploaded.name}")

    for fpath in get_uploaded_file_list():
        fname = Path(fpath).name
        c1, c2 = st.columns([5, 1])
        with c1:
            st.caption(f"📄 {fname}")
        with c2:
            if st.button("✕", key=f"rm_{fname}"):
                Path(fpath).unlink(missing_ok=True)
                save_uploaded_file_list([f for f in get_uploaded_file_list() if f != fpath])
                reload_pipeline()
                st.rerun()

    st.divider()

    # ── 검색 필터 ─────────────────────────────────────────
    st.markdown("**🔍 검색 필터**")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.caption("기술스택")
        st.text_input(
            "기술스택", placeholder="Python, React...",
            label_visibility="collapsed", key="filter_stack",
        )
    with col_f2:
        st.caption("경력")
        st.selectbox(
            "경력", ["전체", "신입", "경력"],
            label_visibility="collapsed", key="filter_career",
        )
    st.divider()

    # ── 북마크 뷰 ──────────────────────────────────────────
    bms = load_bookmarks()
    if bms:
        with st.expander(f"⭐ 북마크 ({len(bms)}개)"):
            for bm in bms:
                q_short = bm["question"][:30] + ("..." if len(bm["question"]) > 30 else "")
                c1, c2 = st.columns([4, 1])
                with c1:
                    if st.button(q_short, key=f"bm_load_{bm['id']}", use_container_width=True,
                                 help=bm["question"]):
                        st.session_state.pending_input = bm["question"]
                        st.rerun()
                with c2:
                    if st.button("✕", key=f"bm_del_{bm['id']}", help="북마크 삭제"):
                        delete_bookmark(bm["id"])
                        st.toast("북마크 삭제됨")
                        st.rerun()
        st.divider()

    # ── 등록 회사 ──────────────────────────────────────────
    if pipeline.store._companies:
        with st.expander(f"🏢 등록 회사 ({len(pipeline.store._companies)}개)"):
            for c in sorted(pipeline.store._companies):
                st.caption(f"• {c}")

    st.divider()

    usage = pipeline.token_usage
    total = usage["input"] + usage["output"]
    st.markdown(
        f'<div class="token-badge">🔢 토큰 {total:,} · 💬 {len(pipeline.history)//2}턴</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    if st.button("🚪 로그아웃", use_container_width=True):
        auth_logout()
        st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 환영 화면
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUGGESTIONS_CATEGORY = [
    {"icon": "🖥️", "title": "백엔드",       "desc": "백엔드 개발자 채용 공고 있는 회사 알려줘"},
    {"icon": "🎨", "title": "프론트엔드",    "desc": "프론트엔드 개발자 채용 공고 알려줘"},
    {"icon": "📊", "title": "데이터 / AI",   "desc": "데이터 엔지니어 또는 AI 엔지니어 채용 공고 알려줘"},
    {"icon": "⚙️", "title": "DevOps",       "desc": "DevOps 또는 인프라 엔지니어 채용 공고 알려줘"},
    {"icon": "📱", "title": "모바일",        "desc": "iOS 또는 안드로이드 개발자 채용 공고 알려줘"},
    {"icon": "🔒", "title": "보안",          "desc": "보안 엔지니어 채용 공고 있는 회사 알려줘"},
]

SUGGESTIONS_INTENT = [
    {"icon": "📋", "title": "자격요건 확인", "desc": "카카오 백엔드 개발자가 되려면 무엇이 필요한가요?"},
    {"icon": "💰", "title": "복리후생 비교", "desc": "복리후생이 좋은 회사 알려줘"},
    {"icon": "🔍", "title": "기술스택 검색", "desc": "Java Spring 경험으로 지원할 수 있는 회사는?"},
    {"icon": "🏢", "title": "회사 비교",     "desc": "카카오랑 네이버 자격요건 비교해줘"},
    {"icon": "📈", "title": "경력 요건",     "desc": "신입으로 지원 가능한 회사 어디야?"},
    {"icon": "📝", "title": "전형 절차",     "desc": "채용 전형 절차가 간단한 회사 알려줘"},
]

messages = current_messages()

if not messages:
    st.markdown('<div class="welcome-title">무엇을 도와드릴까요?</div>', unsafe_allow_html=True)
    st.markdown('<div class="welcome-sub">취업공고 기반 AI 상담 서비스</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🗂️ 직무 카테고리", "🎯 목적별 검색"])

    with tab1:
        cols = st.columns(3)
        for i, s in enumerate(SUGGESTIONS_CATEGORY):
            with cols[i % 3]:
                if st.button(
                    f"{s['icon']} **{s['title']}**\n\n{s['desc']}",
                    key=f"cat_{i}",
                    use_container_width=True,
                ):
                    st.session_state.pending_input = s["desc"]
                    st.rerun()

    with tab2:
        cols = st.columns(3)
        for i, s in enumerate(SUGGESTIONS_INTENT):
            with cols[i % 3]:
                if st.button(
                    f"{s['icon']} **{s['title']}**\n\n{s['desc']}",
                    key=f"intent_{i}",
                    use_container_width=True,
                ):
                    st.session_state.pending_input = s["desc"]
                    st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 대화 표시
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_top_k_cards(query: str, top_k: int = 3):
    """Top-K 유사 공고 카드 (hybrid search 결과)"""
    try:
        results = pipeline.store.search_hybrid(query, top_k=top_k)
        if not results:
            return
        html = f'<div style="margin-top:16px;"><div style="font-size:13px;font-weight:600;color:#ececec;margin-bottom:8px;">🏢 관련 채용공고 Top {top_k}</div>'
        for i, (_, cm) in enumerate(results[:top_k], 1):
            company = (cm.company or "").strip()
            section = (cm.section or "").strip()
            snippet = cm.text[:130].replace('<', '&lt;').replace('>', '&gt;')
            if len(cm.text) > 130:
                snippet += '...'
            html += f"""
            <div class="job-card">
                <div class="job-card-header">
                    <span class="job-rank">#{i}</span>
                    <span class="job-company">{company}</span>
                    <span class="job-section">{section}</span>
                </div>
                <div class="job-snippet">{snippet}</div>
            </div>"""
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
    except Exception:
        pass


def render_sources(citations: list[str]):
    """번호 있는 출처 카드"""
    if not citations:
        return
    html = '<div style="margin-top:12px; display:flex; flex-direction:column; gap:6px;">'
    for i, c in enumerate(citations, 1):
        html += f"""
        <div class="source-card">
            <div class="source-num">{i}</div>
            <div class="source-text">{c}</div>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


for idx, msg in enumerate(messages):
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
        if msg.get("blocked"):
            st.warning(msg["content"])
        else:
            st.markdown(msg["content"])

        # 출처 카드 (AI 메시지만)
        if msg["role"] == "assistant" and msg.get("citations") and not msg.get("blocked"):
            render_sources(msg["citations"])

        # Multi-Query 상세
        if msg.get("queries") and not msg.get("blocked"):
            with st.expander("🔍 검색 상세"):
                if msg.get("company_filter"):
                    st.caption(f"🏢 필터: **{msg['company_filter']}**")
                for i, q in enumerate(msg["queries"]):
                    st.caption(f"{'원본' if i == 0 else f'확장 {i}'}: {q}")

        # 액션 바 (AI 메시지만)
        if msg["role"] == "assistant" and not msg.get("blocked"):
            st.markdown("")
            ac1, ac2, ac3, ac4, ac5, _ = st.columns([1, 1, 1, 1, 1, 5])

            # 복사 버튼
            with ac1:
                copy_button(msg["content"], key=f"copy_{idx}")

            # 재생성 (마지막 AI 메시지만)
            is_last_ai = (
                idx == len(messages) - 1 or
                all(m["role"] == "user" for m in messages[idx+1:])
            )
            if is_last_ai:
                with ac2:
                    st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                    if st.button("🔄", key=f"regen_{idx}", help="답변 재생성"):
                        # 마지막 사용자 질문 찾기
                        last_user = next(
                            (m["content"] for m in reversed(messages[:idx]) if m["role"] == "user"),
                            None
                        )
                        if last_user:
                            # 마지막 AI 메시지 제거 후 재생성
                            messages.pop(idx)
                            messages.pop(idx - 1) if idx > 0 and messages[idx-1]["role"] == "user" else None
                            st.session_state.pending_input = last_user
                            st.session_state.regenerate = True
                    st.markdown('</div>', unsafe_allow_html=True)

            # 👍👎 피드백
            feedback = msg.get("feedback")
            with ac3:
                like_cls = "feedback-active" if feedback == "like" else "action-btn"
                st.markdown(f'<div class="{like_cls}">', unsafe_allow_html=True)
                if st.button("👍", key=f"like_{idx}", help="좋아요"):
                    msg["feedback"] = "like" if feedback != "like" else None
                    save_conversation(user_id, st.session_state.current_chat,
                                      st.session_state.conversations[st.session_state.current_chat])
                    st.toast("피드백 감사해요! 👍", icon="✅")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            with ac4:
                dislike_cls = "feedback-active" if feedback == "dislike" else "action-btn"
                st.markdown(f'<div class="{dislike_cls}">', unsafe_allow_html=True)
                if st.button("👎", key=f"dislike_{idx}", help="별로예요"):
                    msg["feedback"] = "dislike" if feedback != "dislike" else None
                    save_conversation(user_id, st.session_state.current_chat,
                                      st.session_state.conversations[st.session_state.current_chat])
                    st.toast("피드백이 반영됐어요.", icon="📝")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # ⭐ 북마크
            with ac5:
                bid = f"msg_{idx}"
                is_bookmarked = any(b["id"] == bid for b in load_bookmarks())
                bm_cls = "bookmark-active" if is_bookmarked else "action-btn"
                st.markdown(f'<div class="{bm_cls}">', unsafe_allow_html=True)
                if st.button("⭐", key=f"bm_{idx}", help="북마크"):
                    user_q = next(
                        (m["content"] for m in reversed(messages[:idx]) if m["role"] == "user"),
                        ""
                    )
                    if is_bookmarked:
                        delete_bookmark(bid)
                        st.toast("북마크 삭제됨")
                    else:
                        save_bookmark(bid, user_q, msg["content"], msg.get("citations", []))
                        st.toast("⭐ 북마크 저장됨!")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        if msg.get("output_warning"):
            st.warning(f"⚠️ {msg['output_warning']}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 채팅 입력 처리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
prompt = st.chat_input("취업 관련 질문을 입력하세요...")

if st.session_state.pending_input and not prompt:
    prompt = st.session_state.pending_input
    st.session_state.pending_input = None

if prompt:
    conv = st.session_state.conversations[st.session_state.current_chat]

    if not conv["messages"]:
        conv["title"] = prompt[:28]

    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)
    conv["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar="🤖"):
        status_ph = st.empty()
        text_ph   = st.empty()

        full_text = ""
        citations = []
        queries   = []
        company_filter = None
        blocked        = False
        output_warning = ""

        # 사이드바 필터 → 쿼리에 반영
        filter_parts = []
        if st.session_state.get("filter_stack", "").strip():
            filter_parts.append(f"기술스택: {st.session_state.filter_stack.strip()}")
        if st.session_state.get("filter_career", "전체") != "전체":
            filter_parts.append(f"경력: {st.session_state.filter_career}")
        query_with_filter = (
            f"[검색 조건 - {', '.join(filter_parts)}] {prompt}"
            if filter_parts else prompt
        )

        for event in pipeline.ask_stream(query_with_filter):
            if event["type"] == "status":
                status_ph.markdown(
                    f'<span class="status-dot"></span><span style="color:#8e8ea0;font-size:13px;">{event["text"]}</span>',
                    unsafe_allow_html=True,
                )

            elif event["type"] == "blocked":
                status_ph.empty()
                text_ph.warning(event["text"])
                blocked   = True
                full_text = event["text"]

            elif event["type"] == "queries":
                queries        = event["queries"]
                company_filter = event.get("company_filter")
                info = f"🔍 쿼리 {len(queries)}개"
                if company_filter:
                    info += f" | 🏢 {company_filter}"
                status_ph.caption(info)

            elif event["type"] == "citations":
                citations = event["citations"]
                if citations:
                    status_ph.caption(f"📎 {', '.join(citations[:2])}{'...' if len(citations) > 2 else ''}")

            elif event["type"] == "text":
                full_text += event["text"]
                text_ph.markdown(full_text + "▌")

            elif event["type"] == "done":
                status_ph.empty()
                if not blocked:
                    text_ph.markdown(full_text)
                output_warning = event.get("output_warning", "")

        # 출처 카드
        if citations and not blocked:
            render_sources(citations)

        # Top-3 유사 공고 카드
        if not blocked:
            render_top_k_cards(query_with_filter)

        if queries and not blocked:
            with st.expander("🔍 검색 상세"):
                if company_filter:
                    st.caption(f"🏢 필터: **{company_filter}**")
                for i, q in enumerate(queries):
                    st.caption(f"{'원본' if i == 0 else f'확장 {i}'}: {q}")

        if output_warning:
            st.warning(f"⚠️ {output_warning}")

    conv["messages"].append({
        "role":           "assistant",
        "content":        full_text,
        "citations":      citations,
        "queries":        queries,
        "company_filter": company_filter,
        "blocked":        blocked,
        "output_warning": output_warning,
        "feedback":       None,
    })

    save_conversation(user_id, st.session_state.current_chat, conv)
    st.rerun()
