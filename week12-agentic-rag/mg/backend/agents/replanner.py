"""Replanner — revise the remaining plan based on completed step results.

Three possible outcomes:
1. continue — proceed to next pending step
2. revise   — replace remaining steps with a new plan
3. finish   — skip remaining steps, go to Writer
"""

import json
from openai import AsyncOpenAI

from config import SUPERVISOR_MODEL
from agents.supervisor import DOMAIN_DESCRIPTIONS

_client = AsyncOpenAI()

MAX_REPLAN = 2


def _format_completed(plan: list[dict]) -> str:
    lines = []
    for step in plan:
        if step.get("status") != "done":
            continue
        result = step.get("result") or {}
        snippet = ""
        if isinstance(result, dict):
            snippet = (result.get("summary") or "")[:300]
        elif isinstance(result, str):
            snippet = result[:300]
        lines.append(f"  [step {step['id']}] {step['task']}\n    → {snippet}")
    return "\n".join(lines) if lines else "  (완료된 단계 없음)"


def _format_remaining(plan: list[dict]) -> str:
    lines = []
    for step in plan:
        if step.get("status") in ("done", "skipped"):
            continue
        lines.append(f"  [step {step['id']}] [{step.get('domain') or '?'}] {step['task']}")
    return "\n".join(lines) if lines else "  (남은 단계 없음)"


async def replanner_node(state: dict, model: str | None = None) -> dict:
    """Decide whether to continue, revise, or finish."""
    model = model or SUPERVISOR_MODEL
    question = state["question"]
    plan = state.get("plan", []) or []

    completed = _format_completed(plan)
    remaining = _format_remaining(plan)
    domain_text = "\n".join(f"- {k}" for k in DOMAIN_DESCRIPTIONS.keys())

    system = f"""당신은 Plan-and-Execute 시스템의 Replanner 입니다.
완료된 단계의 결과를 보고, 남은 plan을 어떻게 할지 결정합니다.

세 가지 행동:
1. continue — 기존 plan 그대로 다음 pending 단계 진행 (가장 흔함)
2. revise   — 새 결과를 반영해 남은 단계를 교체
3. finish   — 정보 충분, 남은 단계 건너뛰고 답변 작성으로

도메인 키 (revise 시 사용):
{domain_text}

규칙:
- 기존 step 이 잘 수행되고 있으면 continue 가 기본
- 결과가 빈약하거나 새로운 정보가 추가 검색을 요구하면 revise
- 사용자 질문에 답하기 충분하면 finish (불필요 호출 방지)

반드시 JSON 형식으로만 응답:
{{
  "action": "continue" | "revise" | "finish",
  "reasoning": "한 문장 근거",
  "new_plan": [{{"id": N, "domain": "...", "task": "..."}}, ...]
}}
new_plan 은 action=revise 일 때만 채우세요.
"""

    user_block = f"""[사용자 질문]
{question}

[완료된 단계]
{completed}

[남은 단계]
{remaining}

위 진행 상황을 보고 어떻게 할지 결정하세요.
"""

    response = await _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_block},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    content = response.choices[0].message.content or "{}"
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {}

    action = parsed.get("action", "continue")
    if action not in ("continue", "revise", "finish"):
        action = "continue"
    reasoning = parsed.get("reasoning", "")

    new_plan_raw = parsed.get("new_plan", []) or []
    new_plan = []
    if action == "revise":
        next_id = max([s["id"] for s in plan] + [0]) + 1
        for s in new_plan_raw[:6]:
            if not isinstance(s, dict):
                continue
            task = (s.get("task") or "").strip()
            if not task:
                continue
            dom = s.get("domain")
            if dom not in DOMAIN_DESCRIPTIONS:
                dom = None
            new_plan.append({
                "id": next_id,
                "domain": dom,
                "task": task[:200],
                "status": "pending",
                "result": None,
            })
            next_id += 1

    return {
        "action": action,
        "new_plan": new_plan,
        "_reasoning": reasoning,
    }
