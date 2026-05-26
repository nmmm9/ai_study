"""
evaluate.py - 3개 RAG 시스템 RAGAS 평가 메인 스크립트

실행:
  python evaluate.py

출력:
  results/results_<timestamp>.json   (원본 답변 + RAGAS 점수)
  results/report_<timestamp>.html    (시각화 보고서)
"""
import os
import json
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# LangSmith 자동 트레이싱 설정
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT",    "week13-rag-evaluation")

# RAGAS 임포트
from ragas import evaluate as ragas_evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset

from systems import simple_rag, advanced_rag, agentic_rag

SYSTEMS = {
    "simple_rag":   simple_rag,
    "advanced_rag": advanced_rag,
    "agentic_rag":  agentic_rag,
}

METRICS = [faithfulness, answer_relevancy, context_precision, context_recall]

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def load_dataset() -> list[dict]:
    path = Path(__file__).parent / "dataset.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_system(system_name: str, module, dataset: list[dict]) -> list[dict]:
    """한 시스템으로 전체 데이터셋 실행"""
    print(f"\n[{system_name}] 실행 중 ({len(dataset)}개 질문)...")
    records = []
    for i, item in enumerate(dataset, 1):
        print(f"  [{i}/{len(dataset)}] {item['question'][:40]}...")
        try:
            out = module.run(item["question"])
            records.append({
                "id":           item["id"],
                "type":         item["type"],
                "question":     item["question"],
                "ground_truth": item["ground_truth"],
                "answer":       out["answer"],
                "contexts":     out["contexts"],
                "system":       system_name,
                "tool_calls":   out.get("tool_calls", 0),
                "error":        None,
            })
        except Exception as e:
            print(f"    오류: {e}")
            records.append({
                "id":           item["id"],
                "type":         item["type"],
                "question":     item["question"],
                "ground_truth": item["ground_truth"],
                "answer":       f"오류: {e}",
                "contexts":     ["오류 발생"],
                "system":       system_name,
                "tool_calls":   0,
                "error":        str(e),
            })
        time.sleep(0.5)  # rate limit
    return records


def compute_ragas(records: list[dict]) -> dict:
    """RAGAS 메트릭 계산 (오류 레코드 제외)"""
    valid = [r for r in records if r["error"] is None]
    if not valid:
        return {}

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
    scores = result.to_pandas().mean(numeric_only=True).to_dict()
    return {k: round(float(v), 4) for k, v in scores.items()}


def evaluate_all() -> dict:
    dataset = load_dataset()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_records: dict[str, list[dict]] = {}
    all_scores:  dict[str, dict]       = {}

    for name, module in SYSTEMS.items():
        records = run_system(name, module, dataset)
        all_records[name] = records

        print(f"  RAGAS 계산 중 [{name}]...")
        scores = compute_ragas(records)
        all_scores[name] = scores
        print(f"  점수: {scores}")

    # 결과 저장
    output = {
        "timestamp": timestamp,
        "dataset_size": len(dataset),
        "scores": all_scores,
        "records": all_records,
    }
    result_path = RESULTS_DIR / f"results_{timestamp}.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {result_path}")

    # HTML 리포트 생성
    from report import generate_report
    report_path = RESULTS_DIR / f"report_{timestamp}.html"
    generate_report(output, report_path)
    print(f"리포트 생성: {report_path}")

    return output


if __name__ == "__main__":
    evaluate_all()
