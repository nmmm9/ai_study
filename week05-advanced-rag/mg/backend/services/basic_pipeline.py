"""Basic RAG Pipeline (baseline from week 4).

Question → Embed → Vector Search → LLM Generate
"""

from services.embedding_service import embed_single
from services import vector_store
from services.llm_service import ask_with_context
from services.rag_utils import SYSTEM_PROMPT, format_context, chunks_from_results


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
    chunks = chunks_from_results(results)
    steps.append({
        "name": "search",
        "label": "벡터 검색",
        "time_ms": search_ms,
        "detail": f"{len(chunks)}개 청크 검색됨",
    })

    # Step 3: Generate
    context = format_context(chunks)
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
