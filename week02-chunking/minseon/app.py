"""
2주차 과제: Chunking - Streamlit 웹 인터페이스
문서를 업로드하면 청킹 결과를 시각적으로 확인
"""

import streamlit as st
from chunker import chunk_text, chunk_markdown_by_headers, load_document
import tempfile
import os

# ── 페이지 설정 ────────────────────────────────────────
st.set_page_config(page_title="문서 청킹 도구", page_icon="✂️", layout="wide")
st.title("✂️ 문서 청킹 시각화 (2주차)")
st.caption("문서를 업로드하면 청킹 결과를 확인할 수 있습니다.")

# ── 사이드바: 설정 ─────────────────────────────────────
with st.sidebar:
    st.header("청킹 설정")
    chunk_size = st.slider("chunk_size (최대 글자 수)", 100, 2000, 900, step=50)
    chunk_overlap = st.slider("chunk_overlap (겹침 글자 수)", 0, 300, 90, step=10)

    st.divider()
    st.markdown(f"""
    **현재 설정**
    - chunk_size: `{chunk_size}`
    - chunk_overlap: `{chunk_overlap}`
    - overlap 비율: `{chunk_overlap/chunk_size*100:.0f}%`
    """)

    use_md_headers = st.checkbox("Markdown 헤더 기반 분할도 보기", value=False)

# ── 문서 입력 ──────────────────────────────────────────
tab1, tab2 = st.tabs(["파일 업로드", "텍스트 직접 입력"])

text = None
source_name = None

with tab1:
    uploaded = st.file_uploader("문서 업로드 (md / txt / pdf)", type=["md", "txt", "pdf"])
    if uploaded:
        suffix = os.path.splitext(uploaded.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name
        text = load_document(tmp_path)
        source_name = uploaded.name
        os.unlink(tmp_path)

with tab2:
    raw_text = st.text_area("텍스트를 직접 붙여넣으세요", height=200, placeholder="여기에 텍스트를 입력하세요...")
    if raw_text.strip():
        text = raw_text
        source_name = "직접 입력"

# ── 청킹 실행 & 결과 출력 ──────────────────────────────
if text:
    st.divider()

    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    lengths = [len(c) for c in chunks]

    # 통계 요약
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 청크 수", f"{len(chunks)}개")
    col2.metric("평균 길이", f"{sum(lengths)//len(lengths)}자")
    col3.metric("최소 길이", f"{min(lengths)}자")
    col4.metric("최대 길이", f"{max(lengths)}자")

    st.divider()

    # 청크 목록
    st.subheader(f"청킹 결과 — {source_name}")
    for i, chunk in enumerate(chunks):
        with st.expander(f"[{i+1}] {len(chunk)}자  |  {chunk[:60].replace(chr(10), ' ')}..."):
            st.text(chunk)

    # Markdown 헤더 기반 분할 (옵션)
    if use_md_headers and source_name and source_name.endswith(".md"):
        st.divider()
        st.subheader("Markdown 헤더 기반 분할")
        md_chunks = chunk_markdown_by_headers(text)
        for i, chunk in enumerate(md_chunks):
            meta = " > ".join(f"{v}" for v in chunk["metadata"].values())
            with st.expander(f"[{i+1}] {meta}  |  {len(chunk['content'])}자"):
                st.text(chunk["content"])
else:
    st.info("파일을 업로드하거나 텍스트를 입력하면 청킹 결과가 여기에 표시됩니다.")
