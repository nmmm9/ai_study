"""
agentic_rag.py - System C: Agentic RAG

12주차 방식:
  질문 → LLM 판단 → RAG 도구 호출 → 결과 평가 → 재검색 or 답변
  LangGraph ReAct 에이전트가 스스로 검색 여부/횟수 결정

특징: 자율적 판단, 필요시 재검색, 도구 호출 기록 남김
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from systems.base import vector_search, build_context

_llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY", ""))


@tool
def search_trend_history(query: str) -> str:
    """과거 GitHub 트렌드 분석 결과에서 관련 정보를 검색합니다."""
    results = vector_search(query, limit=3)
    if not results:
        return "관련 과거 분석 데이터가 없습니다."
    return build_context(results)


@tool
def get_recent_trends(limit: int = 3) -> str:
    """최근 N번의 트렌드 분석 요약을 가져옵니다."""
    from systems.base import get_supabase
    sb = get_supabase()
    result = (
        sb.table("trend_reports")
        .select("created_at, language, period, repos, judge_decision")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    reports = result.data or []
    if not reports:
        return "저장된 분석 기록이 없습니다."
    return build_context(reports)


_SYSTEM = """당신은 GitHub 기술 트렌드 전문 어시스턴트입니다.
답변 전 반드시 도구를 호출해서 실제 데이터를 확인하세요.
도구 결과가 불충분하면 다른 키워드로 재검색하세요.
한국어로 답변하세요."""

_agent = create_react_agent(
    _llm,
    [search_trend_history, get_recent_trends],
    prompt=_SYSTEM,
)


def run(question: str) -> dict:
    """
    반환: {
        "answer": str,
        "contexts": list[str],
        "system": "agentic_rag",
        "tool_calls": int  # 도구 호출 횟수
    }
    """
    result   = _agent.invoke({"messages": [HumanMessage(content=question)]})
    messages = result.get("messages", [])

    # 도구 호출 기록 추출
    tool_calls = 0
    contexts   = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_calls += len(msg.tool_calls)
        # ToolMessage에서 컨텍스트 수집
        if hasattr(msg, "content") and hasattr(msg, "name"):
            if msg.content and msg.content != "관련 과거 분석 데이터가 없습니다.":
                contexts.append(msg.content[:500])

    answer = messages[-1].content if messages else "답변 생성 실패"

    return {
        "answer":     answer,
        "contexts":   contexts if contexts else ["관련 데이터 없음"],
        "system":     "agentic_rag",
        "tool_calls": tool_calls,
    }
