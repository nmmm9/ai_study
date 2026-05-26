"""Document search tool — thin wrapper around the document_store.

The Retriever agent (agents/retriever.py) handles the agentic loop
(query rewriting, self-eval, re-search). This tool exists so that the
Planner can include a 'documents' step the same way it includes any
other domain step.

For simple cases (single search, no self-eval) the domain agent can
call this tool directly. The full agentic loop is invoked via the
Retriever agent in graph.py.
"""

import json
from tools.registry import register_tool
from services.document_store import search as vector_search, list_documents


@register_tool(
    name="document_search",
    description="업로드된 문서에서 키워드/질문 관련 내용을 검색합니다. ChromaDB 벡터 검색.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "검색할 질문 또는 키워드"},
            "top_k": {"type": "integer", "description": "반환할 chunk 수 (기본 5)", "default": 5},
        },
        "required": ["query"],
    },
)
async def document_search(query: str, top_k: int = 5) -> dict:
    chunks = await vector_search(query, top_k=top_k)
    if not chunks:
        return {
            "query": query,
            "count": 0,
            "results": [],
            "hint": "검색 결과 없음. 문서가 업로드되지 않았거나 키워드가 맞지 않을 수 있습니다.",
        }
    return {
        "query": query,
        "count": len(chunks),
        "results": [{
            "doc_name": c.doc_name,
            "page": c.page,
            "score": round(c.score or 0, 3),
            "chunk_index": c.chunk_index,
            "text": c.text[:600],
        } for c in chunks],
    }


@register_tool(
    name="list_uploaded_documents",
    description="현재 업로드되어 검색 가능한 문서 목록을 조회합니다.",
    parameters={"type": "object", "properties": {}},
)
async def list_uploaded_documents() -> dict:
    docs = list_documents()
    return {"count": len(docs), "documents": docs}
