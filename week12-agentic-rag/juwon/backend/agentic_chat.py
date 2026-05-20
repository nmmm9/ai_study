"""
agentic_chat.py - Agentic RAG 채팅 에이전트

week11 chat vs week12 chat:
  before: 고정 컨텍스트 붙여서 LLM 한 번 호출
  after:  LLM이 스스로 판단 → RAG 도구 호출 → 결과 평가 → 재검색 or 답변

LangGraph create_react_agent로 ReAct 루프 구현.
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from rag_tools import search_trend_history, search_repo_analysis, get_recent_trends

_llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY", ""),
)

_SYSTEM = """당신은 GitHub 기술 트렌드 전문 어시스턴트입니다.

사용 가능한 도구:
- search_trend_history: 과거 트렌드 분석을 시맨틱 검색 (기간/언어/기술 관련 질문)
- search_repo_analysis: 특정 레포에 대한 과거 분석 검색
- get_recent_trends: 최근 N번 분석 요약

답변 규칙:
1. 답변 전 반드시 관련 도구를 호출해서 실제 데이터를 확인하세요.
2. 도구 결과가 불충분하면 다른 키워드로 재검색하세요.
3. 현재 분석 결과와 과거 데이터를 함께 활용해서 답변하세요.
4. 한국어로 답변하세요."""

_agent = create_react_agent(
    _llm,
    [search_trend_history, search_repo_analysis, get_recent_trends],
    prompt=_SYSTEM,
)


def run_agentic_chat(message: str, current_report: dict) -> dict:
    """
    Agentic RAG로 질문에 답변.
    반환: {"reply": str, "steps": [{"tool": str, "input": str}]}
    """
    repos = current_report.get("repos", [])[:10]
    repo_summary = "\n".join(
        f"- {r['name']} (⭐{r.get('stars', 0):,} / 점수:{r.get('trend_score', 0)}): {r.get('description', '')[:60]}"
        for r in repos
    )

    full_message = (
        f"[현재 분석 - {current_report.get('language') or '전체'} / {current_report.get('period', 'weekly')}]\n"
        f"{repo_summary}\n\n"
        f"[Judge 결론]\n{current_report.get('judge_decision', '')[:400]}\n\n"
        f"---\n질문: {message}"
    )

    result = _agent.invoke({"messages": [HumanMessage(content=full_message)]})
    messages = result.get("messages", [])

    # 에이전트 도구 호출 단계 추출 (프론트 표시용)
    steps = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                args = tc.get("args", {})
                steps.append({
                    "tool":  tc["name"],
                    "input": args.get("query") or args.get("repo_name") or str(args.get("limit", "")),
                })

    reply = messages[-1].content if messages else "답변을 생성하지 못했습니다."
    return {"reply": reply, "steps": steps}
