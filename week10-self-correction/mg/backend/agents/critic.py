"""Critic — Self-Correction agent.

Scores the writer's draft answer (1-10) and returns specific feedback.
If the score is below the threshold, the writer re-writes using the
critique. This is the core of the Self-Correction loop introduced in
week 10.

Scoring rubric (taught to the LLM via system prompt):
- 10: 도구 결과를 모두 정확히 반영 + 구조화된 자연스러운 답변
- 7-9: 대체로 정확하지만 구조나 누락된 정보가 있음
- 4-6: 일부 사실 오류, 또는 도구 결과 일부 무시
- 1-3: 도구 결과를 거의 활용 못 함, 또는 환각

Output format (strict JSON):
    {"score": 8, "passed": true, "issues": [...], "suggestions": [...]}
"""

import json
from openai import AsyncOpenAI

from config import DOMAIN_MODEL  # use mid-tier for critic — accuracy matters

_client = AsyncOpenAI()

PASS_THRESHOLD = 7  # answers scoring >= this are accepted
MAX_REVISIONS = 2   # writer can be re-invoked at most this many times


_CRITIC_SYSTEM = """당신은 K-Agent의 Critic 에이전트입니다.
다른 Writer가 작성한 답변을 검수해 1~10점으로 평가하고, 구체적인 피드백을 반환합니다.

평가 기준:
1. 도구 결과 활용도 — 수집된 정보를 모두 반영했는가? (가장 중요)
2. 사실 정확성 — 환각이나 잘못된 추론은 없는가?
3. 답변 구조 — 사용자 질문에 직접 답하는가? Markdown 활용?
4. 누락 — 사용자가 물어본 항목 중 빠뜨린 게 있는가?

점수:
- 10: 완벽 (모든 기준 충족)
- 7~9: 합격 (작은 보완 필요)
- 4~6: 재작성 필요 (사실 오류 또는 도구 결과 누락)
- 1~3: 심각한 문제 (환각 또는 결과 무시)

반드시 JSON 으로만 응답:
{
  "score": 8,
  "passed": true,
  "issues": ["문제점 1", "문제점 2"],
  "suggestions": ["개선 제안 1", "개선 제안 2"]
}

issues 가 비어 있으면 빈 배열로. 점수 7 미만이면 passed=false.
"""


def _format_tool_results(tool_results: list[dict]) -> str:
    if not tool_results:
        return "(도구 결과 없음)"
    out = []
    for r in tool_results:
        snippet = (r.get("result") or "")[:600]
        out.append(f"[{r['domain']}] {r['tool']}({r.get('args', {})})\n→ {snippet}")
    return "\n\n".join(out)


async def critic_node(
    question: str,
    draft_answer: str,
    tool_results: list[dict],
    iteration: int = 1,
    model: str | None = None,
) -> dict:
    """Score and critique the writer's draft. Returns:
        {score, passed, issues[], suggestions[], iteration}
    """
    model = model or DOMAIN_MODEL

    user_block = f"""[사용자 질문]
{question}

[Writer 가 수집한 도구 결과]
{_format_tool_results(tool_results)}

[Writer 의 초안 답변 — 이번 iteration: {iteration}]
{draft_answer}

위 답변을 평가하고 JSON 으로만 응답하세요.
"""

    response = await _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _CRITIC_SYSTEM},
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

    score = int(parsed.get("score", 5) or 5)
    passed = bool(parsed.get("passed", score >= PASS_THRESHOLD))
    issues = parsed.get("issues", []) or []
    suggestions = parsed.get("suggestions", []) or []

    return {
        "score": max(1, min(10, score)),
        "passed": passed,
        "issues": issues,
        "suggestions": suggestions,
        "iteration": iteration,
    }


def build_revision_feedback(critique: dict) -> str:
    """Format the critique as feedback the Writer can consume on re-write."""
    parts = ["[이전 답변에 대한 Critic 피드백]"]
    parts.append(f"점수: {critique.get('score')}/10 — 재작성 필요")

    issues = critique.get("issues") or []
    if issues:
        parts.append("\n발견된 문제:")
        for i, x in enumerate(issues, 1):
            parts.append(f"  {i}. {x}")

    suggestions = critique.get("suggestions") or []
    if suggestions:
        parts.append("\n개선 제안:")
        for i, x in enumerate(suggestions, 1):
            parts.append(f"  {i}. {x}")

    parts.append("\n위 피드백을 반영해 답변을 다시 작성하세요. 도구 결과를 더 정확히 반영하고, 환각을 제거하세요.")
    return "\n".join(parts)
