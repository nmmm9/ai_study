"""HyDE — Hypothetical Document Embeddings.

Generate a hypothetical answer to the question,
then embed that hypothetical (instead of the raw question)
so the search vector is closer to actual document content.
"""

from services.llm_service import ask_short

HYDE_SYSTEM = (
    "다음 질문에 대한 가상의 답변을 작성하세요. "
    "실제 문서에 있을 법한 정보성 텍스트를 2-3문장으로 작성하세요. "
    "확실하지 않은 내용은 포함하지 마세요. "
    "답변만 작성하고, 다른 설명은 하지 마세요."
)


async def generate_hypothetical(
    question: str,
    model: str = "gpt-4o-mini",
) -> tuple[str, int, float]:
    """Generate a hypothetical document for HyDE.

    Returns: (hypothetical_text, time_ms, cost_usd)
    """
    return await ask_short(
        system_prompt=HYDE_SYSTEM,
        user_prompt=question,
        model=model,
        temperature=0.7,
        max_tokens=200,
    )
