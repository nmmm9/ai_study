"""
1주차 과제: OpenAI GPT API 연동 - 프록시 방식 터미널 챗봇

[실무에서 쓰는 프록시 패턴]
- 클라이언트(이 코드)는 프록시 서버 URL + 프록시 키만 알고 있음
- 프록시 서버가 실제 OpenAI API 키를 들고 있음
- 장점: API 키 중앙 관리, 요청 로깅, 비용 제어, Rate Limit 관리 가능

[지원하는 프록시 종류]
- LiteLLM  : 오픈소스 프록시, 여러 LLM을 하나의 엔드포인트로 통합
- Azure OpenAI : Azure를 통해 OpenAI 모델 사용
- OpenRouter : 다양한 LLM을 OpenAI 호환 API로 제공
- 사내 게이트웨이 : 기업이 직접 구축한 API 게이트웨이
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ── 프록시 설정 ────────────────────────────────────────────
# 아래 값만 바꾸면 어떤 프록시든 연결 가능
PROXY_BASE_URL = os.getenv("PROXY_BASE_URL", "https://api.openai.com/v1")
PROXY_API_KEY  = os.getenv("PROXY_API_KEY", os.getenv("OPENAI_API_KEY"))

# OpenAI 호환 클라이언트: base_url만 바꾸면 프록시로 전환됨
#
# [직접 연결]  base_url="https://api.openai.com/v1"   (기본값)
# [LiteLLM]   base_url="http://localhost:4000"
# [Azure]     base_url="https://<리소스명>.openai.azure.com/openai/deployments/<모델명>"
# [OpenRouter] base_url="https://openrouter.ai/api/v1"
client = OpenAI(
    api_key=PROXY_API_KEY,
    base_url=PROXY_BASE_URL,
)


class ChatBot:
    """프록시 서버를 통해 GPT와 대화하는 터미널 챗봇"""

    MODEL = os.getenv("MODEL", "gpt-4o-mini")  # 프록시에 따라 모델명이 달라질 수 있음
    SYSTEM_PROMPT = "당신은 친절한 AI 어시스턴트입니다. 한국어로 답변합니다."
    MAX_HISTORY_TURNS = 10
    MAX_RESPONSE_TOKENS = 1024

    def __init__(self):
        self.history: list[dict] = []
        self.token_usage = {"input": 0, "output": 0}

    def _trim_history(self):
        max_messages = self.MAX_HISTORY_TURNS * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def _build_messages(self) -> list[dict]:
        return [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            *self.history,
        ]

    def send(self, user_input: str) -> str:
        """프록시 서버를 통해 메시지 전송 및 스트리밍 응답 수신"""
        self.history.append({"role": "user", "content": user_input})
        self._trim_history()

        reply = ""
        input_tokens = 0
        output_tokens = 0

        stream = client.chat.completions.create(
            model=self.MODEL,
            max_tokens=self.MAX_RESPONSE_TOKENS,
            messages=self._build_messages(),
            stream=True,
            stream_options={"include_usage": True},
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                print(text, end="", flush=True)
                reply += text
            if chunk.usage:
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens

        print()

        self.token_usage["input"] += input_tokens
        self.token_usage["output"] += output_tokens
        print(f"  [토큰: 입력 {input_tokens} / 출력 {output_tokens}]")

        self.history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self):
        self.history.clear()

    def print_usage(self):
        total = self.token_usage["input"] + self.token_usage["output"]
        print(f"\n── 누적 토큰 사용량 ──")
        print(f"  입력:  {self.token_usage['input']} 토큰")
        print(f"  출력:  {self.token_usage['output']} 토큰")
        print(f"  합계:  {total} 토큰")
        print(f"  대화:  {len(self.history) // 2}턴\n")


def main():
    bot = ChatBot()

    print("┌──────────────────────────────────────┐")
    print("│   GPT-4o-mini 터미널 챗봇 (프록시)   │")
    print("├──────────────────────────────────────┤")
    print(f"│  프록시: {PROXY_BASE_URL[:30]:<30}│")
    print(f"│  모델:   {ChatBot.MODEL:<30}│")
    print("├──────────────────────────────────────┤")
    print("│  quit  → 종료                        │")
    print("│  reset → 대화 초기화                 │")
    print("│  usage → 토큰 사용량 확인            │")
    print("└──────────────────────────────────────┘\n")

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
