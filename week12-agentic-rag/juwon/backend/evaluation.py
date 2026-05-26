"""
evaluation.py - RAG 평가 모듈 (week12 백엔드 통합)

3개 시스템을 20개 질문으로 평가:
  A. Simple RAG   - 단순 벡터 검색 1회
  B. Advanced RAG - Multi-Query + RRF + 리랭킹
  C. Agentic RAG  - LangGraph ReAct 에이전트

백그라운드로 실행되며 state 딕셔너리로 진행률 공유.
"""
import os
import json
import time
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from vector_store import search_reports

_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
_llm    = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY", ""))


DATASET = [
    {"id": 1,  "type": "general",    "question": "최근 GitHub 트렌딩에서 AI/ML 관련 레포의 특징은 무엇인가요?",              "ground_truth": "최근 GitHub 트렌딩에서 AI/ML 관련 레포는 LLM, 딥러닝 프레임워크, 모델 파인튜닝 도구 등이 주를 이루며, Python 언어로 작성된 경우가 많고 빠른 속도로 별점을 획득하는 특징이 있습니다."},
    {"id": 2,  "type": "general",    "question": "GitHub 트렌딩에서 가장 자주 등장하는 프로그래밍 언어는 무엇인가요?",        "ground_truth": "GitHub 트렌딩에서는 Python이 AI/ML 분야의 성장으로 가장 자주 등장하며, TypeScript와 JavaScript는 웹/앱 개발 분야에서, Rust는 시스템 프로그래밍 분야에서 꾸준히 트렌딩에 오릅니다."},
    {"id": 3,  "type": "general",    "question": "웹 개발 관련 트렌딩 레포의 최근 동향은 어떤가요?",                         "ground_truth": "웹 개발 관련 트렌딩 레포는 React, Next.js 기반 프레임워크와 TypeScript 생태계 도구들이 주를 이루며, 풀스택 프레임워크와 UI 컴포넌트 라이브러리가 꾸준히 인기를 얻고 있습니다."},
    {"id": 4,  "type": "general",    "question": "보안 관련 트렌딩 레포에서 공통적으로 다루는 주제는 무엇인가요?",            "ground_truth": "보안 관련 트렌딩 레포는 인증/인가 도구, 취약점 스캐너, 암호화 라이브러리, 펜테스팅 도구 등이 자주 등장하며 최근에는 LLM 보안과 관련된 레포도 증가하고 있습니다."},
    {"id": 5,  "type": "general",    "question": "트렌드 점수가 높은 레포들의 공통적인 특징은 무엇인가요?",                   "ground_truth": "트렌드 점수가 높은 레포는 해당 기간 동안 획득한 별점 수가 많고, 명확한 사용 목적과 좋은 문서화를 갖추고 있으며, 실용적인 문제를 해결하거나 새로운 기술 트렌드를 반영하는 경우가 많습니다."},
    {"id": 6,  "type": "comparison", "question": "AI 관련 레포와 웹 개발 관련 레포를 비교했을 때 어떤 차이가 있나요?",        "ground_truth": "AI 관련 레포는 Python 중심으로 LLM/딥러닝 기술을 다루며 학술/연구 성격이 강하고, 웹 개발 관련 레포는 JavaScript/TypeScript 중심으로 실용적인 프레임워크와 라이브러리 위주입니다."},
    {"id": 7,  "type": "comparison", "question": "Rust와 Python 언어 트렌딩 레포의 특성 차이는 무엇인가요?",                 "ground_truth": "Python 트렌딩 레포는 AI/ML, 데이터 분석 분야가 주를 이루고 별점 획득 속도가 빠른 반면, Rust 트렌딩 레포는 시스템 프로그래밍, 성능 도구, WebAssembly 관련이 많으며 기술적 깊이가 높은 레포가 많습니다."},
    {"id": 8,  "type": "comparison", "question": "이번 주 트렌딩과 이전 분석 결과를 비교했을 때 달라진 점이 있나요?",         "ground_truth": "트렌딩 분석을 반복하면 새로 등장한 레포, 별점이 급등한 레포, 트렌딩에서 사라진 레포를 파악할 수 있으며, 이를 통해 기술 트렌드의 변화 흐름을 확인할 수 있습니다."},
    {"id": 9,  "type": "comparison", "question": "별점이 많은 레포와 트렌드 점수가 높은 레포는 어떻게 다른가요?",             "ground_truth": "별점이 많은 레포는 오랜 기간 누적된 인지도를 반영하는 반면, 트렌드 점수가 높은 레포는 최근 짧은 기간 동안 빠르게 주목받고 있는 레포를 의미합니다."},
    {"id": 10, "type": "comparison", "question": "주간 트렌딩과 일간 트렌딩에는 어떤 차이가 있나요?",                        "ground_truth": "일간 트렌딩은 당일 화제가 된 레포로 변동성이 크고 단기 이슈에 민감한 반면, 주간 트렌딩은 일주일간 지속적으로 주목받은 레포로 더 안정적인 트렌드를 반영합니다."},
    {"id": 11, "type": "specific",   "question": "LLM 관련 트렌딩 레포 중 주목할 만한 것은 무엇인가요?",                     "ground_truth": "LLM 관련 트렌딩 레포로는 언어 모델 추론 엔진, 파인튜닝 도구, 프롬프트 관리 프레임워크, LLM 애플리케이션 개발 도구 등이 자주 등장하며 이 분야는 매우 빠른 속도로 발전하고 있습니다."},
    {"id": 12, "type": "specific",   "question": "React 또는 Next.js 관련 트렌딩 레포가 있나요?",                            "ground_truth": "React와 Next.js 생태계 관련 레포는 UI 컴포넌트 라이브러리, 상태 관리 도구, 풀스택 프레임워크 형태로 꾸준히 트렌딩에 등장하며 TypeScript 지원이 일반화되어 있습니다."},
    {"id": 13, "type": "specific",   "question": "Rust로 작성된 인기 트렌딩 레포의 특징은 무엇인가요?",                      "ground_truth": "Rust 트렌딩 레포는 고성능 시스템 도구, 런타임, CLI 도구, WebAssembly 관련 프로젝트가 많으며 안전성과 성능을 동시에 추구하는 프로젝트들이 개발자들의 주목을 받습니다."},
    {"id": 14, "type": "specific",   "question": "보안 도구 관련 트렌딩 레포를 알려주세요.",                                  "ground_truth": "보안 도구 관련 트렌딩 레포는 네트워크 스캐너, 취약점 분석 도구, 인증 라이브러리, 시크릿 관리 도구 등이 자주 등장하며 최근에는 AI 모델 보안 관련 레포도 증가하고 있습니다."},
    {"id": 15, "type": "specific",   "question": "머신러닝 프레임워크 관련 트렌딩 레포에는 어떤 것들이 있나요?",              "ground_truth": "머신러닝 프레임워크 관련 트렌딩 레포는 모델 학습 최적화 도구, 추론 엔진, 데이터 파이프라인 라이브러리, 모델 평가 프레임워크 등이 있으며 특히 경량화와 실행 속도를 개선하는 도구들이 주목받고 있습니다."},
    {"id": 16, "type": "analysis",   "question": "현재 개발자들이 가장 관심을 가지는 기술 스택은 무엇인가요?",                "ground_truth": "현재 개발자들은 LLM 기반 AI 애플리케이션 개발 도구, Rust 기반 고성능 시스템 도구, TypeScript 풀스택 프레임워크에 높은 관심을 보이고 있으며 AI와 기존 개발 스택의 통합 도구도 주목받고 있습니다."},
    {"id": 17, "type": "analysis",   "question": "오픈소스 AI 도구의 최근 트렌드는 어떤가요?",                               "ground_truth": "오픈소스 AI 도구는 LLM 파인튜닝, RAG 파이프라인, AI 에이전트 프레임워크, 멀티모달 모델 도구 등이 빠르게 증가하고 있으며, 로컬에서 실행 가능한 경량 모델 도구도 큰 주목을 받고 있습니다."},
    {"id": 18, "type": "analysis",   "question": "GitHub 트렌딩 데이터로 볼 때 앞으로 성장할 기술 분야는?",                  "ground_truth": "트렌딩 데이터를 보면 AI 에이전트, 멀티모달 AI, Rust 기반 성능 도구, WebAssembly, 엣지 컴퓨팅 관련 기술이 지속적으로 성장하고 있어 앞으로도 이 분야의 레포가 활발히 등장할 것으로 예상됩니다."},
    {"id": 19, "type": "analysis",   "question": "지금 개발자가 배워야 할 기술을 트렌딩 데이터 기반으로 추천해주세요.",       "ground_truth": "트렌딩 데이터 기반으로 추천하면 LLM API 활용 및 프롬프트 엔지니어링, RAG 파이프라인 구축, Rust 기초, TypeScript 기반 풀스택 개발이 현재 시장에서 가장 주목받는 기술입니다."},
    {"id": 20, "type": "analysis",   "question": "GitHub 트렌딩에서 반복적으로 등장하는 레포의 의미는 무엇인가요?",          "ground_truth": "반복적으로 트렌딩에 등장하는 레포는 단순한 일시적 유행이 아닌 실질적인 개발자 수요가 있는 프로젝트임을 의미하며, 꾸준한 업데이트와 커뮤니티 활동을 통해 지속적인 관심을 받고 있다는 신호입니다."},
]


# ── 공통 유틸 ─────────────────────────────────────────────────

def _build_context(reports: list[dict]) -> str:
    parts = []
    for r in reports:
        date  = r.get("created_at", "")[:10]
        lang  = r.get("language") or "전체"
        repos = r.get("repos", [])
        top   = ", ".join(rp["name"] for rp in repos[:5])
        judge = r.get("judge_decision", "")[:400]
        parts.append(f"[{date} | {lang}]\n상위 레포: {top}\n분석: {judge}")
    return "\n\n---\n\n".join(parts)


def _llm_answer(context: str, question: str) -> str:
    resp = _openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 GitHub 기술 트렌드 전문 어시스턴트입니다. 제공된 데이터를 바탕으로 한국어로 답변하세요."},
            {"role": "user",   "content": f"[참고 데이터]\n{context}\n\n질문: {question}"},
        ],
        max_tokens=512,
    )
    return resp.choices[0].message.content or ""


def _expand_queries(question: str, n: int = 2) -> list[str]:
    try:
        resp = _openai.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=200,
            messages=[
                {"role": "system", "content": "주어진 질문을 다른 표현으로 변형해서 JSON 배열로만 응답하세요."},
                {"role": "user",   "content": f"질문: {question}\n{n}가지 다른 표현으로 변형해주세요."},
            ],
        )
        raw = resp.choices[0].message.content or "[]"
        queries = json.loads(raw)
        return [question] + [q for q in queries if isinstance(q, str)][:n]
    except Exception:
        return [question]


def _rrf_merge(results_list: list[list[dict]], k: int = 60) -> list[dict]:
    scores: dict[str, float] = {}
    docs:   dict[str, dict]  = {}
    for results in results_list:
        for rank, r in enumerate(results):
            doc_id = r.get("id", str(rank))
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
            docs[doc_id]   = r
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [docs[doc_id] for doc_id, _ in ranked[:5]]


# ── System A: Simple RAG ──────────────────────────────────────

def run_simple(question: str) -> dict:
    results  = search_reports(question, limit=3)
    context  = _build_context(results)
    answer   = _llm_answer(context, question)
    contexts = [
        f"{r.get('judge_decision','')[:300]} (레포: {', '.join(rp['name'] for rp in r.get('repos',[])[:3])})"
        for r in results
    ]
    return {"answer": answer, "contexts": contexts or ["관련 데이터 없음"]}


# ── System B: Advanced RAG ────────────────────────────────────

def run_advanced(question: str) -> dict:
    queries      = _expand_queries(question, n=2)
    results_list = [search_reports(q, limit=5) for q in queries]
    merged       = _rrf_merge(results_list)
    top3         = merged[:3]
    context      = _build_context(top3)
    answer       = _llm_answer(context, question)
    contexts     = [
        f"{r.get('judge_decision','')[:300]} (레포: {', '.join(rp['name'] for rp in r.get('repos',[])[:3])})"
        for r in top3
    ]
    return {"answer": answer, "contexts": contexts or ["관련 데이터 없음"]}


# ── System C: Agentic RAG ─────────────────────────────────────

_AGENT_SYSTEM = """당신은 GitHub 기술 트렌드 전문 어시스턴트입니다.
답변 전 반드시 도구를 호출해서 실제 데이터를 확인하세요.
도구 결과가 불충분하면 다른 키워드로 재검색하세요.
한국어로 답변하세요."""


@tool
def search_trend_history_eval(query: str) -> str:
    """과거 GitHub 트렌드 분석 결과에서 관련 정보를 검색합니다."""
    results = search_reports(query, limit=3)
    if not results:
        return "관련 과거 분석 데이터가 없습니다."
    return _build_context(results)


_eval_agent = create_react_agent(
    _llm,
    [search_trend_history_eval],
    prompt=_AGENT_SYSTEM,
)


def run_agentic(question: str) -> dict:
    result   = _eval_agent.invoke({"messages": [HumanMessage(content=question)]})
    messages = result.get("messages", [])

    tool_calls = sum(
        len(m.tool_calls) for m in messages
        if hasattr(m, "tool_calls") and m.tool_calls
    )
    contexts = [
        m.content[:500] for m in messages
        if hasattr(m, "name") and m.content and m.content != "관련 과거 분석 데이터가 없습니다."
    ]
    answer = messages[-1].content if messages else "답변 생성 실패"

    return {
        "answer":     answer,
        "contexts":   contexts or ["관련 데이터 없음"],
        "tool_calls": tool_calls,
    }


# ── 평가 실행기 ───────────────────────────────────────────────

SYSTEMS = {
    "simple_rag":   ("Simple RAG (A)",   run_simple),
    "advanced_rag": ("Advanced RAG (B)", run_advanced),
    "agentic_rag":  ("Agentic RAG (C)",  run_agentic),
}


def run_evaluation(state: dict) -> None:
    """
    백그라운드 태스크로 실행.
    state 딕셔너리를 통해 프론트에 진행률 공유.
    """
    state.update({"status": "running", "progress": 0, "total": len(DATASET) * len(SYSTEMS), "error": None})

    all_records: dict[str, list[dict]] = {}

    for sys_key, (sys_label, runner) in SYSTEMS.items():
        state["current_system"] = sys_label
        records: list[dict] = []

        for item in DATASET:
            try:
                out = runner(item["question"])
                records.append({
                    "id":           item["id"],
                    "type":         item["type"],
                    "question":     item["question"],
                    "ground_truth": item["ground_truth"],
                    "answer":       out["answer"],
                    "contexts":     out["contexts"],
                    "tool_calls":   out.get("tool_calls", 0),
                    "error":        None,
                })
            except Exception as e:
                records.append({
                    "id":           item["id"],
                    "type":         item["type"],
                    "question":     item["question"],
                    "ground_truth": item["ground_truth"],
                    "answer":       f"오류: {e}",
                    "contexts":     ["오류 발생"],
                    "tool_calls":   0,
                    "error":        str(e),
                })
            state["progress"] += 1
            time.sleep(0.3)

        all_records[sys_key] = records

    # RAGAS 평가
    state["current_system"] = "RAGAS 계산 중..."
    scores: dict[str, dict] = {}
    ragas_error = None

    try:
        from ragas import evaluate as ragas_evaluate
        from ragas.metrics import (
            faithfulness, answer_relevancy,
            context_precision, context_recall,
        )
        from datasets import Dataset

        METRICS = [faithfulness, answer_relevancy, context_precision, context_recall]

        for sys_key, records in all_records.items():
            valid = [r for r in records if not r["error"]]
            if not valid:
                scores[sys_key] = {}
                continue
            ds = Dataset.from_list([
                {
                    "question":     r["question"],
                    "answer":       r["answer"],
                    "contexts":     r["contexts"],
                    "ground_truth": r["ground_truth"],
                }
                for r in valid
            ])
            result = ragas_evaluate(ds, metrics=METRICS)
            df     = result.to_pandas()
            scores[sys_key] = {
                col: round(float(df[col].mean()), 4)
                for col in df.select_dtypes("number").columns
            }
    except Exception as e:
        ragas_error = str(e)
        scores = {sys_key: {} for sys_key in all_records}

    state["results"] = {
        "scores":      scores,
        "records":     all_records,
        "ragas_error": ragas_error,
    }
    state["status"]         = "done"
    state["current_system"] = ""
