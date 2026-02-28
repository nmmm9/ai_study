"""
3주차: Embedding & Vector DB - Streamlit 웹 앱
sentence-transformers + FAISS 기반 의미 유사도 검색으로 업그레이드
2주차 키워드 매칭 → 3주차 임베딩 검색
"""

import sys
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# chunking_chat.py에서 DocumentLoader, TextChunker 재사용 (2주차 코드 그대로)
sys.path.insert(0, str(Path(__file__).parent))
from chunking_chat import DocumentLoader, TextChunker
from embedding_search import EmbeddingStore

load_dotenv(Path(__file__).parent / ".env")

# ── 상수 ─────────────────────────────────────────────────

MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = (
    "당신은 친절한 취업 상담 AI입니다. "
    "제공된 취업공고 내용을 바탕으로 질문에 한국어로 답변합니다. "
    "문서에 없는 내용은 없다고 솔직하게 말해주세요."
)
CHUNK_SIZE = 500
OVERLAP = 50
TOP_K = 5

STRATEGY_LABELS = {
    "fixed":     "Fixed — 고정 크기 분할",
    "separator": "Separator — 구분자 재귀 분할",
    "paragraph": "Paragraph — 단락 단위 분할",
}

# ── 세션 상태 초기화 ──────────────────────────────────────

def init_session():
    defaults = {
        "messages":    [],
        "chunks":      [],
        "chunker":     None,
        "raw_text":    "",
        "client":      OpenAI(),
        "token_total": 0,
        "embed_store": None,  # EmbeddingStore, 문서 로드 시 초기화
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ── 청크 검색 ─────────────────────────────────────────────

def find_relevant_chunks(query: str) -> list[str]:
    """임베딩 유사도 검색으로 관련 청크 상위 TOP_K개 반환"""
    store = st.session_state.embed_store
    if store is None or not store.is_built:
        return []
    results = store.search(query, top_k=TOP_K)
    return [chunk for _score, chunk in results]


# ── OpenAI 스트리밍 ───────────────────────────────────────

def stream_chat(messages: list[dict]):
    """st.write_stream에 넘길 제너레이터"""
    stream = st.session_state.client.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True},
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
        if chunk.usage:
            st.session_state.token_total += chunk.usage.total_tokens


def build_messages(context: str = "") -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if context:
        messages.append({"role": "system", "content": context})
    messages.extend(st.session_state.messages)
    return messages


# ── 문서 로드 + 청킹 ──────────────────────────────────────

def load_and_chunk(text: str, strategy: str):
    st.session_state.raw_text = text
    st.session_state.chunker = TextChunker(
        strategy=strategy, chunk_size=CHUNK_SIZE, overlap=OVERLAP
    )
    st.session_state.chunks = st.session_state.chunker.chunk(text)

    # 청크가 바뀔 때마다 임베딩 인덱스 재구축
    with st.spinner("임베딩 인덱스 구축 중... (첫 실행 시 모델 다운로드가 있을 수 있어요)"):
        if st.session_state.embed_store is None:
            st.session_state.embed_store = EmbeddingStore()
        st.session_state.embed_store.build(st.session_state.chunks)


# ── 메인 ─────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="취업공고 챗봇",
        page_icon="💼",
        layout="wide",
    )
    init_session()

    # ── 사이드바 ────────────────────────────────────────

    with st.sidebar:
        st.title("⚙️ 설정")

        # 1. 청킹 전략 선택
        st.subheader("1. 청킹 전략")
        strategy = st.radio(
            label="전략",
            options=list(STRATEGY_LABELS.keys()),
            index=2,  # paragraph 기본값
            format_func=lambda x: STRATEGY_LABELS[x],
            label_visibility="collapsed",
        )

        # 전략이 바뀌면 기존 문서 재청킹
        if st.session_state.raw_text:
            if (st.session_state.chunker is None
                    or st.session_state.chunker.strategy != strategy):
                load_and_chunk(st.session_state.raw_text, strategy)

        st.divider()

        # 2. 문서 로드
        st.subheader("2. 문서 로드")

        # 샘플 파일 버튼
        default_path = Path(__file__).parent / "job_postings.md"
        if st.button("📄 샘플 파일 사용", use_container_width=True):
            load_and_chunk(DocumentLoader.load(str(default_path)), strategy)
            st.success(f"로드 완료 — {len(st.session_state.chunks)}개 청크")

        # 직접 업로드
        uploaded = st.file_uploader("또는 직접 업로드", type=["md", "pdf"])
        if uploaded:
            if uploaded.name.endswith(".pdf"):
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(uploaded.read())
                    raw = DocumentLoader.load(tmp.name)
            else:
                raw = uploaded.read().decode("utf-8")
            load_and_chunk(raw, strategy)
            st.success(f"로드 완료 — {len(st.session_state.chunks)}개 청크")

        st.divider()

        # 3. 청크 목록
        if st.session_state.chunks:
            st.subheader(f"3. 청크 목록 ({len(st.session_state.chunks)}개)")
            for i, chunk in enumerate(st.session_state.chunks, 1):
                preview = chunk[:45].replace("\n", " ")
                with st.expander(f"[{i:02d}] {len(chunk)}자  {preview}…"):
                    st.text(chunk)

        st.divider()

        # 초기화 + 토큰
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑 대화 초기화", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        with col2:
            st.metric("누적 토큰", f"{st.session_state.token_total:,}")

    # ── 메인 채팅 영역 ───────────────────────────────────

    st.title("💼 취업공고 챗봇")
    st.caption("3주차 — 임베딩 기반 유사도 검색 + GPT 질의응답")

    if not st.session_state.chunks:
        st.info("👈 왼쪽 사이드바에서 문서를 먼저 로드해주세요.")
        return

    # 이전 대화 표시
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "strategy" in msg:
                label = STRATEGY_LABELS[msg["strategy"]]
                chunks_used = msg["chunks_used"]
                if chunks_used > 0:
                    st.caption(f"📎 참조 청크 {chunks_used}개 / 전략: {label}")
                else:
                    st.caption(f"⚠️ 관련 청크 없음 / 전략: {label}")

    # 입력창
    if prompt := st.chat_input("취업공고에 대해 궁금한 점을 물어보세요"):
        # 사용자 메시지
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 관련 청크 검색
        relevant = find_relevant_chunks(prompt)
        context = ""
        if relevant:
            context = "아래는 관련 취업공고 내용입니다:\n\n" + "\n\n---\n\n".join(relevant)

        # AI 응답
        with st.chat_message("assistant"):
            if relevant:
                st.caption(f"📎 참조 청크 {len(relevant)}개 / 전략: {strategy}")
            else:
                st.caption("⚠️ 관련 청크를 찾지 못했습니다 (임베딩 검색 결과 없음)")
            response = st.write_stream(stream_chat(build_messages(context)))

        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "strategy": strategy,
            "chunks_used": len(relevant),
        })


if __name__ == "__main__":
    main()
