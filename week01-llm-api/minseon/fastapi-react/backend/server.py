"""
1주차: FastAPI 백엔드 서버

Streamlit(app.py) 대신 FastAPI로 REST API 서버 구현
React 프론트엔드(index.html)와 JSON + SSE 방식으로 통신

비교:
  Streamlit  → Python 코드가 곧 화면 (합쳐져 있음)
  FastAPI    → 백엔드만 담당, 화면은 React가 따로 만듦
"""

import json

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="GPT-4o 챗봇 API")
client = OpenAI()

# ── 설정 ──────────────────────────────────────────────────────
MODEL = "gpt-4o"
SYSTEM_PROMPT = "당신은 친절한 AI 어시스턴트입니다. 한국어로 답변합니다."
MAX_MESSAGES = 20

# ── 서버 상태 (메모리) ─────────────────────────────────────────
# 실제 서비스에서는 DB나 세션으로 관리해야 함 (지금은 학습용 단순 구현)
conversation: list[dict] = []
total_tokens = {"input": 0, "output": 0}


# ── 요청 데이터 모델 ───────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str


# ── 유틸 ───────────────────────────────────────────────────────
def trim_conversation():
    """대화 히스토리를 MAX_MESSAGES 개로 제한 (Sliding Window)"""
    global conversation
    if len(conversation) > MAX_MESSAGES:
        conversation = conversation[-MAX_MESSAGES:]


# ── CORS 설정 ──────────────────────────────────────────────────
# React 프론트엔드(다른 포트)에서 이 서버에 요청할 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 실제 서비스에서는 특정 도메인만 허용
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 스트리밍 제너레이터 ────────────────────────────────────────
async def stream_generator(user_message: str):
    """
    OpenAI 스트리밍 응답을 SSE(Server-Sent Events) 형식으로 변환

    SSE 형식:
      data: {"text": "안녕"}\n\n   ← 텍스트 청크
      data: {"text": "하세요"}\n\n
      data: {"done": true, "usage": {...}}\n\n  ← 완료 신호

    React 프론트엔드에서 fetch + ReadableStream으로 수신
    """
    global conversation, total_tokens

    conversation.append({"role": "user", "content": user_message})
    trim_conversation()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation

    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True},
    )

    full_response = ""
    input_tokens = 0
    output_tokens = 0

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            full_response += text
            # 토큰 하나씩 SSE로 전송
            yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"

        if hasattr(chunk, "usage") and chunk.usage:
            input_tokens = chunk.usage.prompt_tokens
            output_tokens = chunk.usage.completion_tokens

    # 대화 히스토리 & 토큰 누적
    conversation.append({"role": "assistant", "content": full_response})
    total_tokens["input"] += input_tokens
    total_tokens["output"] += output_tokens

    # 완료 신호 전송
    yield f"data: {json.dumps({'done': True, 'usage': {'input': input_tokens, 'output': output_tokens}})}\n\n"


# ── API 엔드포인트 ─────────────────────────────────────────────

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    스트리밍 방식으로 AI 답변 생성 (SSE)

    React에서: fetch("/chat/stream", {method: "POST", body: ...})
    → response.body.getReader()로 스트림 읽기
    """
    return StreamingResponse(
        stream_generator(req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # nginx 버퍼링 비활성화
        },
    )


@app.delete("/chat")
async def reset_chat():
    """대화 히스토리 초기화"""
    global conversation
    conversation.clear()
    return {"status": "reset"}


@app.get("/usage")
async def get_usage():
    """누적 토큰 사용량 조회"""
    return {
        "input": total_tokens["input"],
        "output": total_tokens["output"],
        "total": total_tokens["input"] + total_tokens["output"],
        "conversation_length": len(conversation),
    }


@app.get("/health")
async def health():
    """서버 상태 확인"""
    return {"status": "ok", "model": MODEL}
