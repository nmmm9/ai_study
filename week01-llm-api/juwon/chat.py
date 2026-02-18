"""
1주차 과제: OpenAI GPT API 연동 - 터미널 챗봇
GPT-4o-mini를 활용한 1:1 대화 + Streaming + 토큰 관리
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class ChatBot:
    """OpenAI GPT 기반 터미널 챗봇"""

    MODEL = "gpt-4o-mini"
    SYSTEM_PROMPT = "당신은 친절한 AI 어시스턴트입니다. 한국어로 답변합니다."
    MAX_HISTORY_TURNS = 10     # 유지할 최대 대화 턴 수 (user + assistant 쌍)
    MAX_RESPONSE_TOKENS = 1024

    def __init__(self):
        self.client = OpenAI()
        self.history: list[dict] = []  # {"role": "user"/"assistant", "content": "..."}
        self.token_usage = {"input": 0, "output": 0}

    # ── 대화 히스토리 관리 ────────────────────────────────

    def _trim_history(self):
        """오래된 대화 제거: 최근 N턴(user+assistant 쌍)만 유지"""
        max_messages = self.MAX_HISTORY_TURNS * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def _build_messages(self) -> list[dict]:
        """API에 전달할 messages 배열 구성 (system + history)"""
        return [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            *self.history,
        ]

    # ── API 호출 ──────────────────────────────────────────

    def send(self, user_input: str) -> str:
        """사용자 메시지를 보내고 스트리밍으로 응답 받기"""
        self.history.append({"role": "user", "content": user_input})
        self._trim_history()

        reply = ""
        input_tokens = 0
        output_tokens = 0

        stream = self.client.chat.completions.create(
            model=self.MODEL,
            max_tokens=self.MAX_RESPONSE_TOKENS,
            messages=self._build_messages(),
            stream=True,
            stream_options={"include_usage": True},  # 마지막 청크에 실제 토큰 수 포함
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                print(text, end="", flush=True)
                reply += text
            if chunk.usage:  # 마지막 청크에서 토큰 수 수집
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens

        print()

        self.token_usage["input"] += input_tokens
        self.token_usage["output"] += output_tokens
        print(f"  [토큰: 입력 {input_tokens} / 출력 {output_tokens}]")

        self.history.append({"role": "assistant", "content": reply})
        return reply

    # ── 유틸리티 ──────────────────────────────────────────

    def reset(self):
        """대화 히스토리 초기화"""
        self.history.clear()

    def print_usage(self):
        """누적 토큰 사용량 출력"""
        total = self.token_usage["input"] + self.token_usage["output"]
        print(f"\n── 누적 토큰 사용량 ──")
        print(f"  입력:  {self.token_usage['input']} 토큰")
        print(f"  출력:  {self.token_usage['output']} 토큰")
        print(f"  합계:  {total} 토큰")
        print(f"  대화:  {len(self.history) // 2}턴\n")


# ── 메인 루프 ─────────────────────────────────────────────

def main():
    bot = ChatBot()

    print("┌─────────────────────────────────┐")
    print("│   GPT-4o-mini 터미널 챗봇       │")
    print("├─────────────────────────────────┤")
    print("│  quit  → 종료                   │")
    print("│  reset → 대화 초기화            │")
    print("│  usage → 토큰 사용량 확인       │")
    print("└─────────────────────────────────┘\n")

    while True:
        try:
            user_input = input("나: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            bot.print_usage()
            break

        if not user_input:
            continue

        match user_input.lower():
            case "quit":
                bot.print_usage()
                print("종료합니다.")
                break
            case "reset":
                bot.reset()
                print("대화를 초기화했습니다.\n")
            case "usage":
                bot.print_usage()
            case _:
                print("AI: ", end="")
                bot.send(user_input)
                print()


if __name__ == "__main__":
    main()
