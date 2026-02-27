"""
4주차 과제: RAG 파이프라인 - Streamlit 웹 인터페이스

1주차(LLM API) + 2주차(청킹) + 3주차(임베딩/벡터DB)를 통합한
다중 문서 관리 + 대화 히스토리 유지 RAG 챗봇
"""

import os
import tempfile

import streamlit as st

from rag_pipeline import CHAT_MODEL, EMBEDDING_MODEL, RagPipeline

# ── 페이지 설정 ────────────────────────────────────────────────
st.set_page_config(page_title="RAG 챗봇", page_icon="🔍", layout="wide")

# ── 세션 상태 초기화 ───────────────────────────────────────────
if "rag" not in st.session_state:
    st.session_state.rag = RagPipeline()
if "messages" not in st.session_state:
    st.session_state.messages = []  # [{"role", "content", "hits"?}]
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = {"input": 0, "output": 0}

rag: RagPipeline = st.session_state.rag

# ── 사이드바 ───────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 RAG 챗봇")
    st.caption("4주차: 문서 검색 + 대화 히스토리 유지")

    st.divider()

    # ── 문서 업로드 & 인덱싱 ──────────────────────────────────
    st.subheader("📂 문서 인덱싱")
    uploaded = st.file_uploader(
        "문서 업로드",
        type=["md", "txt", "pdf"],
        label_visibility="collapsed",
    )

    if uploaded:
        if st.button("인덱싱 시작", type="primary", use_container_width=True):
            suffix = os.path.splitext(uploaded.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name

            with st.spinner(f"'{uploaded.name}' 처리 중..."):
                result = rag.index_document(tmp_path, source_name=uploaded.name)

            os.remove(tmp_path)
            st.success(f"완료! {result['chunks']}개 청크 ({result['chars']:,}자)")
            st.rerun()

    st.divider()

    # ── 인덱싱된 문서 목록 ────────────────────────────────────
    st.subheader("📚 인덱싱된 문서")
    sources = rag.get_indexed_sources()

    if sources:
        for src in sources:
            col1, col2 = st.columns([3, 1])
            col1.markdown(f"**{src['source']}**  \n`{src['chunks']}개 청크`")
            if col2.button("삭제", key=f"del_{src['source']}", use_container_width=True):
                rag.delete_source(src["source"])
                st.rerun()
    else:
        st.caption("인덱싱된 문서 없음")

    st.divider()

    # ── 검색 설정 ─────────────────────────────────────────────
    st.subheader("⚙️ 검색 설정")
    top_k = st.slider(
        "top-k (가져올 청크 수)",
        min_value=1, max_value=8, value=3,
        help="질문과 유사한 청크를 몇 개 가져올지 설정",
    )
    threshold = st.slider(
        "유사도 임계값",
        min_value=0.0, max_value=1.0, value=0.0, step=0.05,
        help="이 값 미만의 청크는 검색 결과에서 제외 (0.0 = 모두 포함)",
    )
    show_chunks = st.checkbox("참조 청크 표시", value=True)

    st.divider()

    # ── 통계 ──────────────────────────────────────────────────
    st.subheader("📊 통계")
    stats = rag.get_stats()
    col1, col2 = st.columns(2)
    col1.metric("총 문서", f"{stats['total_documents']}개")
    col2.metric("총 청크", f"{stats['total_chunks']}개")

    total = st.session_state.total_tokens
    st.caption(
        f"누적 토큰  입력: {total['input']:,} / 출력: {total['output']:,}  "
        f"(합계: {total['input'] + total['output']:,})"
    )
    st.caption(f"임베딩 모델: `{EMBEDDING_MODEL}`")
    st.caption(f"채팅 모델: `{CHAT_MODEL}`")

    st.divider()

    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = []
        rag.reset_conversation()
        st.session_state.total_tokens = {"input": 0, "output": 0}
        st.rerun()

# ── 메인 화면 ──────────────────────────────────────────────────
st.title("📖 RAG 챗봇")
st.caption("문서를 업로드하고 질문하면 문서 내용을 참고해서 답변합니다.")

if not sources:
    st.info("왼쪽 사이드바에서 문서를 업로드하고 **인덱싱 시작** 버튼을 눌러주세요.")

# ── 이전 대화 출력 ─────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        # 어시스턴트 메시지에만 참조 청크 표시
        if msg.get("hits") and show_chunks:
            hits = msg["hits"]
            with st.expander(f"참조한 청크 ({len(hits)}개)"):
                for i, hit in enumerate(hits):
                    sim = hit["similarity"]
                    source = hit["metadata"]["source"]
                    chunk_idx = hit["metadata"]["chunk_index"]
                    st.markdown(
                        f"**[{i+1}] 유사도: {sim:.4f}** ({sim*100:.1f}%)  "
                        f"— `{source}` (청크 #{chunk_idx})"
                    )
                    preview = hit["content"][:300]
                    if len(hit["content"]) > 300:
                        preview += "..."
                    st.text(preview)

# ── 사용자 입력 ────────────────────────────────────────────────
user_input = st.chat_input(
    "질문을 입력하세요..." if sources else "먼저 사이드바에서 문서를 업로드해주세요",
    disabled=not sources,
)

if user_input:
    # 1. 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # 2. 어시스턴트 응답 (스트리밍)
    with st.chat_message("assistant"):
        # chat_stream()이 텍스트를 yield하고
        # 종료 후 _last_hits / _last_usage 인스턴스 변수에 메타데이터 저장
        full_response = st.write_stream(
            rag.chat_stream(user_input, top_k=top_k, threshold=threshold)
        )

        # 스트리밍 완료 후 메타데이터 읽기
        hits_result = getattr(rag, "_last_hits", [])
        usage_result = getattr(rag, "_last_usage", {"input": 0, "output": 0})

        # 참조 청크 표시
        if hits_result and show_chunks:
            with st.expander(f"참조한 청크 ({len(hits_result)}개)"):
                for i, hit in enumerate(hits_result):
                    sim = hit["similarity"]
                    source = hit["metadata"]["source"]
                    chunk_idx = hit["metadata"]["chunk_index"]
                    st.markdown(
                        f"**[{i+1}] 유사도: {sim:.4f}** ({sim*100:.1f}%)  "
                        f"— `{source}` (청크 #{chunk_idx})"
                    )
                    preview = hit["content"][:300]
                    if len(hit["content"]) > 300:
                        preview += "..."
                    st.text(preview)

    # 3. 토큰 누적
    st.session_state.total_tokens["input"] += usage_result.get("input", 0)
    st.session_state.total_tokens["output"] += usage_result.get("output", 0)

    # 4. 메시지 히스토리에 저장
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "hits": hits_result,
    })
