"""
1주차 과제: Anthropic Claude API 연동 - 터미널 챗봇
Claude API를 활용한 1:1 대화 + Streaming + 토큰 관리
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic()

# ── 설정 ──────────────────────────────────────────────
SYSTEM_PROMPT = "당신은 친절한 AI 어시스턴트입니다. 한국어로 답변합니다."
MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 1024
MAX_MESSAGES = 20  # Sliding Window: 최근 N개 메시지만 유지
MAX_TOTAL_CHARS = 8000  # 대화 히스토리 최대 글자 수 (토큰 근사치 관리용)

# ── 상태 ──────────────────────────────────────────────
conversation: list[dict] = []
total_input_tokens = 0
total_output_tokens = 0


def estimate_tokens(text: str) -> int:
    """한국어 기준 토큰 수 추정 (글자수 × 1.5 근사치)"""
    return int(len(text) * 1.5)


def get_conversation_chars() -> int:
    """현재 대화 히스토리의 총 글자 수"""
    return sum(len(msg["content"]) for msg in conversation)


def trim_conversation():
    """토큰 관리: Sliding Window + 글자 수 기반 제한"""
    global conversation

    # 1) 메시지 개수 제한
    if len(conversation) > MAX_MESSAGES:
        conversation = conversation[-MAX_MESSAGES:]

    # 2) 글자 수 기반 제한 (오래된 메시지부터 제거)
    while get_conversation_chars() > MAX_TOTAL_CHARS and len(conversation) > 2:
        conversation.pop(0)


def chat(user_input: str) -> str:
    """Streaming 방식으로 Claude와 대화"""
    global total_input_tokens, total_output_tokens

    conversation.append({"role": "user", "content": user_input})
    trim_conversation()

    full_response = ""
    with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=conversation,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text

    print()

    # 토큰 사용량 기록
    usage = stream.get_final_message().usage
    total_input_tokens += usage.input_tokens
    total_output_tokens += usage.output_tokens
    print(f"  [이번 응답: 입력 {usage.input_tokens} / 출력 {usage.output_tokens} 토큰]")

    conversation.append({"role": "assistant", "content": full_response})
    return full_response


def show_usage():
    """누적 토큰 사용량 출력"""
    print(f"\n── 토큰 사용량 ──")
    print(f"  누적 입력: {total_input_tokens} 토큰")
    print(f"  누적 출력: {total_output_tokens} 토큰")
    print(f"  총 합계:   {total_input_tokens + total_output_tokens} 토큰")
    print(f"  대화 메시지 수: {len(conversation)}개")
    print(f"  대화 히스토리 글자 수: {get_conversation_chars()}자\n")


def main():
    print("╔══════════════════════════════════════╗")
    print("║   Claude 1:1 채팅 (Streaming 모드)   ║")
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
