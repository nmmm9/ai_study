"""Writer — composes the final answer from all domain agents' tool results.

The writer never calls tools. It receives the user question + all
collected tool_results and streams a coherent Korean answer.
"""

from datetime import datetime, timezone, timedelta
from openai import AsyncOpenAI

from config import WRITER_MODEL

_client = AsyncOpenAI()
KST = timezone(timedelta(hours=9))


def _format_tool_results(tool_results: list[dict]) -> str:
    if not tool_results:
        return "(수집된 도구 결과 없음)"
    blocks = []
    for r in tool_results:
        blocks.append(
            f"[{r['domain']}] {r['tool']}({r.get('args', {})})\n→ {r['result'][:1200]}"
        )
    return "\n\n".join(blocks)


async def writer_stream(
    question: str,
    tool_results: list[dict],
    model: str | None = None,
    history: list[dict] | None = None,
    revision_feedback: str | None = None,
    previous_draft: str | None = None,
):
    """Stream the final answer token by token.

    When `revision_feedback` is provided, this is a re-write triggered by
    the Critic. The writer must address the feedback explicitly.
    """
    model = model or WRITER_MODEL
    history = history or []
    now = datetime.now(KST).strftime("%Y년 %m월 %d일 %H:%M")

    is_revision = bool(revision_feedback)

    system = f"""당신은 K-Agent의 Writer 에이전트입니다.
다른 도메인 에이전트들이 수집한 정보를 바탕으로 최종 답변을 작성합니다.

원칙:
- 한국어로 자연스럽게 답변
- Markdown 사용 (제목, 목록, 굵은 글씨 적극 활용)
- 도구가 호출되지 않은 경우 모델 지식만으로 답변
- 도구 결과가 비어있으면 솔직히 '결과 없음'이라 답변
- 답변에 도구 이름을 직접 노출하지 마세요 (자연스럽게 정보만 전달)
- 이전 대화 내용을 자연스럽게 이어가세요 (필요하면 참고)

현재 시각: {now} (KST)"""

    if is_revision:
        system += "\n\n중요: 이번 호출은 재작성입니다. Critic 피드백을 반영해 이전 답변의 결함을 모두 고치세요."

    user_parts = [
        "[사용자 질문]",
        question,
        "",
        "[수집된 정보]",
        _format_tool_results(tool_results),
    ]

    if is_revision and previous_draft:
        user_parts.extend([
            "",
            "[이전 초안 — 이걸 개선하세요]",
            previous_draft[:2000],
        ])

    if revision_feedback:
        user_parts.extend(["", revision_feedback])

    user_parts.extend(["", "위 정보를 종합해 최종 답변을 작성하세요."])
    user_block = "\n".join(user_parts)

    msgs: list[dict] = [{"role": "system", "content": system}]
    for h in history[-6:]:
        role = h.get("role")
        content = h.get("content") or ""
        if role in ("user", "assistant") and content:
            msgs.append({"role": role, "content": content[:500]})
    msgs.append({"role": "user", "content": user_block})

    stream = await _client.chat.completions.create(
        model=model,
        messages=msgs,
        temperature=0.4,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
