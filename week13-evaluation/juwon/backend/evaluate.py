"""
evaluate.py - RAGAS 기반 RAG 시스템 평가 (Week 13)

3개 시스템 비교:
  1. Simple RAG   - 현재 분석만 사용 (RAG 없음)
  2. Advanced RAG - 항상 벡터 검색
  3. Agentic RAG  - 에이전트가 스스로 판단해서 검색

평가 지표 (RAGAS):
  - faithfulness       : 답변이 컨텍스트에 충실한가
  - answer_relevancy   : 질문과 답변이 관련있는가
  - context_precision  : 검색된 컨텍스트가 정확한가
"""
import json
import os
from datetime import datetime

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

import advanced_rag
import simple_rag
from agentic_chat import run_agentic_chat
from storage import load_latest_history

load_dotenv()

DATASET_FILE = os.path.join(os.path.dirname(__file__), "dataset.json")
RESULT_FILE  = os.path.join(os.path.dirname(__file__), "eval_results.json")

_llm        = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY", ""))
_embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=os.getenv("OPENAI_API_KEY", ""))


def _load_dataset(n: int = 20) -> list[dict]:
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data[:n]


def _run_system(system_name: str, questions: list[dict], report: dict) -> list[dict]:
    results = []
    for item in questions:
        q  = item["question"]
        gt = item["ground_truth"]

        if system_name == "simple_rag":
            out = simple_rag.answer(q, report)
        elif system_name == "advanced_rag":
            out = advanced_rag.answer(q, report)
        else:
            out = run_agentic_chat(q, report)
            out["contexts"] = [out.get("reply", "")[:300]]

        results.append({
            "question":   q,
            "answer":     out["answer"] if "answer" in out else out.get("reply", ""),
            "contexts":   out.get("contexts", []),
            "ground_truth": gt,
        })
    return results


def _evaluate_system(results: list[dict]) -> dict:
    from datasets import Dataset
    from ragas import evaluate as ragas_evaluate
    from ragas.metrics import answer_relevancy, context_precision, faithfulness

    dataset = Dataset.from_dict({
        "question":     [r["question"]     for r in results],
        "answer":       [r["answer"]       for r in results],
        "contexts":     [r["contexts"]     for r in results],
        "ground_truth": [r["ground_truth"] for r in results],
    })
    scores = ragas_evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
        llm=_llm,
        embeddings=_embeddings,
    )
    return {
        "faithfulness":      round(float(scores["faithfulness"]), 3),
        "answer_relevancy":  round(float(scores["answer_relevancy"]), 3),
        "context_precision": round(float(scores["context_precision"]), 3),
    }


def run_evaluation(n_questions: int = 20) -> dict:
    """전체 평가 실행 — 결과를 eval_results.json에 저장하고 반환"""
    report = load_latest_history()
    if not report:
        return {"error": "분석 기록이 없습니다. 먼저 트렌드 분석을 실행해주세요."}

    questions = _load_dataset(n_questions)
    all_results = {}
    systems     = ["simple_rag", "advanced_rag", "agentic_rag"]

    for system in systems:
        print(f"[eval] {system} 평가 중... ({len(questions)}개 질문)")
        raw     = _run_system(system, questions, report)
        scores  = _evaluate_system(raw)
        all_results[system] = {
            "scores":  scores,
            "details": raw,
        }
        print(f"[eval] {system} 완료: {scores}")

    result = {
        "evaluated_at":  datetime.now().isoformat(),
        "n_questions":   n_questions,
        "systems":       all_results,
        "summary": {
            s: all_results[s]["scores"] for s in systems
        },
    }

    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def load_eval_results() -> dict | None:
    if not os.path.exists(RESULT_FILE):
        return None
    with open(RESULT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
