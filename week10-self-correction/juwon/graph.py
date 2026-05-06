"""
graph.py - LangGraph + Self-Correction

[노드 구성]
collect   → GitHub API로 트렌딩 레포 수집
validate  → 데이터 충분한지 검증 (부족하면 collect로 되돌아감)
generate  → AI가 기술 트렌드 분석 생성
reflect   → AI 결과 품질 검토 (점수 0~100, 70 미만이면 재생성)
compare   → 이전 기록과 비교
notify    → Gmail 발송 + GitHub README 업로드
report    → 최종 리포트 생성 및 저장

[핵심 개념]
9주차:  collect → validate → analyze → compare → report
10주차: generate 뒤에 reflect 노드 추가
        reflect가 품질 점수를 매기고 70 미만이면 generate로 되돌아감
        notify 노드에서 Gmail + GitHub README 자동 발송
"""

import json
import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from github_tools import get_language_stats, get_top_topics, get_trending_repos
from notifier import send_gmail, upload_github_readme
from storage import load_previous_history, save_history

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY", "").strip().strip("﻿"),
)


# ── State 정의 ───────────────────────────────────────────────
class TrendState(TypedDict):
    # 입력
    language:       str
    period:         str
    # 수집
    repos:          list
    language_stats: dict
    top_topics:     dict
    retry_count:    int
    error:          str
    # 생성
    analysis:       str
    insights:       list
    # Self-Correction
    reflect_count:  int
    quality_score:  int
    reflect_feedback: str
    reflect_history:  list
    # 비교/알림/저장
    previous:       dict
    comparison:     str
    notify_status:  str
    report:         dict


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


# ── 노드 2: 검증 ─────────────────────────────────────────────
def validate_node(state: TrendState) -> TrendState:
    repos       = state.get("repos", [])
    retry_count = state.get("retry_count", 0)

    if len(repos) < 5:
        return {**state, "retry_count": retry_count + 1, "error": "데이터 부족"}
    return {**state, "retry_count": retry_count, "error": ""}


def should_retry(state: TrendState) -> str:
    if state.get("error") and state.get("retry_count", 0) < 3:
        return "retry"
    return "generate"


# ── 노드 3: 생성 ─────────────────────────────────────────────
def generate_node(state: TrendState) -> TrendState:
    """AI가 트렌드 분석 생성 (Self-Correction 시 피드백 반영)"""
    repos  = state.get("repos", [])
    stats  = state.get("language_stats", {})
    topics = state.get("top_topics", {})

    repo_summary = "\n".join([
        f"- {r['name']} (⭐{r['stars']:,}) [{r['language']}]: {r['description'][:80] or '설명 없음'}"
        for r in repos[:15]
    ])

    # 이전 피드백이 있으면 프롬프트에 포함
    feedback = state.get("reflect_feedback", "")
    feedback_section = ""
    if feedback and state.get("reflect_count", 0) > 0:
        feedback_section = f"""
⚠️ 이전 분석의 개선이 필요한 부분:
{feedback}

위 피드백을 반드시 반영해서 더 구체적으로 다시 작성해주세요.
"""

    analysis_response = llm.invoke(f"""
다음은 이번 주 GitHub 트렌딩 레포지토리입니다.

{repo_summary}

언어 분포: {json.dumps(stats, ensure_ascii=False)}
인기 토픽: {json.dumps(topics, ensure_ascii=False)}
{feedback_section}
개발자 관점에서 분석해주세요:
1. 이번 주 가장 주목할 기술 트렌드 3가지 (구체적인 레포 이름 포함)
2. 급부상 중인 언어 또는 프레임워크
3. 꼭 살펴봐야 할 레포 Top 3 (이유 포함)
4. 전체적인 기술 흐름 방향성 및 미래 전망

한국어로 답변하세요. 최소 300자 이상으로 구체적으로 작성하세요.
""")

    insight_response = llm.invoke(f"""
다음 분석에서 개발자에게 유용한 핵심 인사이트를 5개 뽑아주세요.
각 항목은 한 문장으로 간결하게 작성하세요.

{analysis_response.content}

반드시 아래 JSON 배열 형식으로만 반환하세요 (다른 텍스트 없이):
["인사이트1", "인사이트2", "인사이트3", "인사이트4", "인사이트5"]
""")

    try:
        insights = json.loads(insight_response.content)
    except Exception:
        insights = [analysis_response.content[:100]]

    return {**state, "analysis": analysis_response.content, "insights": insights}


# ── 노드 4: 반성 (Self-Correction 핵심) ──────────────────────
def reflect_node(state: TrendState) -> TrendState:
    """
    AI 결과 품질 자동 검토

    채점 기준 (총 100점):
    - 분석 길이 300자 이상  : 20점
    - 트렌드 키워드 3개 이상: 25점
    - 구체적 레포 이름 3개↑ : 25점
    - 인사이트 3개 이상     : 15점
    - 기술 방향성 키워드 2개↑: 15점

    70점 이상 → compare로 진행
    70점 미만 → generate로 되돌아감 (최대 3회)
    """
    analysis = state.get("analysis", "")
    insights = state.get("insights", [])
    repos    = state.get("repos", [])

    score  = 0
    issues = []

    # 1. 분석 길이 (20점)
    if len(analysis) >= 300:
        score += 20
    else:
        issues.append(f"분석이 짧음 ({len(analysis)}자 / 최소 300자)")

    # 2. 트렌드 키워드 (25점)
    trend_kws = ["트렌드", "증가", "급부상", "인기", "주목", "성장", "상승"]
    trend_cnt = sum(1 for kw in trend_kws if kw in analysis)
    if trend_cnt >= 3:
        score += 25
    else:
        issues.append(f"트렌드 키워드 부족 ({trend_cnt}개 / 최소 3개)")

    # 3. 레포 이름 언급 (25점)
    repo_names  = [r["name"].split("/")[-1] for r in repos[:10]]
    mentioned   = sum(1 for name in repo_names if name.lower() in analysis.lower())
    if mentioned >= 3:
        score += 25
    else:
        issues.append(f"구체적 레포 이름 부족 ({mentioned}개 / 최소 3개)")

    # 4. 인사이트 수 (15점)
    if len(insights) >= 3:
        score += 15
    else:
        issues.append(f"인사이트 부족 ({len(insights)}개 / 최소 3개)")

    # 5. 방향성 키워드 (15점)
    dir_kws = ["방향", "전망", "미래", "흐름", "변화", "발전", "전환"]
    dir_cnt = sum(1 for kw in dir_kws if kw in analysis)
    if dir_cnt >= 2:
        score += 15
    else:
        issues.append(f"기술 방향성 언급 부족 ({dir_cnt}개 / 최소 2개)")

    feedback = " | ".join(issues) if issues else "모든 품질 기준 통과"

    history = list(state.get("reflect_history", []))
    history.append({
        "attempt":  state.get("reflect_count", 0) + 1,
        "score":    score,
        "feedback": feedback,
    })

    return {
        **state,
        "quality_score":    score,
        "reflect_feedback": feedback,
        "reflect_count":    state.get("reflect_count", 0) + 1,
        "reflect_history":  history,
    }


def should_regenerate(state: TrendState) -> str:
    score         = state.get("quality_score", 0)
    reflect_count = state.get("reflect_count", 0)

    if score < 70 and reflect_count < 3:
        return "regenerate"
    return "compare"


# ── 노드 5: 비교 ─────────────────────────────────────────────
def compare_node(state: TrendState) -> TrendState:
    previous = load_previous_history()

    if not previous:
        return {
            **state,
            "previous":   {},
            "comparison": "이전 분석 기록이 없습니다. 다음 분석부터 비교가 가능합니다.",
        }

    current_langs  = set(state.get("language_stats", {}).keys())
    previous_langs = set(previous.get("language_stats", {}).keys())
    new_langs      = current_langs - previous_langs
    dropped_langs  = previous_langs - current_langs

    compare_response = llm.invoke(f"""
이번 주와 이전 분석 결과를 비교해주세요.

이번 주 언어 분포: {json.dumps(state.get('language_stats', {}), ensure_ascii=False)}
이전 언어 분포:   {json.dumps(previous.get('language_stats', {}), ensure_ascii=False)}

새로 등장한 언어: {list(new_langs) or '없음'}
사라진 언어:     {list(dropped_langs) or '없음'}

변화의 의미를 개발자 관점에서 3문장 이내로 요약해주세요. 한국어로.
""")

    return {**state, "previous": previous, "comparison": compare_response.content}


# ── 노드 6: 알림 ─────────────────────────────────────────────
def notify_node(state: TrendState) -> TrendState:
    """Gmail 발송 + GitHub README 업로드"""
    report_data = {
        **state,
        "quality_score":   state.get("quality_score", 0),
        "reflect_history": state.get("reflect_history", []),
    }

    statuses = []

    gmail_result = send_gmail(report_data)
    statuses.append(f"Gmail: {gmail_result}")

    readme_result = upload_github_readme(report_data)
    statuses.append(f"README: {readme_result}")

    return {**state, "notify_status": " | ".join(statuses)}


# ── 노드 7: 리포트 ───────────────────────────────────────────
def report_node(state: TrendState) -> TrendState:
    report = {
        "repos":           state.get("repos", []),
        "language_stats":  state.get("language_stats", {}),
        "top_topics":      state.get("top_topics", {}),
        "analysis":        state.get("analysis", ""),
        "insights":        state.get("insights", []),
        "comparison":      state.get("comparison", ""),
        "period":          state.get("period", "weekly"),
        "language":        state.get("language", "전체"),
        "quality_score":   state.get("quality_score", 0),
        "reflect_history": state.get("reflect_history", []),
        "notify_status":   state.get("notify_status", ""),
    }
    save_history(report)
    return {**state, "report": report}


# ── 그래프 구성 ──────────────────────────────────────────────
def build_graph():
    graph = StateGraph(TrendState)

    graph.add_node("collect",  collect_node)
    graph.add_node("validate", validate_node)
    graph.add_node("generate", generate_node)
    graph.add_node("reflect",  reflect_node)
    graph.add_node("compare",  compare_node)
    graph.add_node("notify",   notify_node)
    graph.add_node("report",   report_node)

    graph.set_entry_point("collect")
    graph.add_edge("collect", "validate")
    graph.add_conditional_edges(
        "validate",
        should_retry,
        {"retry": "collect", "generate": "generate"},
    )
    graph.add_edge("generate", "reflect")
    graph.add_conditional_edges(
        "reflect",
        should_regenerate,
        {"regenerate": "generate", "compare": "compare"},
    )
    graph.add_edge("compare", "notify")
    graph.add_edge("notify",  "report")
    graph.add_edge("report",  END)

    return graph.compile()


trend_graph = build_graph()


# ── 시각화 ───────────────────────────────────────────────────
def get_graph_ascii() -> str:
    return """\
┌─────────────┐
│   collect   │  ← GitHub API 데이터 수집
└──────┬──────┘
       │
┌──────▼──────┐
│  validate   │  ← 데이터 충분한지 검증
└──────┬──────┘
       │ 부족 시 ─────────────┐
       │ (retry, 최대 3회)    │
       │                     ▼
       │             ┌──────────────┐
       │             │   collect    │ (재수집)
       │             └──────────────┘
       │ 충분 시
┌──────▼──────┐
│  generate   │  ← AI 트렌드 분석 생성
└──────┬──────┘
       │
┌──────▼──────┐
│   reflect   │  ← 품질 자동 검토 (0~100점)
└──────┬──────┘
       │ 점수 < 70 ───────────┐
       │ (최대 3회 재생성)    │
       │                     ▼
       │             ┌──────────────┐
       │             │   generate   │ (피드백 반영 재생성)
       │             └──────────────┘
       │ 점수 ≥ 70
┌──────▼──────┐
│   compare   │  ← 이전 기록과 비교
└──────┬──────┘
       │
┌──────▼──────┐
│   notify    │  ← Gmail 발송 + GitHub README 업로드
└──────┬──────┘
       │
┌──────▼──────┐
│   report    │  ← 리포트 생성 및 저장
└──────┬──────┘
       │
      END
"""


def get_graph_mermaid() -> str:
    return trend_graph.get_graph().draw_mermaid()


def run_analysis(language: str = "", period: str = "weekly") -> dict:
    initial_state = TrendState(
        language=language,
        period=period,
        repos=[],
        language_stats={},
        top_topics={},
        retry_count=0,
        error="",
        analysis="",
        insights=[],
        reflect_count=0,
        quality_score=0,
        reflect_feedback="",
        reflect_history=[],
        previous={},
        comparison="",
        notify_status="",
        report={},
    )
    result = trend_graph.invoke(initial_state)
    return result.get("report", {})
