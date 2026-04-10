"""Shared utilities for RAG pipelines."""

SYSTEM_PROMPT = (
    "다음 문서를 참고하여 질문에 답변하세요. "
    "문서 내용을 기반으로 자세하고 친절하게 답변하세요. "
    "문서에 직접적인 답이 없더라도 관련 내용이 있다면 참고하여 답변하세요. "
    "문서와 완전히 관련 없는 질문에만 '해당 문서에서 관련 정보를 찾지 못했습니다'라고 답하세요."
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
