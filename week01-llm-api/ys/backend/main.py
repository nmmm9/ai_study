import json
import os
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel


# =========================================================
# 1. .env 파일 불러오기
# =========================================================
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("경고: OPENAI_API_KEY가 없습니다. backend/.env 파일을 확인하세요.")

client = OpenAI(api_key=api_key)


# =========================================================
# 2. FastAPI 앱 생성
# =========================================================
app = FastAPI()


# =========================================================
# 3. CORS 설정
# =========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# 4. 요청 데이터 형식 정의
# =========================================================
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    summary: Optional[str] = ""


# =========================================================
# 5. 토큰 관리 설정
# =========================================================
MODEL_NAME = "gpt-4.1-mini"

# 답변 생성 최대 토큰
MAX_OUTPUT_TOKENS = 500

# 이 값을 넘으면 오래된 대화를 요약한다.
SUMMARY_TRIGGER_TOKENS = 500

# 요약 후에도 최근 대화는 일부 유지한다.
RECENT_MESSAGES_TO_KEEP = 4

# 요약문 자체의 최대 길이 제한
MAX_SUMMARY_TOKENS = 250


def estimate_tokens(text: str) -> int:
    """
    과제용 단순 토큰 추정 함수.
    실제 토큰 수와 완전히 일치하지는 않지만,
    토큰 관리 전략을 보여주기 위한 용도로 사용한다.
    """
    if not text:
        return 0

    return max(1, len(text) // 3)


def estimate_messages_tokens(messages: List[dict]) -> int:
    return sum(estimate_tokens(message.get("content", "")) for message in messages)


def make_sse_event(event_name: str, data: dict) -> str:
    """
    FastAPI에서 React로 보낼 SSE 이벤트 형식 생성
    """
    return f"event: {event_name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def summarize_old_messages(
    old_summary: str,
    old_messages: List[ChatMessage],
) -> str:
    """
    오래된 대화 내용을 요약해서 summary memory로 저장한다.

    기존 summary가 있으면 새 요약에 함께 반영한다.
    이렇게 하면 오래된 원문 대화를 지우더라도 핵심 맥락은 유지할 수 있다.
    """
    if not old_messages and not old_summary:
        return old_summary

    old_conversation_text = ""

    for msg in old_messages:
        speaker = "사용자" if msg.role == "user" else "AI"
        old_conversation_text += f"{speaker}: {msg.content}\n"

    summary_prompt = f"""
다음은 이전 대화 요약과 오래된 대화 내용입니다.
앞으로의 대화에 필요한 핵심 정보만 한국어로 짧게 요약하세요.

[기존 요약]
{old_summary if old_summary else "없음"}

[오래된 대화]
{old_conversation_text}

요약 규칙:
- 사용자의 목표, 요구사항, 결정사항을 중심으로 정리
- 불필요한 인사말이나 반복 표현 제거
- 5문장 이내로 작성
- 다음 대화에서 참고할 수 있게 명확하게 작성
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "너는 긴 대화를 짧고 정확하게 요약하는 assistant야.",
            },
            {
                "role": "user",
                "content": summary_prompt,
            },
        ],
        max_tokens=MAX_SUMMARY_TOKENS,
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()


@app.get("/")
def root():
    return {"message": "FastAPI backend is running"}


@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY가 설정되지 않았습니다. backend/.env 파일을 확인하세요.",
        )

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="메시지가 비어 있습니다.")

    def event_generator():
        """
        1. 현재 대화 토큰 추정
        2. 기준치 초과 시 오래된 대화 요약
        3. 요약본 + 최근 대화 + 현재 질문으로 OpenAI 호출
        4. Streaming 응답을 SSE로 전달
        """

        history = request.history or []
        old_summary = request.summary or ""

        # 현재 요청까지 포함해서 토큰 추정
        history_dict = [{"role": msg.role, "content": msg.content} for msg in history]
        current_messages_for_count = history_dict + [
            {"role": "user", "content": request.message}
        ]

        summary_tokens = estimate_tokens(old_summary)
        conversation_tokens = estimate_messages_tokens(current_messages_for_count)
        estimated_before_summary_tokens = summary_tokens + conversation_tokens

        summary_used = False
        new_summary = old_summary
        recent_history = history

        # =========================================================
        # 누적 토큰이 기준치를 넘으면 오래된 대화를 요약
        # =========================================================
        if estimated_before_summary_tokens >= SUMMARY_TRIGGER_TOKENS:
            summary_used = True

            # 최근 대화 일부는 그대로 유지하고, 나머지 오래된 대화만 요약한다.
            old_messages_to_summarize = history[:-RECENT_MESSAGES_TO_KEEP]
            recent_history = history[-RECENT_MESSAGES_TO_KEEP:]

            if old_messages_to_summarize:
                new_summary = summarize_old_messages(
                    old_summary=old_summary,
                    old_messages=old_messages_to_summarize,
                )

        # =========================================================
        # OpenAI에 보낼 메시지 구성
        # =========================================================
        messages = [
            {
                "role": "system",
                "content": (
                    "너는 사용자의 질문에 한국어로 친절하고 명확하게 답하는 AI assistant야. "
                    "답변은 핵심 중심으로 작성해."
                ),
            }
        ]

        # 요약 메모리가 있으면 system 메시지로 전달
        if new_summary:
            messages.append(
                {
                    "role": "system",
                    "content": f"이전 대화 요약 메모리:\n{new_summary}",
                }
            )

        # 최근 대화 추가
        for msg in recent_history:
            messages.append({"role": msg.role, "content": msg.content})

        # 현재 사용자 질문 추가
        messages.append({"role": "user", "content": request.message})

        estimated_input_tokens = estimate_messages_tokens(messages)

        # 프론트엔드에 토큰 관리 정보 먼저 전달
        yield make_sse_event(
            "meta",
            {
                "model": MODEL_NAME,
                "summaryUsed": summary_used,
                "summary": new_summary,
                "summaryTriggerTokens": SUMMARY_TRIGGER_TOKENS,
                "recentMessagesToKeep": RECENT_MESSAGES_TO_KEEP,
                "maxOutputTokens": MAX_OUTPUT_TOKENS,
                "estimatedBeforeSummaryTokens": estimated_before_summary_tokens,
                "estimatedInputTokens": estimated_input_tokens,
                "note": (
                    "누적 토큰이 기준치를 넘으면 오래된 대화를 요약하고, "
                    "요약본과 최근 대화만 사용합니다."
                ),
            },
        )

        full_answer = ""

        try:
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=MAX_OUTPUT_TOKENS,
                stream=True,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta.content

                if delta:
                    full_answer += delta

                    yield make_sse_event(
                        "message",
                        {
                            "delta": delta,
                        },
                    )

            estimated_output_tokens = estimate_tokens(full_answer)

            yield make_sse_event(
                "done",
                {
                    "summaryUsed": summary_used,
                    "summary": new_summary,
                    "estimatedOutputTokens": estimated_output_tokens,
                    "estimatedTotalTokens": estimated_input_tokens
                    + estimated_output_tokens,
                },
            )

        except Exception as e:
            yield make_sse_event(
                "error",
                {
                    "message": str(e),
                },
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )