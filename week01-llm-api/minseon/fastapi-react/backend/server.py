"""
1주차: FastAPI 백엔드 서버

[관심사 분리]
  이 파일: FastAPI 라우터 (엔드포인트 정의, 상태 관리)
  services/llm_service.py: OpenAI 설정, 대화 관리, SSE 스트리밍 생성

비교:
  Streamlit  → Python 코드가 곧 화면 (합쳐져 있음)
  FastAPI    → 백엔드만 담당, 화면은 React가 따로 만듦

  프론트/백엔드 완전 분리 → 전문적인 구조
디자인 자유도 최고
배우고 설정할 게 많음 (Node.js, npm, CORS 등)
실제 서비스 수준의 앱 가능
"""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.llm_service import stream_generator

load_dotenv()

app = FastAPI(title="GPT-4o 챗봇 API")

# ── 서버 상태 (메모리) ─────────────────────────────────────────
# 실제 서비스에서는 DB나 세션으로 관리해야 함 (지금은 학습용 단순 구현)
conversation: list[dict] = []
total_tokens = {"input": 0, "output": 0}


# ── 요청 데이터 모델 ───────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str


# ── CORS 설정 ──────────────────────────────────────────────────
# React 프론트엔드(다른 포트)에서 이 서버에 요청할 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 실제 서비스에서는 특정 도메인만 허용
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── API 엔드포인트 ─────────────────────────────────────────────

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    스트리밍 방식으로 AI 답변 생성 (SSE)

    React에서: fetch("/chat/stream", {method: "POST", body: ...})
    → response.body.getReader()로 스트림 읽기
    """
    return StreamingResponse(
        stream_generator(req.message, conversation, total_tokens),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # nginx 버퍼링 비활성화
        },
    )


@app.delete("/chat")
async def reset_chat():
    """대화 히스토리 초기화"""
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
    return {"status": "ok"}
