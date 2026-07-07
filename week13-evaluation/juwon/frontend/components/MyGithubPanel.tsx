"use client";

import { useState } from "react";
import Markdown from "@/components/Markdown";

type MyGithubResult = {
  username:        string;
  my_repo_count:   number;
  my_languages:    Record<string, number>;
  trend_languages: Record<string, number>;
  overlap_langs:   string[];
  match_pct:       number;
  analysis:        string;
  my_repos:        any[];
};

export default function MyGithubPanel({ report }: { report: any }) {
  const [username, setUsername] = useState("");
  const [result,   setResult]   = useState<MyGithubResult | null>(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState<string | null>(null);

  const analyze = async () => {
    if (!username.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res  = await fetch("http://localhost:8000/api/my-github", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ username: username.trim(), report }),
      });
      const data = await res.json();
      if (!res.ok) setError(data.detail ?? "분석 실패");
      else setResult(data);
    } catch {
      setError("서버 오류. 백엔드가 실행 중인지 확인해주세요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* 입력 */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
        <h2 className="text-lg font-bold mb-1 text-[#c9d1d9]">🧑‍💻 내 GitHub vs 트렌드 비교</h2>
        <p className="text-xs text-[#8b949e] mb-4">
          내 GitHub 레포를 현재 트렌딩과 비교해서 공부하면 좋을 기술을 추천해드립니다
        </p>
        <div className="flex gap-2">
          <input value={username} onChange={(e) => setUsername(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && analyze()}
            placeholder="GitHub 유저네임 입력 (예: yoonjuwon0618)"
            className="flex-1 bg-[#0d1117] border border-[#30363d] rounded-lg px-3 py-2 text-sm text-white placeholder-[#484f58] focus:outline-none focus:border-[#58a6ff]" />
          <button onClick={analyze} disabled={loading || !username.trim()}
            className="bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 text-white text-sm font-semibold px-5 rounded-lg transition">
            {loading ? "분석 중..." : "🔍 분석"}
          </button>
        </div>
        {error && <p className="text-xs text-[#f85149] mt-2">{error}</p>}
      </div>

      {/* 결과 */}
      {result && (
        <>
          {/* 요약 카드 */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <p className="text-xs text-[#8b949e]">내 레포 수</p>
              <p className="text-xl font-bold mt-1">{result.my_repo_count}개</p>
            </div>
            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <p className="text-xs text-[#8b949e]">트렌드 일치도</p>
              <p className="text-xl font-bold mt-1 text-[#3fb950]">{result.match_pct}%</p>
            </div>
            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <p className="text-xs text-[#8b949e]">겹치는 언어</p>
              <p className="text-xl font-bold mt-1">{result.overlap_langs.length}개</p>
            </div>
          </div>

          {/* 언어 비교 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4">
              <h3 className="text-sm font-bold text-[#58a6ff] mb-3">내가 쓰는 언어</h3>
              <div className="space-y-2">
                {Object.entries(result.my_languages).map(([lang, cnt]) => {
                  const isOverlap = result.overlap_langs.includes(lang);
                  return (
                    <div key={lang} className="flex items-center justify-between">
                      <span className={`text-xs ${isOverlap ? "text-[#3fb950] font-semibold" : "text-[#8b949e]"}`}>
                        {isOverlap ? "✅ " : ""}{lang}
                      </span>
                      <span className="text-xs text-[#484f58]">{cnt}개</span>
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-4">
              <h3 className="text-sm font-bold text-[#d29e22] mb-3">트렌딩 언어</h3>
              <div className="space-y-2">
                {Object.entries(result.trend_languages).map(([lang, cnt]) => {
                  const isOverlap = result.overlap_langs.includes(lang);
                  return (
                    <div key={lang} className="flex items-center justify-between">
                      <span className={`text-xs ${isOverlap ? "text-[#3fb950] font-semibold" : "text-[#8b949e]"}`}>
                        {isOverlap ? "✅ " : ""}{lang}
                      </span>
                      <span className="text-xs text-[#484f58]">{cnt}개</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* AI 분석 */}
          <div className="bg-[#161b22] border border-[#58a6ff] rounded-xl overflow-hidden">
            <div className="px-5 py-3 bg-[#1c2d40] border-b border-[#58a6ff]">
              <span className="text-sm font-bold text-[#58a6ff]">🤖 AI 멘토 분석 결과</span>
            </div>
            <div className="px-5 py-4">
              <Markdown content={result.analysis} />
            </div>
          </div>

          {/* 내 레포 목록 */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
            <h3 className="text-sm font-bold text-[#c9d1d9] mb-3">📁 내 최근 레포 (fork 제외)</h3>
            <div className="space-y-2">
              {result.my_repos.map((r: any) => (
                <div key={r.name} className="flex items-center justify-between py-1.5 border-b border-[#21262d] last:border-0">
                  <div>
                    <span className="text-xs font-semibold text-[#58a6ff]">{r.name}</span>
                    {r.description && <span className="text-xs text-[#8b949e] ml-2">{r.description.slice(0, 50)}</span>}
                  </div>
                  <span className="text-xs text-[#484f58] shrink-0 ml-2">{r.language || "N/A"}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
