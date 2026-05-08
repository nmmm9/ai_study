"""
LLM 서비스 - GPT 스트리밍 응답 생성

[관심사 분리 역할]
  이 파일: OpenAI Chat API 스트리밍 호출, 대화 히스토리 관리
  embedding_service.py: 임베딩 (텍스트 → 벡터)
  rag_pipeline.py: 검색 결과 + 대화 히스토리를 조합해 이 서비스 호출
"""

from openai import OpenAI

CHAT_MODEL = "gpt-4o-mini"
MAX_HISTORY = 10  # 유지할 대화 쌍 수

def trim_conversation(conversation: list[dict]) -> None:
    """대화 히스토리를 MAX_HISTORY 쌍으로 제한 (in-place)"""
    max_messages = MAX_HISTORY * 2
    if len(conversation) > max_messages:
        del conversation[:-max_messages]


def stream_response(system_content: str, conversation: list[dict], user_message: str):
    """
    RAG + 대화 히스토리 기반 스트리밍 답변 생성

    Args:
        system_content: 컨텍스트가 주입된 시스템 프롬프트
        conversation:   대화 히스토리 리스트 (in-place 수정됨)
        user_message:   사용자 질문

    Yields:
        str: 텍스트 청크 (스트리밍 중)

    Side effects:
        - conversation에 user/assistant 메시지 추가
        - 반환값 last_usage 접근: stream_response 호출 후 .gi_frame.f_locals 불가
          → 대신 StopIteration.value 또는 별도 딕셔너리 활용 권장
    """
    conversation.append({"role": "user", "content": user_message})
    trim_conversation(conversation)

    messages = [{"role": "system", "content": system_content}] + conversation

    client = OpenAI()
    stream = client.chat.completions.create(
        model=CHAT_MODEL,
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
            yield text
        if hasattr(chunk, "usage") and chunk.usage:
            input_tokens = chunk.usage.prompt_tokens
            output_tokens = chunk.usage.completion_tokens

    conversation.append({"role": "assistant", "content": full_response})

    # 사용량 정보를 제너레이터 종료 후 읽을 수 있도록 저장
    # (호출부: rag_pipeline.py에서 _last_usage로 접근)
    stream_response._last_usage = {"input": input_tokens, "output": output_tokens}
