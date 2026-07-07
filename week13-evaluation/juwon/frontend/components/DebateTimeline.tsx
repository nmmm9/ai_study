import Markdown from "./Markdown";

type DebateItem = {
  role:    string;
  content: string;
};

const ROLE_CONFIG: Record<string, { label: string; border: string; header: string; icon: string }> = {
  supervisor: {
    label:  "Supervisor 종합",
    border: "border-[#58a6ff]",
    header: "bg-[#1c2d40] text-[#58a6ff]",
    icon:   "📊",
  },
  critic: {
    label:  "Critic 반론",
    border: "border-[#f85149]",
    header: "bg-[#2a0d0d] text-[#f85149]",
    icon:   "⚡",
  },
  judge: {
    label:  "Judge 최종 결정",
    border: "border-[#3fb950]",
    header: "bg-[#1a2d1a] text-[#3fb950]",
    icon:   "⚖️",
  },
};

export default function DebateTimeline({ history }: { history: DebateItem[] }) {
  if (!history.length) return null;

  return (
    <div>
      <h2 className="text-lg font-bold mb-3 text-[#c9d1d9]">💬 토론 타임라인</h2>
      <div className="space-y-4">
        {history.map((item, i) => {
          const cfg = ROLE_CONFIG[item.role] ?? {
            label:  item.role,
            border: "border-[#30363d]",
            header: "bg-[#21262d] text-[#8b949e]",
            icon:   "🤖",
          };
          return (
            <div key={i} className={`border ${cfg.border} rounded-xl overflow-hidden`}>
              <div className={`flex items-center gap-2 px-4 py-2.5 ${cfg.header}`}>
                <span className="text-xs font-bold">{cfg.icon} 라운드 {i + 1} — {cfg.label}</span>
              </div>
              <div className="bg-[#161b22] px-4 py-3">
                <Markdown content={item.content} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
