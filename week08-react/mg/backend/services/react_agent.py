"""ReAct Agent — Reasoning + Acting loop with explicit Thought traces.

Unlike week07 Function Calling (LLM decides internally):
- Every step has a visible Thought (why this tool? what am I thinking?)
- Action (tool call) follows the Thought
- Observation (tool result) feeds back into next Thought
- Loop continues until LLM decides to give final Answer

Thought → Action → Observation → Thought → ... → Answer
"""

import json
from datetime import datetime, timezone, timedelta
from openai import AsyncOpenAI
from tools.registry import get_all_tools, execute_tool

_client = AsyncOpenAI()

KST = timezone(timedelta(hours=9))
MAX_ROUNDS = 7


def _build_system_prompt() -> str:
    now = datetime.now(KST)
    weekday = ["월", "화", "수", "목", "금", "토", "일"][now.weekday()]
    today = now.strftime(f"%Y년 %m월 %d일 ({weekday})")

    return f"""당신은 한국 생활 도우미 AI 에이전트 'K-Agent'입니다.

현재 날짜: {today}
현재 시간: {now.strftime("%H:%M")} (KST)

당신은 ReAct(Reasoning + Acting) 패턴으로 동작합니다.
모든 행동 전에 반드시 추론 과정을 설명하세요.

## 응답 규칙

1. 도구를 호출하기 전에, 먼저 왜 그 도구를 선택하는지 짧게 설명하세요.
   예: "사용자가 로또 당첨번호를 물어봤으니 lotto_results를 호출하겠습니다."

2. 도구 결과를 받은 후, 결과를 분석하고 추가 행동이 필요한지 판단하세요.
   예: "로또 결과를 받았습니다. 1218회 당첨번호는..."

3. 모든 정보가 충분하면 최종 답변을 생성하세요.

4. 여러 도구가 필요하면, 각 단계마다 추론을 먼저 하고 행동하세요.

5. 한국어로 자연스럽게 답변하세요."""


async def react_stream(
    question: str,
    model: str = "gpt-4o-mini",
    history: list[dict] | None = None,
):
    """ReAct agent loop. Yields (event_type, data) tuples.

    Event types:
    - "thought": LLM's reasoning before action
    - "action": tool call details
    - "observation": tool result
    - "token": streaming final answer token
    - "done": end of response
    """
    messages = [{"role": "system", "content": _build_system_prompt()}]
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": question})

    tools = get_all_tools()
    round_num = 0

    while round_num < MAX_ROUNDS:
        round_num += 1

        response = await _client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools if tools else None,
            temperature=0.3,
        )

        choice = response.choices[0]
        msg = choice.message

        # Case 1: LLM wants to call tools (with optional reasoning text)
        if msg.tool_calls and len(msg.tool_calls) > 0:
            # Extract Thought from content (LLM's reasoning before tool call)
            if msg.content:
                yield "thought", {
                    "round": round_num,
                    "text": msg.content,
                }

            # Add assistant message to history
            messages.append(msg.model_dump())

            # Execute each tool call
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                # Yield Action
                yield "action", {
                    "round": round_num,
                    "tool": fn_name,
                    "arguments": fn_args,
                }

                # Execute tool
                result = await execute_tool(fn_name, fn_args)

                # Yield Observation
                yield "observation", {
                    "round": round_num,
                    "tool": fn_name,
                    "result": result[:800],
                }

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            continue

        # Case 2: LLM responds with text only (final answer or direct response)
        # If there's content, it might include final reasoning + answer
        if msg.content:
            # Check if content has a thought + answer structure
            content = msg.content

            # Yield final thought if this is after tool calls
            if round_num > 1:
                yield "thought", {
                    "round": round_num,
                    "text": "충분한 정보를 모았습니다. 최종 답변을 생성합니다.",
                }

        # Stream the final answer
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

    # Max rounds reached
    yield "thought", {"round": round_num, "text": "최대 추론 횟수에 도달했습니다. 현재까지의 정보로 답변합니다."}

    messages.append({
        "role": "user",
        "content": "지금까지 수집한 정보를 바탕으로 최종 답변을 해주세요.",
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
