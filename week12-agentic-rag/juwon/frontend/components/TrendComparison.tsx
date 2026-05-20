type Repo = { name: string; url: string; stars: number; trend_score: number; score_diff?: number; description: string };
type Comparison = { has_previous: boolean; new_repos: Repo[]; rising: Repo[]; falling: Repo[]; disappeared: Repo[] };

function RepoChip({ repo, badge }: { repo: Repo; badge: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between bg-[#0d1117] rounded-lg px-3 py-2">
      <div className="min-w-0">
        <a href={repo.url} target="_blank" rel="noopener noreferrer"
          className="text-xs text-[#58a6ff] hover:underline font-semibold truncate block">{repo.name}</a>
        <p className="text-xs text-[#8b949e] truncate">{repo.description || "설명 없음"}</p>
      </div>
      <div className="ml-3 shrink-0">{badge}</div>
    </div>
  );
}

export default function TrendComparison({ comparison }: { comparison: Comparison }) {
  if (!comparison?.has_previous) return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
      <h2 className="text-lg font-bold mb-1 text-[#c9d1d9]">📈 트렌드 변화</h2>
      <p className="text-xs text-[#8b949e]">비교할 이전 분석 데이터가 없어요. 한 번 더 실행하면 변화를 볼 수 있어요.</p>
    </div>
  );

  const sections = [
    { title: "🆕 새로 등장", repos: comparison.new_repos,  badge: () => <span className="text-xs bg-[#1c2d40] text-[#58a6ff] rounded-full px-2 py-0.5">NEW</span> },
    { title: "🚀 급등",      repos: comparison.rising,     badge: (r: Repo) => <span className="text-xs text-[#3fb950] font-bold">▲ +{r.score_diff}</span> },
    { title: "📉 급락",      repos: comparison.falling,    badge: (r: Repo) => <span className="text-xs text-[#f85149] font-bold">▼ {r.score_diff}</span> },
    { title: "👋 사라짐",    repos: comparison.disappeared, badge: () => <span className="text-xs bg-[#2a0d0d] text-[#f85149] rounded-full px-2 py-0.5">OUT</span> },
  ];

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
      <h2 className="text-lg font-bold mb-4 text-[#c9d1d9]">📈 트렌드 변화</h2>
      <div className="grid grid-cols-2 gap-4">
        {sections.map(({ title, repos, badge }) => (
          <div key={title}>
            <p className="text-xs font-bold text-[#8b949e] mb-2">{title}</p>
            {repos.length === 0
              ? <p className="text-xs text-[#484f58]">변화 없음</p>
              : <div className="space-y-2">{repos.map((r) => <RepoChip key={r.name} repo={r} badge={badge(r)} />)}</div>
            }
          </div>
        ))}
      </div>
    </div>
  );
}
