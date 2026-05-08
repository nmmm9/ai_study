"""
4주차 RAG 파이프라인 - Streamlit 웹 UI
백엔드: rag_pipeline.py (RAGPipeline)
프론트: Streamlit (채팅 인터페이스)

실행: streamlit run app.py
"""

import streamlit as st
from pathlib import Path
from rag_pipeline import RAGPipeline

# ── 페이지 설정 ───────────────────────────────────────────────
st.set_page_config(
    page_title="취업 상담 AI",
    page_icon="💼",
    layout="centered",
)

# ── RAG 파이프라인 초기화 (최초 1회만 실행) ──────────────────
@st.cache_resource(show_spinner="RAG 파이프라인 초기화 중...")
def get_pipeline() -> RAGPipeline:
    pipeline = RAGPipeline()
    doc_path = str(Path(__file__).parent / "job_postings.md")
    pipeline.load_document(doc_path, strategy="paragraph", chunk_size=200)
    return pipeline

pipeline = get_pipeline()

# ── 세션 상태 초기화 ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []  # {"role", "content", "citations"}

# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 파이프라인 정보")
    st.markdown("""
    | 항목 | 내용 |
    |------|------|
    | LLM | GPT-4o-mini |
    | Vector DB | ChromaDB |
    | 임베딩 | sentence-transformers |
    | Re-ranker | Cross-Encoder |
    | 가드레일 | 취업 외 질문 차단 |
    | 검색 | top-10 → Re-rank top-3 |
    """)

    st.divider()

    usage = pipeline.token_usage
    total = usage["input"] + usage["output"]
    st.markdown("**토큰 사용량**")
    st.markdown(f"- 입력: `{usage['input']}`")
    st.markdown(f"- 출력: `{usage['output']}`")
    st.markdown(f"- 합계: `{total}`")
    st.markdown(f"- 대화: `{len(pipeline.history) // 2}`턴")

    st.divider()

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        pipeline.reset()
        st.rerun()

# ── 헤더 ─────────────────────────────────────────────────────
st.title("💼 취업 상담 AI")
st.caption("취업공고 기반 RAG 챗봇 | 4주차 - juwon")
st.divider()

# ── 이전 대화 표시 ────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("blocked"):
            st.warning(msg["content"])
        else:
            st.markdown(msg["content"])
        if msg.get("citations"):
            with st.expander("📎 참조 출처"):
                for citation in msg["citations"]:
                    st.markdown(f"- {citation}")
        if msg.get("output_warning"):
            st.warning(f"⚠️ {msg['output_warning']}")

# ── 채팅 입력 ─────────────────────────────────────────────────
if prompt := st.chat_input("취업 관련 질문을 입력하세요..."):

    # 사용자 메시지 표시
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI 응답 생성
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        text_placeholder = st.empty()

        full_text = ""
        citations = []
        blocked = False
        output_warning = ""

        for event in pipeline.ask_stream(prompt):

            if event["type"] == "status":
                status_placeholder.caption(f"⏳ {event['text']}")

            elif event["type"] == "blocked":
                status_placeholder.empty()
                text_placeholder.warning(event["text"])
                blocked = True
                full_text = event["text"]

            elif event["type"] == "citations":
                citations = event["citations"]
                if citations:
                    status_placeholder.caption(
                        f"📎 참조: {', '.join(citations[:2])}{'...' if len(citations) > 2 else ''}"
                    )

            elif event["type"] == "text":
                full_text += event["text"]
                text_placeholder.markdown(full_text + "▌")

            elif event["type"] == "done":
                status_placeholder.empty()
                if not blocked:
                    text_placeholder.markdown(full_text)
                output_warning = event.get("output_warning", "")

        # 출처 표시
        if citations and not blocked:
            with st.expander("📎 참조 출처"):
                for citation in citations:
                    st.markdown(f"- {citation}")

        # 출력 검증 경고
        if output_warning:
            st.warning(f"⚠️ {output_warning}")

    # 메시지 저장
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_text,
        "citations": citations,
        "blocked": blocked,
        "output_warning": output_warning,
    })

    # 사이드바 토큰 수치 갱신
    st.rerun()
