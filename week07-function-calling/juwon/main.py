"""
main.py - 여행 플래너 AI Agent 실행 진입점

실행 방법:
    python main.py
"""

from agent import SYSTEM_PROMPT, chat


def main():
    print("=" * 55)
    print("  ✈  여행 플래너 AI Agent  |  7주차 Function Calling")
    print("=" * 55)
    print("질문 예시:")
    print("  - 제주도 날씨 어때?")
    print("  - 부산 관광지 추천해줘")
    print("  - 경주 맛집 알려줘")
    print("  - 3박 4일 여행 예산 얼마야?")
    print("  - 서울 언제 가는 게 좋아?")
    print("\n종료하려면 'quit' 또는 'exit' 입력")
    print("-" * 55)

    # 대화 히스토리 초기화
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("\n나: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n여행 플래너를 종료합니다. 좋은 여행 되세요! ✈")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "종료", "q"):
            print("\n여행 플래너를 종료합니다. 좋은 여행 되세요! ✈")
            break

        # 사용자 메시지 추가
        messages.append({"role": "user", "content": user_input})

        # Agent 실행
        response, messages = chat(messages)
        print(f"\nAI: {response}")


if __name__ == "__main__":
    main()
