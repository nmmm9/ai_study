import type { SearchResult } from "@/types/vector";

interface StatsBarProps {
  memoryResult: SearchResult;
  vectordbResult: SearchResult;
}

function Bar({
  label,
  memoryValue,
  vectordbValue,
  memoryDisplay,
  vectordbDisplay,
}: {
  label: string;
  memoryValue: number;
  vectordbValue: number;
  memoryDisplay: string;
  vectordbDisplay: string;
}) {
  const max = Math.max(memoryValue, vectordbValue, 1);
  const memPct = (memoryValue / max) * 100;
  const vecPct = (vectordbValue / max) * 100;

  return (
    <div className="space-y-1.5">
      <p className="text-[10px] tracking-widest uppercase text-pearl-muted">
        {label}
      </p>
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span className="w-16 text-[10px] text-bad">Memory</span>
          <div className="relative h-5 flex-1 rounded-md bg-base-100">
            <div
              className="animate-bar-grow h-full rounded-md bg-bad/30"
              style={{ width: `${memPct}%` }}
            />
          </div>
          <span className="w-20 text-right text-xs text-bad">
            {memoryDisplay}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-16 text-[10px] text-good">VectorDB</span>
          <div className="relative h-5 flex-1 rounded-md bg-base-100">
            <div
              className="animate-bar-grow h-full rounded-md bg-good/30"
              style={{ width: `${vecPct}%` }}
            />
          </div>
          <span className="w-20 text-right text-xs font-medium text-good">
            {vectordbDisplay}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function StatsBar({
  memoryResult,
  vectordbResult,
}: StatsBarProps) {
  const speedup =
    vectordbResult.timing.total_ms > 0
      ? (memoryResult.timing.total_ms / vectordbResult.timing.total_ms).toFixed(
          1
        )
      : "—";

  return (
    <div className="animate-fade-in-up rounded-2xl border border-stroke bg-base-50 p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xs font-medium tracking-widest uppercase text-pearl-dim">
          비교 통계
        </h2>
        <span className="rounded-full bg-gold/10 px-3 py-0.5 text-sm font-semibold text-gold">
          {speedup}x 빠름
        </span>
      </div>
      <div className="grid grid-cols-3 gap-6">
        <Bar
          label="임베딩 시간"
          memoryValue={memoryResult.timing.embed_ms}
          vectordbValue={vectordbResult.timing.embed_ms}
          memoryDisplay={`${(memoryResult.timing.embed_ms / 1000).toFixed(1)}s`}
          vectordbDisplay={`${(vectordbResult.timing.embed_ms / 1000).toFixed(1)}s`}
        />
        <Bar
          label="총 시간"
          memoryValue={memoryResult.timing.total_ms}
          vectordbValue={vectordbResult.timing.total_ms}
          memoryDisplay={`${(memoryResult.timing.total_ms / 1000).toFixed(1)}s`}
          vectordbDisplay={`${(vectordbResult.timing.total_ms / 1000).toFixed(1)}s`}
        />
        <Bar
          label="비용"
          memoryValue={memoryResult.cost_usd}
          vectordbValue={vectordbResult.cost_usd}
          memoryDisplay={`$${memoryResult.cost_usd.toFixed(4)}`}
          vectordbDisplay={`$${vectordbResult.cost_usd.toFixed(4)}`}
        />
      </div>
    </div>
  );
}
