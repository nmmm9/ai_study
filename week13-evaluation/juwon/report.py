"""
report.py - HTML 평가 보고서 생성기

generate_report(data, output_path) 호출 시 대화형 HTML 파일 생성
"""
from pathlib import Path
import json


METRIC_LABELS = {
    "faithfulness":      "Faithfulness",
    "answer_relevancy":  "Answer Relevancy",
    "context_precision": "Context Precision",
    "context_recall":    "Context Recall",
}

SYSTEM_LABELS = {
    "simple_rag":   "Simple RAG (A)",
    "advanced_rag": "Advanced RAG (B)",
    "agentic_rag":  "Agentic RAG (C)",
}

SYSTEM_COLORS = {
    "simple_rag":   "#6366f1",
    "advanced_rag": "#22c55e",
    "agentic_rag":  "#f59e0b",
}


def _score_color(score: float) -> str:
    if score >= 0.8:
        return "#22c55e"
    if score >= 0.6:
        return "#f59e0b"
    return "#ef4444"


def _find_failures(records: dict[str, list[dict]], threshold: float = 0.7) -> list[dict]:
    """모든 시스템에서 점수가 낮은 케이스 추출 (answer_relevancy 기준)"""
    failures = []
    for sys_name, recs in records.items():
        for r in recs:
            if r.get("error"):
                failures.append({**r, "failure_reason": f"실행 오류: {r['error']}"})
    return failures[:10]


def generate_report(data: dict, output_path: Path):
    scores  = data["scores"]    # {system_name: {metric: score}}
    records = data["records"]   # {system_name: [record]}
    ts      = data["timestamp"]
    n       = data["dataset_size"]

    # ── Chart.js 데이터 ──────────────────────────────────────────────
    metrics      = list(METRIC_LABELS.keys())
    chart_labels = [METRIC_LABELS[m] for m in metrics]
    chart_datasets = []
    for sys_name, sys_scores in scores.items():
        chart_datasets.append({
            "label":           SYSTEM_LABELS.get(sys_name, sys_name),
            "data":            [sys_scores.get(m, 0) for m in metrics],
            "backgroundColor": SYSTEM_COLORS.get(sys_name, "#888"),
            "borderColor":     SYSTEM_COLORS.get(sys_name, "#888"),
            "borderWidth":     2,
        })

    radar_datasets = []
    for sys_name, sys_scores in scores.items():
        radar_datasets.append({
            "label":            SYSTEM_LABELS.get(sys_name, sys_name),
            "data":             [sys_scores.get(m, 0) for m in metrics],
            "backgroundColor":  SYSTEM_COLORS.get(sys_name, "#888") + "33",
            "borderColor":      SYSTEM_COLORS.get(sys_name, "#888"),
            "pointBackgroundColor": SYSTEM_COLORS.get(sys_name, "#888"),
            "borderWidth": 2,
        })

    # ── 점수 테이블 HTML ─────────────────────────────────────────────
    def score_cell(v):
        color = _score_color(v)
        return f'<td style="color:{color};font-weight:700;text-align:center">{v:.3f}</td>'

    table_rows = ""
    for m in metrics:
        row = f"<tr><td>{METRIC_LABELS[m]}</td>"
        for sys_name in scores:
            v = scores[sys_name].get(m, 0)
            row += score_cell(v)
        row += "</tr>"
        table_rows += row

    # 평균 행
    avg_row = "<tr style='background:#f8fafc;font-weight:bold'><td>평균</td>"
    for sys_name in scores:
        vals = [scores[sys_name].get(m, 0) for m in metrics]
        avg  = sum(vals) / len(vals) if vals else 0
        avg_row += score_cell(avg)
    avg_row += "</tr>"

    sys_headers = "".join(
        f'<th style="color:{SYSTEM_COLORS[s]}">{SYSTEM_LABELS.get(s, s)}</th>'
        for s in scores
    )

    # ── 실패 케이스 ──────────────────────────────────────────────────
    failures      = _find_failures(records)
    failure_cards = ""
    if failures:
        for f in failures:
            failure_cards += f"""
            <div class="failure-card">
              <div class="tag">{SYSTEM_LABELS.get(f['system'], f['system'])} | Q{f['id']} ({f['type']})</div>
              <p><strong>Q:</strong> {f['question']}</p>
              <p><strong>A:</strong> {f['answer'][:300]}...</p>
              <p class="reason"><strong>원인:</strong> {f.get('failure_reason', '점수 미달')}</p>
            </div>"""
    else:
        failure_cards = "<p style='color:#6b7280'>오류 없이 모든 질문을 처리했습니다.</p>"

    # ── 질문별 상세 테이블 ───────────────────────────────────────────
    first_sys   = list(records.keys())[0] if records else "simple_rag"
    questions   = records.get(first_sys, [])
    detail_rows = ""
    for item in questions:
        qid  = item["id"]
        qtype = item["type"]
        q    = item["question"]
        cells = f"<td>{qid}</td><td><span class='type-tag'>{qtype}</span></td><td>{q}</td>"
        for sys_name in records:
            sys_recs = {r["id"]: r for r in records[sys_name]}
            rec      = sys_recs.get(qid, {})
            ans      = rec.get("answer", "")[:120] + "..."
            tc       = rec.get("tool_calls", 0)
            tc_badge = f' <span class="tc-badge">🔧{tc}</span>' if tc else ""
            cells   += f"<td>{ans}{tc_badge}</td>"
        detail_rows += f"<tr>{cells}</tr>"

    detail_sys_headers = "".join(
        f'<th style="color:{SYSTEM_COLORS.get(s, \"#888\")}">{SYSTEM_LABELS.get(s, s)}</th>'
        for s in records
    )

    # ── 개선 분석 ────────────────────────────────────────────────────
    improvements = _generate_improvements(scores, metrics)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Week 13 - RAG 시스템 평가 보고서</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #f1f5f9; color: #1e293b; }}
  header {{ background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff; padding: 2rem; }}
  header h1 {{ font-size: 1.8rem; margin-bottom: .4rem; }}
  header p  {{ opacity: .8; font-size: .95rem; }}
  .container {{ max-width: 1100px; margin: 2rem auto; padding: 0 1rem; }}
  .card {{ background: #fff; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  h2 {{ font-size: 1.2rem; margin-bottom: 1rem; color: #374151; border-left: 4px solid #6366f1; padding-left: .6rem; }}
  .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
  canvas {{ max-height: 320px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .9rem; }}
  th, td {{ padding: .6rem .8rem; border-bottom: 1px solid #e5e7eb; }}
  th {{ background: #f8fafc; font-weight: 600; }}
  tr:hover td {{ background: #f8fafc; }}
  .type-tag {{ background: #e0e7ff; color: #4338ca; font-size: .75rem; padding: 2px 6px; border-radius: 9px; }}
  .tc-badge {{ background: #fef3c7; color: #92400e; font-size: .75rem; padding: 1px 5px; border-radius: 9px; }}
  .failure-card {{ background: #fff7f7; border: 1px solid #fca5a5; border-radius: 8px; padding: 1rem; margin-bottom: .8rem; }}
  .failure-card .tag {{ color: #ef4444; font-size: .8rem; font-weight: 600; margin-bottom: .4rem; }}
  .failure-card .reason {{ color: #6b7280; font-size: .85rem; margin-top: .4rem; }}
  .improvement-list li {{ margin-bottom: .6rem; line-height: 1.6; }}
  .meta-pills {{ display: flex; gap: .5rem; flex-wrap: wrap; margin-top: .8rem; }}
  .pill {{ background: #e0e7ff; color: #3730a3; font-size: .8rem; padding: 3px 10px; border-radius: 20px; }}
  @media (max-width: 700px) {{ .charts-grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<header>
  <h1>Week 13 — RAG 시스템 평가 보고서</h1>
  <p>생성: {ts} &nbsp;|&nbsp; 질문 수: {n}개</p>
  <div class="meta-pills">
    <span class="pill" style="background:rgba(255,255,255,.2);color:#fff">Simple RAG (A)</span>
    <span class="pill" style="background:rgba(255,255,255,.2);color:#fff">Advanced RAG (B)</span>
    <span class="pill" style="background:rgba(255,255,255,.2);color:#fff">Agentic RAG (C)</span>
  </div>
</header>

<div class="container">

  <!-- 점수 요약 테이블 -->
  <div class="card">
    <h2>RAGAS 메트릭 비교</h2>
    <table>
      <thead><tr><th>메트릭</th>{sys_headers}</tr></thead>
      <tbody>{table_rows}{avg_row}</tbody>
    </table>
    <p style="font-size:.8rem;color:#9ca3af;margin-top:.5rem">
      ● 초록(≥0.8) ● 주황(≥0.6) ● 빨강(&lt;0.6)
    </p>
  </div>

  <!-- 차트 -->
  <div class="charts-grid">
    <div class="card">
      <h2>메트릭별 점수 (막대)</h2>
      <canvas id="barChart"></canvas>
    </div>
    <div class="card">
      <h2>종합 점수 (레이더)</h2>
      <canvas id="radarChart"></canvas>
    </div>
  </div>

  <!-- 개선 분석 -->
  <div class="card">
    <h2>시스템별 분석 및 개선점</h2>
    <ul class="improvement-list">{improvements}</ul>
  </div>

  <!-- 실패 케이스 -->
  <div class="card">
    <h2>실패 케이스 분석</h2>
    {failure_cards}
  </div>

  <!-- 질문별 상세 -->
  <div class="card">
    <h2>질문별 답변 상세</h2>
    <div style="overflow-x:auto">
      <table>
        <thead><tr><th>#</th><th>유형</th><th>질문</th>{detail_sys_headers}</tr></thead>
        <tbody>{detail_rows}</tbody>
      </table>
    </div>
  </div>

</div>

<script>
const BAR_DATA = {{
  labels: {json.dumps(chart_labels, ensure_ascii=False)},
  datasets: {json.dumps(chart_datasets, ensure_ascii=False)},
}};
new Chart(document.getElementById('barChart'), {{
  type: 'bar',
  data: BAR_DATA,
  options: {{
    responsive: true,
    scales: {{ y: {{ min: 0, max: 1 }} }},
    plugins: {{ legend: {{ position: 'bottom' }} }},
  }},
}});

const RADAR_DATA = {{
  labels: {json.dumps(chart_labels, ensure_ascii=False)},
  datasets: {json.dumps(radar_datasets, ensure_ascii=False)},
}};
new Chart(document.getElementById('radarChart'), {{
  type: 'radar',
  data: RADAR_DATA,
  options: {{
    responsive: true,
    scales: {{ r: {{ min: 0, max: 1, ticks: {{ stepSize: 0.2 }} }} }},
    plugins: {{ legend: {{ position: 'bottom' }} }},
  }},
}});
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def _generate_improvements(scores: dict, metrics: list[str]) -> str:
    lines = []
    for sys_name, sys_scores in scores.items():
        label = SYSTEM_LABELS.get(sys_name, sys_name)
        avg   = sum(sys_scores.get(m, 0) for m in metrics) / len(metrics)
        weak  = [METRIC_LABELS[m] for m in metrics if sys_scores.get(m, 0) < 0.65]
        color = SYSTEM_COLORS.get(sys_name, "#888")

        note = ""
        if sys_name == "simple_rag":
            note = "단일 쿼리 검색 한계 → Multi-Query 확장으로 커버리지 개선 가능"
        elif sys_name == "advanced_rag":
            note = "쿼리 확장 + RRF 효과 검증 → 리랭킹 모델(Cross-Encoder) 추가 시 정밀도 향상 기대"
        elif sys_name == "agentic_rag":
            note = "자율적 도구 호출로 유연한 검색 가능 → 프롬프트 튜닝으로 불필요한 호출 감소 가능"

        weak_str = f" | 취약 메트릭: {', '.join(weak)}" if weak else ""
        lines.append(
            f'<li><strong style="color:{color}">{label}</strong> — 평균 {avg:.3f}{weak_str}<br>'
            f'<span style="color:#6b7280">{note}</span></li>'
        )
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("사용법: python report.py results/results_<timestamp>.json")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    out = Path(sys.argv[1]).with_suffix(".html")
    generate_report(data, out)
    print(f"보고서 생성: {out}")
