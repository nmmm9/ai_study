"use client";

import { useEffect, useState } from "react";

type LangPrediction = {
  language:   string;
  confidence: number;
  reason:     string;
};

type PredictionResult = {
  predicted_languages:   LangPrediction[];
  predicted_topics:      string[];
  predicted_repos:       string[];
  overall_prediction:    string;
  confidence_level:      string;
  data_period:           string;
  analyzed_days:         number;
  historical_lang_trend: Record<string, number>;
  total_lang_counts:     Record<string, number>;
  rising_repos:          string[];
  record_count:          number;
};

const CONFIDENCE_COLOR: Record<string, string> = {
  "높음": "text-[#3fb950] border-[#3fb950]",
  "보통": "text-[#d29e22] border-[#d29e22]",
  "낮음": "text-[#f85149] border-[#f85149]",
};

export default function TrendPredictionPanel() {
  const [result,  setResult]  = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const fetchPrediction = async () => {
    setLoading(true);
    setError(null);
    try {
      const res  = await fetch("http://localhost:8000/api/predict");
      const data = await res.json();
      if (!res.ok) setError(data.detail ?? "예측 실패");
      else setResult(data);
    } catch {
      setError("서버 오류. 백엔드가 실행 중인지 확인해주세요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* 헤더 */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
        <h2 className="text-lg font-bold mb-1 text-[#c9d1d9]">📈 미래 트렌드 예측</h2>
        <p className="text-xs text-[#8b949e] mb-4">
          GitHub Actions로 매일 수집된 트렌드 데이터를 시계열로 분석하여 앞으로 1~2주 내 유행할 기술을 예측합니다
        </p>
        <button
          onClick={fetchPrediction}
          disabled={loading}
          className="bg-[#6e40c9] hover:bg-[#8957e5] disabled:opacity-50 text-white font-semibold px-6 py-2 rounded-lg text-sm transition"
        >
          {loading ? "예측 중..." : "🔮 트렌드 예측 시작"}
        </button>
        {error && <p className="text-xs text-[#f85149] mt-2">{error}</p>}
      </div>

      {result && (
        <>
          {/* 데이터 요약 */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <p className="text-xs text-[#8b949e]">분석 기간</p>
              <p className="text-sm font-bold mt-1">{result.data_period}</p>
            </div>
            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <p className="text-xs text-[#8b949e]">분석 일수</p>
              <p className="text-xl font-bold mt-1">{result.analyzed_days}일</p>
            </div>
            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <p className="text-xs text-[#8b949e]">예측 신뢰도</p>
              <p className={`text-xl font-bold mt-1 ${(CONFIDENCE_COLOR[result.confidence_level] ?? "text-white").split(" ")[0]}`}>
                {result.confidence_level}
              </p>
            </div>
          </div>

          {/* 예측 언어 */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
            <h3 className="text-sm font-bold text-[#c9d1d9] mb-4">🏆 예측 인기 언어 (1~2주 내)</h3>
            <div className="space-y-3">
              {result.predicted_languages.map((lang, i) => (
                <div key={lang.language}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[#484f58] w-4">{i + 1}</span>
                      <span className="text-sm font-semibold text-[#c9d1d9]">{lang.language}</span>
                      <span className="text-xs text-[#8b949e]">{lang.reason}</span>
                    </div>
                    <span className="text-sm font-bold text-[#58a6ff]">{lang.confidence}%</span>
                  </div>
                  <div className="w-full bg-[#21262d] rounded-full h-1.5">
                    <div
                      className="bg-[#58a6ff] h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${lang.confidence}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 예측 주제 & 레포 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4">
              <h3 className="text-sm font-bold text-[#d29e22] mb-3">🔖 예측 핫 토픽</h3>
              <div className="flex flex-wrap gap-2">
                {result.predicted_topics.map((topic) => (
                  <span key={topic} className="bg-[#272e38] border border-[#d29e22] text-[#d29e22] text-xs px-2.5 py-1 rounded-full">
                    {topic}
                  </span>
                ))}
              </div>
            </div>
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4">
              <h3 className="text-sm font-bold text-[#3fb950] mb-3">📁 예상 레포 유형</h3>
              <ul className="space-y-1.5">
                {result.predicted_repos.map((repo) => (
                  <li key={repo} className="text-xs text-[#8b949e] flex items-start gap-1.5">
                    <span className="text-[#3fb950] mt-0.5">›</span>{repo}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* 종합 예측 */}
          <div className="bg-[#161b22] border border-[#6e40c9] rounded-xl overflow-hidden">
            <div className="px-5 py-3 bg-[#1e1a2e] border-b border-[#6e40c9]">
              <span className="text-sm font-bold text-[#8957e5]">🔮 AI 종합 트렌드 예측</span>
            </div>
            <p className="px-5 py-4 text-sm text-[#c9d1d9] leading-relaxed whitespace-pre-wrap">
              {result.overall_prediction}
            </p>
          </div>

          {/* 과거 언어 상승세 */}
          {Object.keys(result.historical_lang_trend).length > 0 && (
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
              <h3 className="text-sm font-bold text-[#c9d1d9] mb-3">📊 과거 데이터 기반 언어 상승률</h3>
              <div className="space-y-2">
                {Object.entries(result.historical_lang_trend).map(([lang, score]) => {
                  const pct     = Math.min(Math.abs(score) * 100, 100);
                  const isRising = score >= 0;
                  return (
                    <div key={lang} className="flex items-center gap-3">
                      <span className="text-xs text-[#8b949e] w-20 shrink-0">{lang}</span>
                      <div className="flex-1 bg-[#21262d] rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full transition-all duration-300 ${isRising ? "bg-[#3fb950]" : "bg-[#f85149]"}`}
                          style={{ width: `${Math.max(pct, 2)}%` }}
                        />
                      </div>
                      <span className={`text-xs font-semibold w-14 text-right ${isRising ? "text-[#3fb950]" : "text-[#f85149]"}`}>
                        {isRising ? "+" : ""}{(score * 100).toFixed(0)}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 지속 등장 레포 */}
          {result.rising_repos.length > 0 && (
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4">
              <h3 className="text-sm font-bold text-[#c9d1d9] mb-2">🔁 최근 지속 등장 레포 (관심 지속)</h3>
              <div className="flex flex-wrap gap-2">
                {result.rising_repos.map((r) => (
                  <span key={r} className="bg-[#21262d] text-[#8b949e] text-xs px-2.5 py-1 rounded">
                    {r}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
