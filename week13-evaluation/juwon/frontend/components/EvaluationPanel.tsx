"use client";

import { useEffect, useState } from "react";

type Scores  = { faithfulness: number; answer_relevancy: number; context_precision: number };
type Results = {
  evaluated_at: string;
  n_questions:  number;
  summary:      Record<string, Scores>;
  systems:      Record<string, { scores: Scores; details: any[] }>;
};

const SYSTEM_LABEL: Record<string, string> = {
  simple_rag:   "Simple RAG",
  advanced_rag: "Advanced RAG",
  agentic_rag:  "Agentic RAG",
};

const SYSTEM_DESC: Record<string, string> = {
  simple_rag:   "현재 분석만 사용 (RAG 없음)",
  advanced_rag: "항상 벡터 검색",
  agentic_rag:  "에이전트가 스스로 판단해서 검색",
};

const SYSTEM_COLOR: Record<string, string> = {
  simple_rag:   "text-[#8b949e]",
  advanced_rag: "text-[#58a6ff]",
  agentic_rag:  "text-[#3fb950]",
};

function ScoreBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "#3fb950" : pct >= 60 ? "#d29e22" : "#f85149";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-[#21262d] rounded-full h-2">
        <div className="h-2 rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs font-bold w-10 text-right" style={{ color }}>{pct}%</span>
    </div>
  );
}

export default function EvaluationPanel() {
  const [results,   setResults]   = useState<Results | null>(null);
  const [loading,   setLoading]   = useState(false);
  const [running,   setRunning]   = useState(false);
  const [nQuestion, setNQuestion] = useState(20);
  const [msg,       setMsg]       = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    fetch("http://localhost:8000/api/evaluate/results")
      .then((r) => r.json())
      .then((d) => setResults(d.message ? null : d))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const runEval = async () => {
    setRunning(true);
    setMsg("평가 실행 중... (약 2~5분 소요됩니다)");
    try {
      const res  = await fetch("http://localhost:8000/api/evaluate", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ n_questions: nQuestion }),
      });
      if (res.ok) {
        const data = await res.json();
        setResults(data);
        setMsg(null);
      } else {
        const err = await res.json();
        setMsg("❌ " + (err.detail ?? "평가 실패"));
      }
    } catch {
      setMsg("❌ 서버 오류");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 실행 컨트롤 */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
        <h2 className="text-lg font-bold mb-1 text-[#c9d1d9]">🧪 RAG 시스템 평가 (RAGAS)</h2>
        <p className="text-xs text-[#8b949e] mb-4">
          3개 RAG 시스템을 동일한 질문으로 비교 평가합니다 — faithfulness · answer_relevancy · context_precision
        </p>
        <div className="flex items-center gap-3 mb-3">
          <label className="text-xs text-[#8b949e]">질문 수:</label>
          {[5, 10, 20].map((n) => (
            <button key={n} onClick={() => setNQuestion(n)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                nQuestion === n ? "bg-[#1c2d40] border border-[#58a6ff] text-[#58a6ff]" : "bg-[#21262d] text-[#8b949e] hover:text-white"
              }`}>
              {n}개
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <button onClick={runEval} disabled={running}
            className="bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 text-white font-semibold py-2 px-5 rounded-lg text-sm transition">
            {running ? "평가 중..." : "▶ 평가 시작"}
          </button>
          <span className="text-xs text-[#8b949e]">예상 비용: ~${(nQuestion * 0.003).toFixed(3)}</span>
        </div>
        {msg && <p className={`text-xs mt-3 ${msg.startsWith("❌") ? "text-[#f85149]" : "text-[#d29e22]"}`}>{msg}</p>}
      </div>

      {/* 결과 */}
      {loading && <p className="text-xs text-[#8b949e]">결과 로딩 중...</p>}
      {!loading && !results && (
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-6 text-center text-[#8b949e] text-sm">
          아직 평가 결과가 없습니다. 위에서 평가를 실행해주세요.
        </div>
      )}
      {results && (
        <>
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-[#c9d1d9]">📊 시스템별 점수 비교</h3>
              <span className="text-xs text-[#8b949e]">{results.evaluated_at?.slice(0, 16).replace("T", " ")} · {results.n_questions}개 질문</span>
            </div>
            <div className="space-y-5">
              {Object.entries(results.summary).map(([sys, scores]) => (
                <div key={sys} className="bg-[#0d1117] border border-[#21262d] rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className={`font-bold text-sm ${SYSTEM_COLOR[sys]}`}>{SYSTEM_LABEL[sys] ?? sys}</span>
                    <span className="text-xs text-[#484f58]">— {SYSTEM_DESC[sys]}</span>
                  </div>
                  <div className="space-y-2">
                    {[
                      { label: "Faithfulness",       key: "faithfulness" },
                      { label: "Answer Relevancy",   key: "answer_relevancy" },
                      { label: "Context Precision",  key: "context_precision" },
                    ].map(({ label, key }) => (
                      <div key={key} className="grid grid-cols-[140px_1fr] items-center gap-3">
                        <span className="text-xs text-[#8b949e]">{label}</span>
                        <ScoreBar value={(scores as any)[key] ?? 0} />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 실패 사례 분석 */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
            <h3 className="font-bold text-[#c9d1d9] mb-3">🔍 실패 사례 분석 (점수 낮은 케이스)</h3>
            {Object.entries(results.systems).map(([sys, data]) => {
              const weak = data.details
                .map((d: any, i: number) => ({ ...d, idx: i }))
                .sort((a: any, b: any) => a.answer?.length - b.answer?.length)
                .slice(0, 2);
              return (
                <div key={sys} className="mb-4">
                  <p className={`text-xs font-bold mb-2 ${SYSTEM_COLOR[sys]}`}>{SYSTEM_LABEL[sys]}</p>
                  {weak.map((item: any, i: number) => (
                    <div key={i} className="bg-[#0d1117] rounded-lg p-3 mb-2 text-xs">
                      <p className="text-[#8b949e] mb-1">Q: {item.question?.slice(0, 60)}...</p>
                      <p className="text-[#c9d1d9]">A: {item.answer?.slice(0, 100)}...</p>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
