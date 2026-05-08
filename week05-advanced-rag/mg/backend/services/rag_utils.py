"""Shared utilities for RAG pipelines."""

SYSTEM_PROMPT = (
    "다음 문서를 참고하여 질문에 답변하세요. "
    "문서에 없는 내용은 '문서에 해당 정보가 없습니다'라고 답하세요."
)


def format_context(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{i + 1}] {c['text']}" for i, c in enumerate(chunks)
    )


def chunks_from_results(results) -> list[dict]:
    return [
        {"index": r.index, "text": r.text, "score": round(r.score, 4)}
        for r in results
    ]
