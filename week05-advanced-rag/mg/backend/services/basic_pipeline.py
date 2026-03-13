"""Basic RAG Pipeline (baseline from week 4).

Question → Embed → Vector Search → LLM Generate
"""

from services.embedding_service import embed_single
from services import vector_store
from services.llm_service import ask_with_context

SYSTEM_PROMPT = (
    "다음 문서를 참고하여 질문에 답변하세요. "
    "문서에 없는 내용은 '문서에 해당 정보가 없습니다'라고 답하세요."
)


def _format_context(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{i + 1}] {c['text']}" for i, c in enumerate(chunks)
    )


async def run_basic_rag(
    question: str,
    collection_name: str,
    top_k: int = 5,
    model: str = "gpt-4o-mini",
) -> dict:
    """Basic RAG: question → embed → search → generate."""
    steps = []

    # Step 1: Embed question
    query_emb, embed_ms = await embed_single(question)
    steps.append({
        "name": "embed",
        "label": "질문 임베딩",
        "time_ms": embed_ms,
    })

    # Step 2: Vector search
    results, search_ms = vector_store.search(collection_name, query_emb, top_k)
    chunks = [
        {"index": r.index, "text": r.text, "score": round(r.score, 4)}
        for r in results
    ]
    steps.append({
        "name": "search",
        "label": "벡터 검색",
        "time_ms": search_ms,
        "detail": f"{len(chunks)}개 청크 검색됨",
    })

    # Step 3: Generate
    context = _format_context(chunks)
    llm_result = await ask_with_context(
        question, context, model, system_prompt=SYSTEM_PROMPT
    )
    steps.append({
        "name": "generate",
        "label": "LLM 생성",
        "time_ms": llm_result.time_ms,
    })

    total_ms = embed_ms + search_ms + llm_result.time_ms

    return {
        "answer": llm_result.answer,
        "sources": chunks,
        "steps": steps,
        "timing": {
            "embed_ms": embed_ms,
            "search_ms": search_ms,
            "llm_ms": llm_result.time_ms,
            "total_ms": total_ms,
        },
        "cost_usd": llm_result.cost_usd,
        "total_tokens": llm_result.total_tokens,
        "mode": "basic",
    }
