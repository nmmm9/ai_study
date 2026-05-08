import type { Stats } from "@/types/compare";

interface StatsBarProps {
  rawStats: Stats;
  chunkedStats: Stats;
}

function Bar({
  label,
  rawValue,
  chunkedValue,
  rawDisplay,
  chunkedDisplay,
}: {
  label: string;
  rawValue: number;
  chunkedValue: number;
  rawDisplay: string;
  chunkedDisplay: string;
}) {
  const max = Math.max(rawValue, chunkedValue, 1);
  const rawPct = (rawValue / max) * 100;
  const chunkedPct = (chunkedValue / max) * 100;

  return (
    <div className="space-y-1.5">
      <p className="text-[10px] tracking-widest uppercase text-pearl-muted">
        {label}
      </p>
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span className="w-10 text-[10px] text-bad">Raw</span>
          <div className="relative h-5 flex-1 rounded-md bg-base-100">
            <div
              className="animate-bar-grow h-full rounded-md bg-bad/30"
              style={{ width: `${rawPct}%` }}
            />
          </div>
          <span className="w-20 text-right text-xs text-bad">{rawDisplay}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-10 text-[10px] text-good">Chunk</span>
          <div className="relative h-5 flex-1 rounded-md bg-base-100">
            <div
              className="animate-bar-grow h-full rounded-md bg-good/30"
              style={{ width: `${chunkedPct}%` }}
            />
          </div>
          <span className="w-20 text-right text-xs font-medium text-good">
            {chunkedDisplay}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function StatsBar({ rawStats, chunkedStats }: StatsBarProps) {
  const savings =
    rawStats.total_tokens > 0
      ? Math.round(
          ((rawStats.total_tokens - chunkedStats.total_tokens) /
            rawStats.total_tokens) *
            100
        )
      : 0;

  return (
    <div className="animate-fade-in-up rounded-2xl border border-stroke bg-base-50 p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xs font-medium tracking-widest uppercase text-pearl-dim">
          비교 통계
        </h2>
        <span className="rounded-full bg-gold/10 px-3 py-0.5 text-sm font-semibold text-gold">
          절감률 {savings}%
        </span>
      </div>
      <div className="grid grid-cols-3 gap-6">
        <Bar
          label="토큰"
          rawValue={rawStats.total_tokens}
          chunkedValue={chunkedStats.total_tokens}
          rawDisplay={rawStats.total_tokens.toLocaleString()}
          chunkedDisplay={chunkedStats.total_tokens.toLocaleString()}
        />
        <Bar
          label="시간"
          rawValue={rawStats.time_ms}
          chunkedValue={chunkedStats.time_ms}
          rawDisplay={`${(rawStats.time_ms / 1000).toFixed(1)}s`}
          chunkedDisplay={`${(chunkedStats.time_ms / 1000).toFixed(1)}s`}
        />
        <Bar
          label="비용"
          rawValue={rawStats.cost_usd}
          chunkedValue={chunkedStats.cost_usd}
          rawDisplay={`$${rawStats.cost_usd.toFixed(4)}`}
          chunkedDisplay={`$${chunkedStats.cost_usd.toFixed(4)}`}
        />
      </div>
    </div>
  );
}
