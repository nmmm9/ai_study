"""
1주차 과제: LLM API 연동 - 터미널 챗봇
OpenAI / Anthropic API를 활용한 1:1 대화 + Streaming
"""
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()
conversation = [
    {"role": "system", "content": "당신은 친절한 AI 어시스턴트입니다. 한국어로 답변합니다."}
]


def chat(user_input: str) -> str:
    """사용자 입력을 받아 GPT-4o로 스트리밍 응답을 출력한다."""
    conversation.append({"role": "user", "content": user_input})

    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=conversation,
        temperature=0.7,
        max_tokens=1024,
        stream=True,
    )

    full_response = ""
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="", flush=True)
            full_response += content

    print()  # 줄바꿈
    conversation.append({"role": "assistant", "content": full_response})
    return full_response


def main():
    print("=" * 50)
    print("  1주차 과제: LLM 터미널 챗봇 (GPT-4o)")
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
            conversation.append(
                {"role": "system", "content": "당신은 친절한 AI 어시스턴트입니다. 한국어로 답변합니다."}
            )
            print("대화가 초기화되었습니다.")
            continue

        print("[AI] ", end="")
        chat(user_input)


if __name__ == "__main__":
    main()
