"""Planner — decompose user query into ordered steps.

Each step is a single sub-task with a hinted domain. The Executor then
dispatches each step to the appropriate domain agent (reusing week09
infrastructure).
"""

import json
from datetime import datetime, timezone, timedelta
from openai import AsyncOpenAI

from config import SUPERVISOR_MODEL
from agents.supervisor import DOMAIN_DESCRIPTIONS

_client = AsyncOpenAI()
KST = timezone(timedelta(hours=9))

MAX_STEPS = 6


def _domain_text() -> str:
    return "\n".join(f"- {k}: {v}" for k, v in DOMAIN_DESCRIPTIONS.items())


async def planner_node(state: dict, model: str | None = None) -> dict:
    """Decompose the question into an ordered step plan."""
    model = model or SUPERVISOR_MODEL
    question = state["question"]
    history: list[dict] = state.get("history", []) or []
    now_dt = datetime.now(KST)
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    now = now_dt.strftime("%Y-%m-%d %H:%M (KST)")
    today_weekday = weekdays[now_dt.weekday()]
    from datetime import timedelta as _td
    yesterday = (now_dt - _td(days=1)).strftime("%Y-%m-%d") + f" ({weekdays[(now_dt - _td(days=1)).weekday()]})"
    last_sunday_delta = (now_dt.weekday() - 6) % 7 or 7
    last_sunday = (now_dt - _td(days=last_sunday_delta)).strftime("%Y-%m-%d")

    system = f"""당신은 멀티 에이전트 시스템의 Planner 입니다.
현재 시각: {now} {today_weekday}요일
어제: {yesterday}
직전 일요일: {last_sunday}

날짜 계산 규칙:
- "오늘", "어제", "지난주 ○요일" 같은 상대 날짜는 위 정보를 우선 사용하세요.
- 더 복잡한 날짜 계산이 필요하면 info 도메인의 date_arithmetic 도구를 사용하세요.
- calculate 도구는 수학 계산 전용입니다. "YYYY-MM-DD - 7" 같은 날짜 식은 금지.

사용자의 질문을 작은 단계로 분해해 실행 계획(plan)을 만드세요.
각 단계는 하나의 도메인 에이전트가 처리할 수 있는 단일 sub-task 여야 합니다.

도메인:
{_domain_text()}

규칙:
1. 단순 질문이면 1 단계 plan. 복합 질문이면 2~6 단계.
2. 각 단계는 명확하고 독립적이어야 함 (다음 단계가 이전 결과를 참조해도 OK).
3. 도구가 필요 없는 일반 대화면 빈 plan ([]) 반환.
4. 같은 도메인의 여러 sub-task 는 합치지 말고 명확히 분리.
5. 단계는 실행 순서대로 나열 (먼저 필요한 정보부터).

반드시 JSON 형식으로만 응답:
{{
  "reasoning": "왜 이렇게 분해했는지 한 문장",
  "steps": [
    {{"id": 1, "domain": "<도메인키>", "task": "<한 줄 sub-task 설명>"}}
  ]
}}
"""

    messages: list[dict] = [{"role": "system", "content": system}]
    for h in history[-6:]:
        role = h.get("role")
        content = h.get("content") or ""
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content[:600]})
    messages.append({"role": "user", "content": question})

    response = await _client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    content = response.choices[0].message.content or "{}"
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {}

    raw_steps = parsed.get("steps", []) or []
    reasoning = parsed.get("reasoning", "")

    valid_steps = []
    for i, s in enumerate(raw_steps[:MAX_STEPS]):
        if not isinstance(s, dict):
            continue
        dom = s.get("domain")
        task = (s.get("task") or "").strip()
        if not task:
            continue
        if dom not in DOMAIN_DESCRIPTIONS:
            dom = None
        valid_steps.append({
            "id": i + 1,
            "domain": dom,
            "task": task[:200],
            "status": "pending",
            "result": None,
        })

    return {
        "plan": valid_steps,
        "_reasoning": reasoning,
    }
