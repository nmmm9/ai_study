import time
from dataclasses import dataclass

from openai import AsyncOpenAI

_client = AsyncOpenAI()

PRICING = {
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "embedding": 0.02 / 1_000_000,  # text-embedding-3-small
}


@dataclass
class LLMResponse:
    answer: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    time_ms: int
    cost_usd: float


async def ask_with_context(
    question: str, context: str, model: str = "gpt-4o-mini"
) -> LLMResponse:
    start_time = time.perf_counter()

    response = await _client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "다음 문서를 참고하여 질문에 답변하세요.\n\n"
                    f"---\n{context}\n---"
                ),
            },
            {"role": "user", "content": question},
        ],
        temperature=0.3,
    )

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    usage = response.usage
    pricing = PRICING.get(model, PRICING["gpt-4o-mini"])
    cost = (
        usage.prompt_tokens * pricing["input"]
        + usage.completion_tokens * pricing["output"]
    )

    return LLMResponse(
        answer=response.choices[0].message.content,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
        time_ms=elapsed_ms,
        cost_usd=round(cost, 6),
    )
