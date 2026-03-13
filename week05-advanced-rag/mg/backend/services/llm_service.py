import time
from dataclasses import dataclass

from openai import AsyncOpenAI

_client = AsyncOpenAI()

PRICING = {
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "embedding": 0.02 / 1_000_000,
}


@dataclass
class LLMResponse:
    answer: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    time_ms: int
    cost_usd: float


def _calc_cost(usage, model: str) -> float:
    pricing = PRICING.get(model, PRICING["gpt-4o-mini"])
    return usage.prompt_tokens * pricing["input"] + usage.completion_tokens * pricing["output"]


async def ask_with_context(
    question: str,
    context: str,
    model: str = "gpt-4o-mini",
    system_prompt: str | None = None,
) -> LLMResponse:
    start_time = time.perf_counter()

    sys_content = system_prompt or "다음 문서를 참고하여 질문에 답변하세요."
    sys_content += f"\n\n---\n{context}\n---"

    response = await _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_content},
            {"role": "user", "content": question},
        ],
        temperature=0.3,
    )

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    usage = response.usage
    cost = _calc_cost(usage, model)

    return LLMResponse(
        answer=response.choices[0].message.content,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
        time_ms=elapsed_ms,
        cost_usd=round(cost, 6),
    )


async def ask_json(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0,
    max_tokens: int = 1024,
) -> tuple[str, int, float]:
    """LLM call expecting JSON response. Returns (content, time_ms, cost_usd)."""
    start_time = time.perf_counter()

    response = await _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    usage = response.usage
    cost = round(_calc_cost(usage, model), 6)

    return response.choices[0].message.content, elapsed_ms, cost


async def ask_short(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 300,
) -> tuple[str, int, float]:
    """Short LLM call (e.g. HyDE). Returns (content, time_ms, cost_usd)."""
    start_time = time.perf_counter()

    response = await _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    usage = response.usage
    cost = round(_calc_cost(usage, model), 6)

    return response.choices[0].message.content, elapsed_ms, cost
