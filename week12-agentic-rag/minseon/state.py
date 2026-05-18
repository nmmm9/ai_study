"""
state.py
────────
week12 Agentic RAG 공유 상태

흐름:
  agent_node → search_tool_node → grade_docs_node
             ↘ generate_node          ↓ relevant
                                generate_node
                                      ↓ not relevant
                                rewrite_node → agent_node (재시도)
"""

from typing_extensions import TypedDict


class AgenticRAGState(TypedDict, total=False):
    question:           str    # 사용자 원본 질문
    rewritten_question: str    # 재작성된 검색 쿼리
    tool_calls:         list   # LLM이 요청한 tool call 정보
    documents:          list   # 검색된 정책 문서 목록
    grade:              str    # "relevant" | "not_relevant"
    answer:             str    # 최종 답변
    retry_count:        int    # 재시도 횟수 (무한루프 방지)
    execution_trace:    list   # [{"node": str, "summary": str}]
