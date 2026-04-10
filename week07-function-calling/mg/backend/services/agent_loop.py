"""Agent Loop — OpenAI Function Calling with tool execution.

Flow:
1. User message + tool schemas → LLM
2. LLM returns tool_calls → execute each tool
3. Tool results → back to LLM
4. Repeat until LLM responds with text (no more tool calls)
5. Stream final response
"""

import json
from datetime import datetime, timezone, timedelta
from openai import AsyncOpenAI
from tools.registry import get_all_tools, execute_tool

_client = AsyncOpenAI()

KST = timezone(timedelta(hours=9))


def _build_system_prompt() -> str:
    now = datetime.now(KST)
    weekday = ["월", "화", "수", "목", "금", "토", "일"][now.weekday()]
    today = now.strftime(f"%Y년 %m월 %d일 ({weekday})")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    return f"""당신은 한국 생활 도우미 AI 에이전트 'K-Agent'입니다.

현재 날짜: {today}
현재 시간: {now.strftime("%H:%M")} (KST)
어제 날짜: {yesterday}

사용자의 질문에 답하기 위해 다양한 한국 도구를 사용할 수 있습니다.
도구가 필요하면 적절한 도구를 호출하고, 결과를 바탕으로 자연스럽게 답변하세요.
도구가 필요 없는 일반 대화에는 바로 답변하세요.

답변 규칙:
- "오늘", "어제", "이번 주" 등 상대적 날짜는 위의 현재 날짜를 기준으로 계산하세요
- 도구 결과를 그대로 나열하지 말고, 사용자에게 친절하게 정리해서 전달하세요
- 여러 도구를 조합해야 하면 순서대로 호출하세요
- 한국어로 답변하세요"""

MAX_TOOL_ROUNDS = 5


async def agent_stream(
    question: str,
    model: str = "gpt-4o-mini",
    history: list[dict] | None = None,
):
    """Agent loop with function calling. Yields (event_type, data)."""
    messages = [{"role": "system", "content": _build_system_prompt()}]
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": question})

    tools = get_all_tools()
    tool_round = 0

    while tool_round < MAX_TOOL_ROUNDS:
        response = await _client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools if tools else None,
            temperature=0.3,
        )

        choice = response.choices[0]

        # If LLM wants to call tools
        if choice.finish_reason == "tool_calls" or (choice.message.tool_calls and len(choice.message.tool_calls) > 0):
            tool_round += 1

            # Add assistant message with tool_calls
            messages.append(choice.message.model_dump())

            for tool_call in choice.message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                yield "tool_call", {
                    "name": fn_name,
                    "arguments": fn_args,
                    "round": tool_round,
                }

                # Execute tool
                result = await execute_tool(fn_name, fn_args)

                yield "tool_result", {
                    "name": fn_name,
                    "result": result[:500],
                }

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            continue

        # LLM responded with text — stream it
        # Re-call with streaming for the final response
        stream = await _client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools if tools else None,
            temperature=0.3,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield "token", delta.content

        yield "done", None
        return

    # Max rounds reached — force a text response
    messages.append({
        "role": "user",
        "content": "도구 호출 한도에 도달했습니다. 지금까지의 정보로 답변해주세요.",
    })

    stream = await _client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield "token", delta.content

    yield "done", None
