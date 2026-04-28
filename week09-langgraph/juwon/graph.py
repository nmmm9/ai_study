"""
graph.py - LangGraph 핵심

[노드 구성]
collect  → GitHub API로 트렌딩 레포 수집
validate → 데이터 충분한지 검증 (부족하면 collect로 되돌아감)
analyze  → AI가 기술 트렌드 분석
compare  → 이전 기록과 비교
report   → 최종 리포트 생성 및 저장

[핵심 개념]
8주차: while 루프로 직접 반복 관리
9주차: LangGraph가 노드/엣지로 흐름 관리
       conditional_edge로 조건 분기 처리
"""

import json
import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from github_tools import get_language_stats, get_top_topics, get_trending_repos
from storage import load_previous_history, save_history

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY", "").strip().strip("\ufeff"),
)


# ── State 정의 ───────────────────────────────────────────────
class TrendState(TypedDict):
    language:       str
    period:         str
    repos:          list
    language_stats: dict
    top_topics:     dict
    analysis:       str
    insights:       list
    previous:       dict
    comparison:     str
    report:         dict
    retry_count:    int
    error:          str


# ── 노드 1: 수집 ─────────────────────────────────────────────
def collect_node(state: TrendState) -> TrendState:
    """GitHub API로 트렌딩 레포 수집"""
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
    """
    데이터가 충분한지 확인
    5개 미만이면 error 표시 → conditional edge가 collect로 되돌림
    """
    repos       = state.get("repos", [])
    retry_count = state.get("retry_count", 0)

    if len(repos) < 5:
        return {**state, "retry_count": retry_count + 1, "error": "데이터 부족"}

    return {**state, "retry_count": retry_count, "error": ""}


def should_retry(state: TrendState) -> str:
    """
    검증 결과에 따라 다음 노드 결정
    → "retry":   collect로 되돌아감 (최대 3회)
    → "analyze": 분석으로 진행
    """
    if state.get("error") and state.get("retry_count", 0) < 3:
        return "retry"
    return "analyze"


# ── 노드 3: 분석 ─────────────────────────────────────────────
def analyze_node(state: TrendState) -> TrendState:
    """AI가 트렌드 분석 및 핵심 인사이트 추출"""
    repos  = state.get("repos", [])
    stats  = state.get("language_stats", {})
    topics = state.get("top_topics", {})

    repo_summary = "\n".join([
        f"- {r['name']} (⭐{r['stars']:,}) [{r['language']}]: {r['description'][:80] or '설명 없음'}"
        for r in repos[:15]
    ])

    # 트렌드 분석
    analysis_response = llm.invoke(f"""
다음은 이번 주 GitHub 트렌딩 레포지토리입니다.

{repo_summary}

언어 분포: {json.dumps(stats, ensure_ascii=False)}
인기 토픽: {json.dumps(topics, ensure_ascii=False)}

개발자 관점에서 분석해주세요:
1. 이번 주 가장 주목할 기술 트렌드 3가지
2. 급부상 중인 언어 또는 프레임워크
3. 꼭 살펴봐야 할 레포 Top 3 (이유 포함)
4. 전체적인 기술 흐름 방향성

한국어로 답변하세요.
""")

    # 인사이트 5개 추출
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


# ── 노드 4: 비교 ─────────────────────────────────────────────
def compare_node(state: TrendState) -> TrendState:
    """이전 분석 기록과 비교"""
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


# ── 노드 5: 리포트 ───────────────────────────────────────────
def report_node(state: TrendState) -> TrendState:
    """최종 리포트 생성 및 히스토리 저장"""
    report = {
        "repos":          state.get("repos", []),
        "language_stats": state.get("language_stats", {}),
        "top_topics":     state.get("top_topics", {}),
        "analysis":       state.get("analysis", ""),
        "insights":       state.get("insights", []),
        "comparison":     state.get("comparison", ""),
        "period":         state.get("period", "weekly"),
        "language":       state.get("language", "전체"),
    }
    save_history(report)
    return {**state, "report": report}


# ── 그래프 구성 ──────────────────────────────────────────────
def build_graph():
    graph = StateGraph(TrendState)

    # 노드 등록
    graph.add_node("collect",  collect_node)
    graph.add_node("validate", validate_node)
    graph.add_node("analyze",  analyze_node)
    graph.add_node("compare",  compare_node)
    graph.add_node("report",   report_node)

    # 엣지 연결
    graph.set_entry_point("collect")
    graph.add_edge("collect", "validate")
    graph.add_conditional_edges(
        "validate",
        should_retry,
        {"retry": "collect", "analyze": "analyze"},
    )
    graph.add_edge("analyze", "compare")
    graph.add_edge("compare", "report")
    graph.add_edge("report",  END)

    return graph.compile()


trend_graph = build_graph()


# ── 그래프 시각화 ────────────────────────────────────────────
def get_graph_ascii() -> str:
    """ASCII 아트로 그래프 구조 직접 작성 (graphviz 불필요)"""
    return """\
┌─────────────┐
│   collect   │  ← GitHub API 데이터 수집
└──────┬──────┘
       │
┌──────▼──────┐
│  validate   │  ← 데이터 충분한지 검증
└──────┬──────┘
       │ 부족 시 ──────────────┐
       │ (retry, 최대 3회)     │
       │                      ▼
       │              ┌───────────────┐
       │              │    collect    │ (재수집)
       │              └───────────────┘
       │ 충분 시
┌──────▼──────┐
│   analyze   │  ← AI 트렌드 분석
└──────┬──────┘
       │
┌──────▼──────┐
│   compare   │  ← 이전 기록과 비교
└──────┬──────┘
       │
┌──────▼──────┐
│   report    │  ← 리포트 생성 및 저장
└──────┬──────┘
       │
      END
"""


def get_graph_mermaid() -> str:
    """Mermaid 다이어그램 코드 반환 (웹 UI용)"""
    return trend_graph.get_graph().draw_mermaid()


def run_analysis(language: str = "", period: str = "weekly") -> dict:
    """LangGraph 실행 진입점"""
    initial_state = TrendState(
        language=language,
        period=period,
        repos=[],
        language_stats={},
        top_topics={},
        analysis="",
        insights=[],
        previous={},
        comparison="",
        report={},
        retry_count=0,
        error="",
    )
    result = trend_graph.invoke(initial_state)
    return result.get("report", {})
