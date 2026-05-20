"""
graph.py - Multi-Agent Debate + Agentic RAG (week12)

week11 대비 변경사항:
  - 전문가 에이전트 3명이 분석 전 RAG로 과거 데이터 조회
  - "이번 주 vs 지난 분석" 비교 관점이 자동으로 추가됨
  - 저장: JSON 파일 → Supabase pgvector

[에이전트 흐름]
collector → agent_ai + agent_web + agent_sec (각자 RAG 조회)
         → supervisor → critic → judge → report
"""
import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from github_tools import get_language_stats, get_top_topics, get_trending_repos
from storage import save_history
from vector_store import search_reports

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY", "").strip().strip("﻿"),
)


# ── State ────────────────────────────────────────────────────
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


# ── RAG 헬퍼: 과거 분석 컨텍스트 가져오기 ─────────────────────
def _get_past_context(query: str, field: str) -> str:
    """RAG로 과거 분석을 검색하고 특정 필드만 추출"""
    try:
        results = search_reports(query, limit=2)
        if not results:
            return ""
        parts = []
        for r in results:
            date = r.get("created_at", "")[:10]
            content = r.get(field, "")[:300]
            if content:
                parts.append(f"[{date}] {content}")
        if not parts:
            return ""
        return "\n\n[과거 분석 참고]\n" + "\n---\n".join(parts)
    except Exception:
        return ""


# ── 노드 1: 수집 ─────────────────────────────────────────────
def collect_node(state: TrendState) -> TrendState:
    repos = get_trending_repos(
        language=state.get("language", ""),
        period=state.get("period", "weekly"),
        limit=25,
    )
    return {
        **state,
        "repos":          repos,
        "language_stats": get_language_stats(repos),
        "top_topics":     get_top_topics(repos),
    }


# ── 노드 2: AI/ML 전문가 (RAG 강화) ──────────────────────────
def agent_ai_node(state: TrendState) -> TrendState:
    repos    = state.get("repos", [])
    ai_repos = [r for r in repos if any(
        kw in (r.get("description", "") + " ".join(r.get("topics", []))).lower()
        for kw in ["ai", "ml", "llm", "machine learning", "deep learning", "neural", "gpt", "model"]
    )][:8] or repos[:8]

    repo_summary = "\n".join(
        f"- {r['name']} (⭐{r['stars']:,} / 트렌드점수:{r.get('trend_score',0)}) : {r['description'][:60]}"
        for r in ai_repos
    )

    past = _get_past_context("AI ML 딥러닝 트렌드 분석", "analysis_ai")

    response = llm.invoke(f"""당신은 AI/ML 기술 전문가입니다.
아래 GitHub 트렌딩 레포지토리를 AI/ML 관점에서만 분석해주세요.

{repo_summary}
{past}

다음을 포함해서 한국어로 분석해주세요:
1. 주목할 AI/ML 기술 트렌드 (구체적인 레포 이름 포함)
2. 어떤 AI 기술이 급부상 중인가{' (과거 분석과 비교해서 변화를 언급하세요)' if past else ''}
3. 개발자가 주목해야 할 레포 2개 추천 (이유 포함)
""")
    return {"analysis_ai": response.content}


# ── 노드 3: 웹/앱 전문가 (RAG 강화) ──────────────────────────
def agent_web_node(state: TrendState) -> TrendState:
    repos     = state.get("repos", [])
    web_repos = [r for r in repos if any(
        kw in (r.get("description", "") + " ".join(r.get("topics", []))).lower()
        for kw in ["web", "react", "vue", "next", "frontend", "javascript", "typescript", "app", "mobile", "ui"]
    )][:8] or repos[:8]

    repo_summary = "\n".join(
        f"- {r['name']} (⭐{r['stars']:,} / 트렌드점수:{r.get('trend_score',0)}) : {r['description'][:60]}"
        for r in web_repos
    )

    past = _get_past_context("웹 앱 프론트엔드 JavaScript 프레임워크 트렌드", "analysis_web")

    response = llm.invoke(f"""당신은 웹/앱 개발 전문가입니다.
아래 GitHub 트렌딩 레포지토리를 웹/앱 개발 관점에서만 분석해주세요.

{repo_summary}
{past}

다음을 포함해서 한국어로 분석해주세요:
1. 주목할 웹/앱 기술 트렌드 (구체적인 레포 이름 포함)
2. 어떤 프레임워크/라이브러리가 급부상 중인가{' (과거 분석과 비교해서 변화를 언급하세요)' if past else ''}
3. 개발자가 주목해야 할 레포 2개 추천 (이유 포함)
""")
    return {"analysis_web": response.content}


# ── 노드 4: 보안 전문가 (RAG 강화) ──────────────────────────
def agent_sec_node(state: TrendState) -> TrendState:
    repos     = state.get("repos", [])
    sec_repos = [r for r in repos if any(
        kw in (r.get("description", "") + " ".join(r.get("topics", []))).lower()
        for kw in ["security", "auth", "crypto", "encryption", "privacy", "vulnerability", "hack", "pentest"]
    )][:8] or repos[:8]

    repo_summary = "\n".join(
        f"- {r['name']} (⭐{r['stars']:,} / 트렌드점수:{r.get('trend_score',0)}) : {r['description'][:60]}"
        for r in sec_repos
    )

    past = _get_past_context("보안 암호화 취약점 인증 트렌드", "analysis_sec")

    response = llm.invoke(f"""당신은 보안 전문가입니다.
아래 GitHub 트렌딩 레포지토리를 보안 관점에서만 분석해주세요.

{repo_summary}
{past}

다음을 포함해서 한국어로 분석해주세요:
1. 주목할 보안 기술 트렌드 (구체적인 레포 이름 포함)
2. 어떤 보안 이슈나 기술이 급부상 중인가{' (과거 분석과 비교해서 변화를 언급하세요)' if past else ''}
3. 개발자가 주목해야 할 레포 2개 추천 (이유 포함)
""")
    return {"analysis_sec": response.content}


# ── 노드 5: Supervisor ───────────────────────────────────────
def supervisor_node(state: TrendState) -> TrendState:
    response = llm.invoke(f"""당신은 수석 기술 분석가입니다.
세 전문가의 분석을 종합해서 최종 트렌드 리포트를 작성해주세요.

[AI/ML 전문가 분석]
{state.get('analysis_ai', '')}

[웹/앱 전문가 분석]
{state.get('analysis_web', '')}

[보안 전문가 분석]
{state.get('analysis_sec', '')}

세 분야를 아우르는 종합 트렌드 리포트를 한국어로 작성해주세요.
전체적인 기술 흐름과 개발자가 지금 당장 주목해야 할 것을 정리해주세요.
""")

    history = list(state.get("debate_history", []))
    history.append({"role": "supervisor", "content": response.content})
    return {**state, "supervisor_report": response.content, "debate_history": history}


# ── 노드 6: Critic ───────────────────────────────────────────
def critic_node(state: TrendState) -> TrendState:
    response = llm.invoke(f"""당신은 비판적 검토자입니다.
아래 종합 리포트에서 부족하거나 잘못된 부분을 지적해주세요.

[종합 리포트]
{state.get('supervisor_report', '')}

비판적으로 검토해주세요:
1. 빠진 중요한 트렌드가 있는가
2. 근거가 부족한 주장이 있는가
3. 더 강조했어야 할 부분이 있는가

한국어로 구체적으로 반론해주세요.
""")

    history = list(state.get("debate_history", []))
    history.append({"role": "critic", "content": response.content})
    return {**state, "critic_feedback": response.content, "debate_history": history}


# ── 노드 7: Judge ────────────────────────────────────────────
def judge_node(state: TrendState) -> TrendState:
    response = llm.invoke(f"""당신은 최종 심판자입니다.
Supervisor의 종합 리포트와 Critic의 반론을 검토해서 최종 결론을 내려주세요.

[Supervisor 종합 리포트]
{state.get('supervisor_report', '')}

[Critic 반론]
{state.get('critic_feedback', '')}

Critic의 반론을 반영해서 최종 트렌드 리포트를 완성해주세요.
한국어로 작성하고, 결론을 명확하게 내려주세요.
""")

    history = list(state.get("debate_history", []))
    history.append({"role": "judge", "content": response.content})
    return {**state, "judge_decision": response.content, "debate_history": history}


# ── 노드 8: 리포트 저장 ──────────────────────────────────────
def report_node(state: TrendState) -> TrendState:
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
    return {**state, "report": report}


# ── 그래프 구성 ──────────────────────────────────────────────
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
    initial_state = TrendState(
        language=language,
        period=period,
        repos=[],
        language_stats={},
        top_topics={},
        analysis_ai="",
        analysis_web="",
        analysis_sec="",
        supervisor_report="",
        critic_feedback="",
        judge_decision="",
        debate_history=[],
        report={},
    )
    result = trend_graph.invoke(initial_state)
    return result.get("report", {})
