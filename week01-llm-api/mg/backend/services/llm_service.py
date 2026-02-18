import json
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI


AVAILABLE_MODELS = [
    {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
]

_openai_client = AsyncOpenAI()


async def stream_chat(
    messages: list[dict], model: str, temperature: float
) -> AsyncGenerator[str, None]:
    stream = await _openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True,
        stream_options={"include_usage": True},
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield f"data: {json.dumps({'content': chunk.choices[0].delta.content, 'done': False})}\n\n"

        if chunk.usage:
            yield f"data: {json.dumps({'content': '', 'done': True, 'usage': {'prompt_tokens': chunk.usage.prompt_tokens, 'completion_tokens': chunk.usage.completion_tokens, 'total_tokens': chunk.usage.total_tokens}})}\n\n"
