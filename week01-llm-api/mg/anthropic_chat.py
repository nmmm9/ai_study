"""
1주차 과제: Anthropic API 연동 - 터미널 챗봇
Claude Sonnet 4.5를 활용한 1:1 대화 + Streaming
"""
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic()
conversation = []
SYSTEM_PROMPT = "당신은 친절한 AI 어시스턴트입니다. 한국어로 답변합니다."


def chat(user_input: str) -> str:
    """사용자 입력을 받아 Claude로 스트리밍 응답을 출력한다."""
    conversation.append({"role": "user", "content": user_input})

    full_response = ""
    with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=conversation,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text

    print()
    conversation.append({"role": "assistant", "content": full_response})
    return full_response


def main():
    print("=" * 50)
    print("  1주차 과제: LLM 터미널 챗봇 (Claude Sonnet 4.5)")
    print("  종료: quit / 대화 초기화: reset")
    print("=" * 50)

    while True:
        user_input = input("\n[나] ").strip()

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("챗봇을 종료합니다.")
            break
        if user_input.lower() == "reset":
            conversation.clear()
            print("대화가 초기화되었습니다.")
            continue

        print("[AI] ", end="")
        chat(user_input)


if __name__ == "__main__":
    main()
