"""
graph.py - Multi-Agent Debate + RAG 강화 (Week 12/13)

Week 11 대비 변경:
  - 각 전문가 에이전트가 분석 전 과거 관련 데이터를 RAG로 참조
  - 저장: 임베딩 포함 JSON (벡터 검색 지원)
"""
import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from github_tools import get_language_stats, get_top_topics, get_trending_repos
from storage import save_history, search_reports

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY", "").strip().strip("﻿"),
)


def _get_past_context(query: str, field: str = "judge_decision") -> str:
    results = search_reports(query, limit=2)
    if not results:
        return ""
    parts = []
    for r in results:
        date    = r.get("created_at", "")[:10]
        content = r.get(field, "")[:300]
        if content:
            parts.append(f"[{date}] {content}")
    return "\n".join(parts)


class TrendState(TypedDict):
    language:          str
    period:            str
    repos:             list
    language_stats:    dict
    top_topics:        dict
    analysis_ai:       str
    analysis_web:      str
    analysis_sec:      str
    supervisor_report: str
    critic_feedback:   str
    judge_decision:    str
    debate_history:    list
    report:            dict


def collect_node(state: TrendState) -> dict:
    repos = get_trending_repos(
        language=state.get("language", ""),
        period=state.get("period", "weekly"),
        limit=25,
    )
    return {
        "repos":          repos,
        "language_stats": get_language_stats(repos),
        "top_topics":     get_top_topics(repos),
    }


def agent_ai_node(state: TrendState) -> dict:
    repos    = state.get("repos", [])
    ai_repos = [r for r in repos if any(
        kw in (r.get("description", "") + " ".join(r.get("topics", []))).lower()
        for kw in ["ai", "ml", "llm", "machine learning", "deep learning", "neural", "gpt", "model"]
    )][:8] or repos[:8]
    repo_summary = "\n".join([
        f"- {r['name']} (⭐{r['stars']:,} / 트렌드점수:{r.get('trend_score', 0)}): {r['description'][:60]}"
        for r in ai_repos
    ])
    past = _get_past_context("AI ML LLM 딥러닝 트렌드", "analysis_ai")
    past_section = f"\n\n[과거 AI/ML 분석 참고]\n{past}" if past else ""
    response = llm.invoke(f"""당신은 AI/ML 기술 전문가입니다.
아래 GitHub 트렌딩 레포지토리를 AI/ML 관점에서 분석해주세요.{past_section}

[현재 트렌딩 레포]
{repo_summary}

다음을 포함해서 한국어로 분석해주세요:
1. 주목할 AI/ML 기술 트렌드 (구체적인 레포 이름 포함)
2. 어떤 AI 기술이 급부상 중인가 (과거와 비교 시 변화 포함)
3. 개발자가 주목해야 할 레포 2개 추천 (이유 포함)
""")
    return {"analysis_ai": response.content}


def agent_web_node(state: TrendState) -> dict:
    repos     = state.get("repos", [])
    web_repos = [r for r in repos if any(
        kw in (r.get("description", "") + " ".join(r.get("topics", []))).lower()
        for kw in ["web", "react", "vue", "next", "frontend", "javascript", "typescript", "app", "mobile", "ui"]
    )][:8] or repos[:8]
    repo_summary = "\n".join([
        f"- {r['name']} (⭐{r['stars']:,} / 트렌드점수:{r.get('trend_score', 0)}): {r['description'][:60]}"
        for r in web_repos
    ])
    past = _get_past_context("웹 프론트엔드 React TypeScript 트렌드", "analysis_web")
    past_section = f"\n\n[과거 웹/앱 분석 참고]\n{past}" if past else ""
    response = llm.invoke(f"""당신은 웹/앱 개발 전문가입니다.
아래 GitHub 트렌딩 레포지토리를 웹/앱 관점에서 분석해주세요.{past_section}

[현재 트렌딩 레포]
{repo_summary}

다음을 포함해서 한국어로 분석해주세요:
1. 주목할 웹/앱 기술 트렌드 (구체적인 레포 이름 포함)
2. 어떤 프레임워크/라이브러리가 급부상 중인가 (과거와 비교 시 변화 포함)
3. 개발자가 주목해야 할 레포 2개 추천 (이유 포함)
""")
    return {"analysis_web": response.content}


def agent_sec_node(state: TrendState) -> dict:
    repos     = state.get("repos", [])
    sec_repos = [r for r in repos if any(
        kw in (r.get("description", "") + " ".join(r.get("topics", []))).lower()
        for kw in ["security", "auth", "crypto", "encryption", "privacy", "vulnerability", "hack", "pentest"]
    )][:8] or repos[:8]
    repo_summary = "\n".join([
        f"- {r['name']} (⭐{r['stars']:,} / 트렌드점수:{r.get('trend_score', 0)}): {r['description'][:60]}"
        for r in sec_repos
    ])
    past = _get_past_context("보안 취약점 인증 암호화 트렌드", "analysis_sec")
    past_section = f"\n\n[과거 보안 분석 참고]\n{past}" if past else ""
    response = llm.invoke(f"""당신은 보안 전문가입니다.
아래 GitHub 트렌딩 레포지토리를 보안 관점에서 분석해주세요.{past_section}

[현재 트렌딩 레포]
{repo_summary}

다음을 포함해서 한국어로 분석해주세요:
1. 주목할 보안 기술 트렌드 (구체적인 레포 이름 포함)
2. 어떤 보안 이슈나 기술이 급부상 중인가 (과거와 비교 시 변화 포함)
3. 개발자가 주목해야 할 레포 2개 추천 (이유 포함)
""")
    return {"analysis_sec": response.content}


def supervisor_node(state: TrendState) -> dict:
    response = llm.invoke(f"""당신은 수석 기술 분석가입니다.
세 전문가의 분석을 종합해서 최종 트렌드 리포트를 작성해주세요.

[AI/ML 전문가 분석]
{state.get('analysis_ai', '')}

[웹/앱 전문가 분석]
{state.get('analysis_web', '')}

[보안 전문가 분석]
{state.get('analysis_sec', '')}

세 분야를 아우르는 종합 트렌드 리포트를 한국어로 작성해주세요.
""")
    history = list(state.get("debate_history", []))
    history.append({"role": "supervisor", "content": response.content})
    return {"supervisor_report": response.content, "debate_history": history}


def critic_node(state: TrendState) -> dict:
    response = llm.invoke(f"""당신은 비판적 검토자입니다.
아래 종합 리포트에서 부족하거나 잘못된 부분을 지적해주세요.

[종합 리포트]
{state.get('supervisor_report', '')}

1. 빠진 중요한 트렌드가 있는가
2. 근거가 부족한 주장이 있는가
3. 더 강조했어야 할 부분이 있는가

한국어로 구체적으로 반론해주세요.
""")
    history = list(state.get("debate_history", []))
    history.append({"role": "critic", "content": response.content})
    return {"critic_feedback": response.content, "debate_history": history}


def judge_node(state: TrendState) -> dict:
    response = llm.invoke(f"""당신은 최종 심판자입니다.
Supervisor의 종합 리포트와 Critic의 반론을 검토해서 최종 결론을 내려주세요.

[Supervisor 종합 리포트]
{state.get('supervisor_report', '')}

[Critic 반론]
{state.get('critic_feedback', '')}

Critic의 반론을 반영해서 최종 트렌드 리포트를 한국어로 완성해주세요.
""")
    history = list(state.get("debate_history", []))
    history.append({"role": "judge", "content": response.content})
    return {"judge_decision": response.content, "debate_history": history}


def report_node(state: TrendState) -> dict:
    report = {
        "repos":             state.get("repos", []),
        "language_stats":    state.get("language_stats", {}),
        "top_topics":        state.get("top_topics", {}),
        "analysis_ai":       state.get("analysis_ai", ""),
        "analysis_web":      state.get("analysis_web", ""),
        "analysis_sec":      state.get("analysis_sec", ""),
        "supervisor_report": state.get("supervisor_report", ""),
        "critic_feedback":   state.get("critic_feedback", ""),
        "judge_decision":    state.get("judge_decision", ""),
        "debate_history":    state.get("debate_history", []),
        "period":            state.get("period", "weekly"),
        "language":          state.get("language", "전체"),
    }
    save_history(report)
    return {"report": report}


def build_graph():
    graph = StateGraph(TrendState)
    graph.add_node("collect",    collect_node)
    graph.add_node("agent_ai",   agent_ai_node)
    graph.add_node("agent_web",  agent_web_node)
    graph.add_node("agent_sec",  agent_sec_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("critic",     critic_node)
    graph.add_node("judge",      judge_node)
    graph.add_node("report",     report_node)
    graph.set_entry_point("collect")
    graph.add_edge("collect",    "agent_ai")
    graph.add_edge("collect",    "agent_web")
    graph.add_edge("collect",    "agent_sec")
    graph.add_edge("agent_ai",   "supervisor")
    graph.add_edge("agent_web",  "supervisor")
    graph.add_edge("agent_sec",  "supervisor")
    graph.add_edge("supervisor", "critic")
    graph.add_edge("critic",     "judge")
    graph.add_edge("judge",      "report")
    graph.add_edge("report",     END)
    return graph.compile()


trend_graph = build_graph()


def run_analysis(language: str = "", period: str = "weekly") -> dict:
    result = trend_graph.invoke(TrendState(
        language=language, period=period,
        repos=[], language_stats={}, top_topics={},
        analysis_ai="", analysis_web="", analysis_sec="",
        supervisor_report="", critic_feedback="", judge_decision="",
        debate_history=[], report={},
    ))
    return result.get("report", {})
