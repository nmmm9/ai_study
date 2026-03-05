"""
FastAPI 백엔드 LLM 서비스 - OpenAI 스트리밍 호출 (SSE 포맷)

[관심사 분리 역할]
  이 파일: OpenAI 설정, 대화 관리, SSE 스트리밍 생성
  server.py: FastAPI 라우터 (엔드포인트 정의, HTTP 요청/응답)
"""

import json

from openai import OpenAI

# ── 설정 ──────────────────────────────────────────────
MODEL = "gpt-4o"
MAX_MESSAGES = 20
SYSTEM_PROMPT = "당신은 친절한 AI 어시스턴트입니다. 한국어로 답변합니다."

# ── 대화 관리 ──────────────────────────────────────────
def trim_conversation(conversation: list[dict]) -> None:
    """Sliding Window: MAX_MESSAGES 초과 시 오래된 메시지 제거 (in-place)"""
    if len(conversation) > MAX_MESSAGES:
        del conversation[:-MAX_MESSAGES]


# ── 스트리밍 제너레이터 ────────────────────────────────
async def stream_generator(user_message: str, conversation: list[dict], total_tokens: dict):
    """
    OpenAI 스트리밍 응답을 SSE(Server-Sent Events) 형식으로 변환

    Args:
        user_message:  사용자 입력 텍스트
        conversation:  대화 히스토리 리스트 (in-place 수정됨)
        total_tokens:  누적 토큰 카운터 딕셔너리 (in-place 수정됨)

    Yields:
        SSE 이벤트 문자열
          - 텍스트 청크: data: {"text": "..."}\n\n
          - 완료 신호:   data: {"done": true, "usage": {...}}\n\n
    """
    conversation.append({"role": "user", "content": user_message})
    trim_conversation(conversation)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation

    client = OpenAI()
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
            yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"

        if hasattr(chunk, "usage") and chunk.usage:
            input_tokens = chunk.usage.prompt_tokens
            output_tokens = chunk.usage.completion_tokens

    conversation.append({"role": "assistant", "content": full_response})
    total_tokens["input"] += input_tokens
    total_tokens["output"] += output_tokens

    yield f"data: {json.dumps({'done': True, 'usage': {'input': input_tokens, 'output': output_tokens}})}\n\n"
