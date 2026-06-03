"""
agentic_chat.py - LangGraph ReAct 기반 Agentic RAG 채팅 (Week 12/13)
에이전트가 스스로 판단해서 RAG 도구를 호출함
"""
import os
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from rag_tools import get_recent_trends, search_repo_analysis, search_trend_history

_llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY", ""))

_SYSTEM = """당신은 GitHub 기술 트렌드 전문 어시스턴트입니다.

사용 가능한 도구:
- search_trend_history: 특정 기술/트렌드에 대한 과거 분석 검색
- get_recent_trends: 최근 트렌드 분석 요약 조회
- search_repo_analysis: 특정 레포지토리 관련 과거 분석 검색

규칙:
1. 과거 데이터가 필요한 질문이면 반드시 도구를 호출하세요
2. 도구 결과가 부족하면 다른 키워드로 재검색하세요
3. 현재 분석 결과와 과거 데이터를 함께 참조해서 답변하세요
4. 항상 한국어로 답변하세요"""


def run_agentic_chat(message: str, current_report: dict) -> dict:
    agent = create_react_agent(_llm, [search_trend_history, get_recent_trends, search_repo_analysis])

    repos = current_report.get("repos", [])[:8]
    repo_summary = "\n".join([
        f"- {r['name']} (⭐{r.get('stars', 0):,}): {r.get('description', '')[:60]}"
        for r in repos
    ])
    context_msg = f"""[현재 분석 결과]
트렌딩 레포: {repo_summary}

AI/ML 분석: {current_report.get('analysis_ai', '')[:300]}
웹/앱 분석: {current_report.get('analysis_web', '')[:300]}
보안 분석: {current_report.get('analysis_sec', '')[:300]}
Judge 결론: {current_report.get('judge_decision', '')[:300]}

위 현재 분석 결과와 과거 데이터를 함께 참조해서 답변해주세요.
질문: {message}"""

    result   = agent.invoke({"messages": [HumanMessage(content=context_msg)]})
    messages = result.get("messages", [])

    steps = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                steps.append({
                    "tool":  tc["name"],
                    "input": str(tc["args"].get("query", tc["args"].get("limit", tc["args"]))),
                })

    reply = messages[-1].content if messages else "답변 생성 실패"
    return {"reply": reply, "steps": steps}
