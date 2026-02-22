"""
1주차 과제: OpenAI GPT-4o - Streamlit 웹 챗봇
"""

import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# ── 설정 ──────────────────────────────────────────────
MODEL = "gpt-4o"
MAX_TOKENS = 1024
SYSTEM_PROMPT = "당신은 친절한 AI 어시스턴트입니다. 한국어로 답변합니다."

# ── 페이지 설정 ────────────────────────────────────────
st.set_page_config(page_title="GPT-4o 챗봇", page_icon="🤖")
st.title("🤖 GPT-4o 1:1 채팅")

# ── 세션 상태 초기화 ───────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
if "total_input_tokens" not in st.session_state:
    st.session_state.total_input_tokens = 0
if "total_output_tokens" not in st.session_state:
    st.session_state.total_output_tokens = 0

# ── 초기화 버튼 + 토큰 사용량 ──────────────────────────
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    if st.button("대화 초기화"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.total_input_tokens = 0
        st.session_state.total_output_tokens = 0
        st.rerun()
with col2:
    st.metric("입력 토큰", st.session_state.total_input_tokens)
with col3:
    st.metric("출력 토큰", st.session_state.total_output_tokens)
with col4:
    st.metric("총 토큰", st.session_state.total_input_tokens + st.session_state.total_output_tokens)

# ── 이전 대화 출력 ─────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ── 사용자 입력 ────────────────────────────────────────
if user_input := st.chat_input("메시지를 입력하세요..."):

    # 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # AI 응답 (Streaming)
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=st.session_state.messages,
            stream=True,
            stream_options={"include_usage": True},
        )

        def generate():
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                if chunk.usage:
                    st.session_state.total_input_tokens += chunk.usage.prompt_tokens
                    st.session_state.total_output_tokens += chunk.usage.completion_tokens

        full_response = st.write_stream(generate())

    st.session_state.messages.append({"role": "assistant", "content": full_response})
