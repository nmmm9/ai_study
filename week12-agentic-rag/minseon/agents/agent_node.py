"""
agent_node.py
─────────────
Agentic RAG의 핵심 — LLM이 스스로 검색 여부를 결정합니다.

- 질문을 보고 RAG 검색(search_policy tool)이 필요한지 판단
- 필요하면 tool_call 반환 → search_tool_node로 이동
- 충분히 알면 직접 답변 → generate_node로 이동
"""

import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from openai import OpenAI
from state import AgenticRAGState
from tools.rag_tool import SEARCH_TOOL

_client = OpenAI()

_SYSTEM = """\
당신은 청년정책 전문 AI입니다.
사용자의 질문에 답하기 위해 필요하다면 search_policy 도구를 호출하세요.

판단 기준:
- 특정 정책의 조건, 금액, 기간, 중복 수혜 여부 → 반드시 검색
- 일반적인 정책 추천, 탐색 → 검색 후 답변
- 이미 검색 결과가 충분히 제공된 경우 → 직접 답변

검색 시 키워드는 구체적으로 설정하세요.
"""


def agent_node(state: AgenticRAGState) -> dict:
    """LLM이 검색 여부를 결정하는 에이전트 노드."""
    question  = state.get("rewritten_question") or state.get("question", "")
    documents = state.get("documents", [])
    retry     = state.get("retry_count", 0)

    messages = [{"role": "system", "content": _SYSTEM}]

    # 이미 검색 결과가 있으면 컨텍스트로 제공
    if documents:
        ctx = "\n\n".join(
            f"### {d['title']}\n{d['content'][:1000]}" for d in documents
        )
        messages.append({
            "role": "user",
            "content": f"질문: {question}\n\n현재 검색된 문서:\n{ctx}",
        })
    else:
        messages.append({"role": "user", "content": question})

    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=[SEARCH_TOOL],
        tool_choice="auto",
        max_tokens=500,
    )

    msg       = resp.choices[0].message
    tool_calls = msg.tool_calls or []

    tc_summary = f"{len(tool_calls)}개 tool call" if tool_calls else "직접 답변 선택"
    print(f"[agent_node] retry={retry} | {tc_summary}")

    trace = list(state.get("execution_trace", []))
    trace.append({"node": "agent_node", "summary": tc_summary})

    return {
        "tool_calls":      [tc.model_dump() for tc in tool_calls],
        "retry_count":     retry,
        "execution_trace": trace,
    }


def route_agent(state: AgenticRAGState) -> str:
    """tool call 여부에 따라 분기."""
    return "search" if state.get("tool_calls") else "generate"
