"""
3주차 과제: Embedding & Vector DB - Streamlit RAG 챗봇
문서를 임베딩해서 ChromaDB에 저장 후, 질문에 관련 청크를 검색해 GPT로 답변
"""

import os
import streamlit as st
from dotenv import load_dotenv

from embedder import embed_texts, get_collection, store_embeddings, search, split_text, load_document

load_dotenv()

# ── 페이지 설정 ────────────────────────────────────────
st.set_page_config(page_title="RAG 챗봇", page_icon="📚")
st.title("📚 RAG 챗봇 (3주차)")
st.caption("문서를 업로드하면 내용 기반으로 답변합니다.")

# ── 세션 상태 초기화 ───────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "indexed" not in st.session_state:
    st.session_state.indexed = False

# ── 사이드바: 문서 업로드 & 인덱싱 ───────────────────────
with st.sidebar:
    st.header("문서 설정")

    uploaded = st.file_uploader("문서 업로드 (md / txt / pdf)", type=["md", "txt", "pdf"])

    if uploaded and st.button("임베딩 & 저장", type="primary"):
        # 업로드 파일을 임시 저장
        tmp_path = f"./tmp_{uploaded.name}"
        with open(tmp_path, "wb") as f:
            f.write(uploaded.read())

        with st.spinner("문서 처리 중..."):
            text = load_document(tmp_path)
            chunks = split_text(text)
            vectors = embed_texts(chunks)
            collection = get_collection()
            store_embeddings(collection, chunks, vectors, uploaded.name)

        os.remove(tmp_path)
        st.session_state.indexed = True
        st.success(f"완료! {len(chunks)}개 청크 저장됨")

    st.divider()

    top_k = st.slider("검색할 청크 수 (top-k)", min_value=1, max_value=5, value=3)
    show_chunks = st.checkbox("참조 청크 보기", value=True)

    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.rerun()

# ── 상태 표시 ──────────────────────────────────────────
if not st.session_state.indexed:
    st.info("사이드바에서 문서를 업로드하고 '임베딩 & 저장' 버튼을 눌러주세요.")

# ── 이전 대화 출력 ─────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("chunks") and show_chunks:
            with st.expander("참조한 문서 청크"):
                for i, chunk in enumerate(msg["chunks"]):
                    st.markdown(f"**[{i+1}] 유사도: {chunk['similarity']:.3f}**")
                    st.text(chunk["content"][:300] + ("..." if len(chunk["content"]) > 300 else ""))

# ── 사용자 입력 ────────────────────────────────────────
if user_input := st.chat_input("질문을 입력하세요...", disabled=not st.session_state.indexed):

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("검색 중..."):
            collection = get_collection()
            hits = search(collection, user_input, top_k=top_k)

        # 검색된 청크를 컨텍스트로 구성
        context = "\n\n---\n\n".join([h["content"] for h in hits])
        prompt = f"""다음 문서 내용을 참고해서 질문에 답변해주세요.

[참고 문서]
{context}

[질문]
{user_input}

문서에 없는 내용은 "문서에서 찾을 수 없습니다"라고 답변해주세요."""

        from openai import OpenAI
        client = OpenAI()

        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 주어진 문서를 기반으로 질문에 답변하는 AI입니다. 한국어로 답변합니다."},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )

        full_response = st.write_stream(
            chunk.choices[0].delta.content
            for chunk in stream
            if chunk.choices and chunk.choices[0].delta.content
        )

        # 참조 청크 표시
        chunks_info = [{"content": h["content"], "similarity": 1 - h["distance"]} for h in hits]
        if show_chunks:
            with st.expander("참조한 문서 청크"):
                for i, chunk in enumerate(chunks_info):
                    st.markdown(f"**[{i+1}] 유사도: {chunk['similarity']:.3f}**")
                    st.text(chunk["content"][:300] + ("..." if len(chunk["content"]) > 300 else ""))

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "chunks": chunks_info,
    })
