type Repo = {
  name:        string;
  description: string;
  stars:       number;
  forks:       number;
  language:    string;
  url:         string;
  trend_score: number;
};

export default function RepoList({ repos }: { repos: Repo[] }) {
  return (
    <div>
      <h2 className="text-lg font-bold mb-3 text-[#c9d1d9]">🔥 트렌딩 레포</h2>
      <div className="space-y-2">
        {repos.slice(0, 10).map((repo) => (
          <div key={repo.name} className="bg-[#161b22] border border-[#30363d] rounded-lg px-4 py-3 flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <a href={repo.url} target="_blank" rel="noopener noreferrer"
                className="text-[#58a6ff] font-semibold hover:underline text-sm">
                {repo.name}
              </a>
              <span className="ml-2 text-xs bg-[#21262d] text-[#8b949e] rounded-full px-2 py-0.5">
                {repo.language}
              </span>
              <p className="text-xs text-[#8b949e] mt-1 truncate">{repo.description || "설명 없음"}</p>
            </div>
            <div className="text-right ml-4 shrink-0 space-y-1">
              <p className="text-xs text-[#8b949e]">⭐ {repo.stars.toLocaleString()}</p>
              <p className="text-xs text-[#3fb950] font-semibold">점수 {repo.trend_score}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
