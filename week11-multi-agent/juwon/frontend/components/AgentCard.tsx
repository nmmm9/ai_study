import Markdown from "./Markdown";

const COLORS: Record<string, { border: string; badge: string }> = {
  blue:   { border: "border-[#58a6ff]", badge: "bg-[#1c2d40] text-[#58a6ff]" },
  green:  { border: "border-[#3fb950]", badge: "bg-[#1a2d1a] text-[#3fb950]" },
  yellow: { border: "border-[#d29e22]", badge: "bg-[#2d2208] text-[#d29e22]" },
};

type Props = {
  title:   string;
  icon:    string;
  content: string;
  color:   string;
};

export default function AgentCard({ title, icon, content, color }: Props) {
  const c = COLORS[color] ?? { border: "border-[#30363d]", badge: "bg-[#21262d] text-[#8b949e]" };

  return (
    <div className={`bg-[#161b22] border ${c.border} rounded-xl flex flex-col`}>
      <div className={`flex items-center gap-2 px-4 py-3 border-b border-[#21262d]`}>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${c.badge}`}>{icon} {title}</span>
      </div>
      <div className="px-4 py-3 overflow-y-auto max-h-72">
        {content
          ? <Markdown content={content} />
          : <p className="text-xs text-[#484f58]">분석 중...</p>
        }
      </div>
    </div>
  );
}
