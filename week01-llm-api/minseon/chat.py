"""
터미널 챗봇 - CLI

[관심사 분리]
  이 파일: 터미널 출력, 명령어 처리, 상태(conversation, tokens) 관리
  services/llm_service.py: OpenAI 클라이언트, 설정값, 대화 유틸 함수
"""

from dotenv import load_dotenv

from services.llm_service import (
    client, MODEL, MAX_TOKENS, SYSTEM_PROMPT,
    get_conversation_chars, trim_conversation,
)

load_dotenv()

# ── 상태 ──────────────────────────────────────────────
conversation: list[dict] = []
total_input_tokens = 0
total_output_tokens = 0


def chat(user_input: str) -> str:
    """Streaming 방식으로 GPT와 대화"""
    global total_input_tokens, total_output_tokens

    conversation.append({"role": "user", "content": user_input})
    trim_conversation(conversation)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation

    full_response = ""
    stream = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True},
    )

    input_tokens = 0
    output_tokens = 0
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            print(text, end="", flush=True)
            full_response += text
        if chunk.usage:
            input_tokens = chunk.usage.prompt_tokens
            output_tokens = chunk.usage.completion_tokens

    print()

    total_input_tokens += input_tokens
    total_output_tokens += output_tokens
    print(f"  [이번 응답: 입력 {input_tokens} / 출력 {output_tokens} 토큰]")

    conversation.append({"role": "assistant", "content": full_response})
    return full_response


def show_usage():
    """누적 토큰 사용량 출력"""
    print(f"\n── 토큰 사용량 ──")
    print(f"  누적 입력: {total_input_tokens} 토큰")
    print(f"  누적 출력: {total_output_tokens} 토큰")
    print(f"  총 합계:   {total_input_tokens + total_output_tokens} 토큰")
    print(f"  대화 메시지 수: {len(conversation)}개")
    print(f"  대화 히스토리 글자 수: {get_conversation_chars(conversation)}자\n")


def main():
    print("╔══════════════════════════════════════╗")
    print("║   GPT-4o 1:1 채팅 (Streaming 모드)  ║")
    print("╠══════════════════════════════════════╣")
    print("║  명령어:                             ║")
    print("║    quit  - 종료                      ║")
    print("║    reset - 대화 초기화               ║")
    print("║    usage - 토큰 사용량 확인          ║")
    print("╚══════════════════════════════════════╝")
    print()

    while True:
        try:
            user_input = input("[나] ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            show_usage()
            print("종료합니다.")
            break

        if user_input.lower() == "reset":
            conversation.clear()
            print("대화가 초기화되었습니다.\n")
            continue

        if user_input.lower() == "usage":
            show_usage()
            continue

        print("[AI] ", end="")
        chat(user_input)
        print()


if __name__ == "__main__":
    main()
