"""
evaluator.py
────────────
week13 핵심 평가 로직

1. week12 Agentic RAG 파이프라인에 테스트 질문을 돌림
2. (question, answer, contexts, ground_truth) 수집
3. RAGAS 4개 지표로 평가
4. 결과를 JSON으로 저장

LangSmith 연동:
  .env에 LANGCHAIN_API_KEY + LANGCHAIN_TRACING_V2=true 설정 시
  RAGAS가 사용하는 LLM 호출이 자동으로 LangSmith에 트레이싱됨.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

_HERE = Path(__file__).parent
load_dotenv(_HERE / ".env")

# week12 RAG 파이프라인 경로 추가
_WEEK12 = _HERE.parent.parent / "week12-agentic-rag" / "minseon"
sys.path.insert(0, str(_WEEK12))

RESULTS_DIR = _HERE / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ── week12 RAG 실행 ────────────────────────────────────────────────────────
def _run_rag(question: str) -> tuple[str, list[str]]:
    """week12 그래프를 실행해 (answer, contexts) 반환."""
    from graph import run as rag_run

    result   = rag_run(question)
    answer   = result.get("answer", "")
    documents = result.get("documents", [])

    contexts = [
        f"{d['title']}\n{d['content'][:800]}"
        for d in documents
    ] if documents else ["관련 문서를 찾지 못했습니다."]

    return answer, contexts


# ── RAGAS 평가 ─────────────────────────────────────────────────────────────
def _build_ragas_dataset(records: list[dict]):
    """records → HuggingFace Dataset (RAGAS 입력 형식)."""
    from datasets import Dataset

    return Dataset.from_dict({
        "question":     [r["question"]     for r in records],
        "answer":       [r["answer"]       for r in records],
        "contexts":     [r["contexts"]     for r in records],
        "ground_truth": [r["ground_truth"] for r in records],
    })


def _run_ragas(dataset) -> dict:
    """RAGAS 4개 지표 계산. 0.1.x / 0.2.x API 모두 대응."""
    try:
        # 0.2.x API
        from ragas import evaluate
        from ragas.metrics import (
            Faithfulness,
            AnswerRelevancy,
            ContextPrecision,
            ContextRecall,
        )
        metrics = [Faithfulness(), AnswerRelevancy(), ContextPrecision(), ContextRecall()]
        result  = evaluate(dataset, metrics=metrics)
        return result.to_pandas().mean(numeric_only=True).to_dict()

    except ImportError:
        pass

    # 0.1.x API
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )
    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    result  = evaluate(dataset, metrics=metrics)
    return dict(result)


# ── 메인 평가 실행 ─────────────────────────────────────────────────────────
def run_evaluation(
    test_data: list[dict],
    progress_callback=None,
) -> dict:
    """
    전체 평가 파이프라인 실행.

    Args:
        test_data: dataset.TEST_DATASET
        progress_callback: 진행률 알림용 콜백 fn(current, total, item_id)

    Returns:
        {
          "timestamp": str,
          "total": int,
          "records": [{"id", "category", "question", "answer",
                       "contexts", "ground_truth", "latency_s"}, ...],
          "ragas_scores": {"faithfulness": float, ...},
          "per_record_scores": [...],
        }
    """
    total   = len(test_data)
    records = []

    print(f"\n[평가 시작] 총 {total}개 질문")
    for i, item in enumerate(test_data):
        if progress_callback:
            progress_callback(i, total, item["id"])

        print(f"  [{i+1}/{total}] {item['id']} — {item['question'][:40]}...")
        t0      = time.time()
        answer, contexts = _run_rag(item["question"])
        latency = round(time.time() - t0, 2)

        records.append({
            "id":           item["id"],
            "category":     item["category"],
            "question":     item["question"],
            "answer":       answer,
            "contexts":     contexts,
            "ground_truth": item["ground_truth"],
            "latency_s":    latency,
        })

    # RAGAS 평가
    print("\n[RAGAS 평가 중...]")
    ragas_scores     = {}
    per_record_scores = []

    try:
        dataset = _build_ragas_dataset(records)
        ragas_scores = _run_ragas(dataset)

        # 개별 점수도 저장 (DataFrame 반환 버전)
        try:
            from ragas import evaluate
            from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
            df = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision, context_recall]).to_pandas()
            for idx, row in df.iterrows():
                per_record_scores.append({
                    "id":                records[idx]["id"],
                    "faithfulness":      round(float(row.get("faithfulness", 0)), 3),
                    "answer_relevancy":  round(float(row.get("answer_relevancy", 0)), 3),
                    "context_precision": round(float(row.get("context_precision", 0)), 3),
                    "context_recall":    round(float(row.get("context_recall", 0)), 3),
                })
        except Exception:
            pass

        print("[RAGAS 평가 완료]")
        for k, v in ragas_scores.items():
            print(f"  {k}: {v:.3f}")

    except Exception as e:
        print(f"[경고] RAGAS 평가 실패: {e}")
        ragas_scores = {"error": str(e)}

    result = {
        "timestamp":        datetime.now().isoformat(),
        "total":            total,
        "records":          records,
        "ragas_scores":     {k: round(float(v), 4) for k, v in ragas_scores.items() if k != "error"},
        "ragas_error":      ragas_scores.get("error"),
        "per_record_scores": per_record_scores,
    }

    # 결과 저장
    out_path = RESULTS_DIR / f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[결과 저장] {out_path}")

    return result


def load_latest_result() -> dict | None:
    """가장 최근 평가 결과 JSON 로드."""
    files = sorted(RESULTS_DIR.glob("eval_*.json"), reverse=True)
    if not files:
        return None
    return json.loads(files[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    from dataset import TEST_DATASET
    run_evaluation(TEST_DATASET)
