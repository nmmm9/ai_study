"""
5주차 Advanced RAG - Streamlit 웹 UI
백엔드: rag_pipeline.py (AdvancedRAGPipeline)

실행: streamlit run app.py
"""

import streamlit as st
from pathlib import Path
from rag_pipeline import AdvancedRAGPipeline

# ── 페이지 설정 ───────────────────────────────────────────────
st.set_page_config(
    page_title="취업 상담 AI (Advanced)",
    page_icon="💼",
    layout="centered",
)

# ── RAG 파이프라인 초기화 ──────────────────────────────────────
@st.cache_resource(show_spinner="Advanced RAG 파이프라인 초기화 중...")
def get_pipeline() -> AdvancedRAGPipeline:
    pipeline = AdvancedRAGPipeline()
    # week04의 job_postings.md 참조
    doc_path = str(
        Path(__file__).resolve().parent.parent.parent
        / "week04-rag-pipeline" / "juwon" / "job_postings.md"
    )
    pipeline.load_document(doc_path, child_size=200, parent_size=600)
    return pipeline

pipeline = get_pipeline()

# ── 세션 상태 초기화 ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Advanced RAG (5주차)")
    st.markdown("""
    | 항목 | 4주차 | 5주차 |
    |------|-------|-------|
    | 검색 | Vector only | **BM25 + Vector** |
    | 쿼리 | 단일 | **Multi-Query** |
    | 필터 | 없음 | **회사명 감지** |
    | 청크 | 200자 | **child 200 / parent 600** |
    | Re-ranker | Cross-Encoder | Cross-Encoder |
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

    st.markdown(f"**등록 회사 수:** `{len(pipeline.store._companies)}`개")
    if pipeline.store._companies:
        st.markdown(", ".join(sorted(pipeline.store._companies)))

    st.divider()

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        pipeline.reset()
        st.rerun()

# ── 헤더 ─────────────────────────────────────────────────────
st.title("💼 취업 상담 AI")
st.caption("Advanced RAG | BM25 + Vector · Multi-Query · Metadata Filtering · Parent-Child | 5주차 - juwon")
st.divider()

# ── 이전 대화 표시 ────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("blocked"):
            st.warning(msg["content"])
        else:
            st.markdown(msg["content"])

        # 확장된 쿼리 표시
        if msg.get("queries"):
            with st.expander("🔍 Multi-Query 확장"):
                if msg.get("company_filter"):
                    st.caption(f"🏢 회사 필터: **{msg['company_filter']}**")
                for i, q in enumerate(msg["queries"]):
                    label = "원본" if i == 0 else f"확장 {i}"
                    st.markdown(f"- `{label}` {q}")

        if msg.get("citations"):
            with st.expander("📎 참조 출처"):
                for citation in msg["citations"]:
                    st.markdown(f"- {citation}")

        if msg.get("output_warning"):
            st.warning(f"⚠️ {msg['output_warning']}")

# ── 채팅 입력 ─────────────────────────────────────────────────
if prompt := st.chat_input("취업 관련 질문을 입력하세요..."):

    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        text_placeholder = st.empty()

        full_text = ""
        citations = []
        queries = []
        company_filter = None
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

            elif event["type"] == "queries":
                queries = event["queries"]
                company_filter = event.get("company_filter")
                info = f"🔍 쿼리 {len(queries)}개"
                if company_filter:
                    info += f" | 🏢 {company_filter} 필터 적용"
                status_placeholder.caption(info)

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

        # 확장 쿼리 표시
        if queries and not blocked:
            with st.expander("🔍 Multi-Query 확장"):
                if company_filter:
                    st.caption(f"🏢 회사 필터: **{company_filter}**")
                for i, q in enumerate(queries):
                    label = "원본" if i == 0 else f"확장 {i}"
                    st.markdown(f"- `{label}` {q}")

        # 출처 표시
        if citations and not blocked:
            with st.expander("📎 참조 출처"):
                for citation in citations:
                    st.markdown(f"- {citation}")

        if output_warning:
            st.warning(f"⚠️ {output_warning}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_text,
        "citations": citations,
        "queries": queries,
        "company_filter": company_filter,
        "blocked": blocked,
        "output_warning": output_warning,
    })

    st.rerun()
