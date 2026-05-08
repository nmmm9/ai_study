import type { TokenUsage } from "@/types/chat";

interface TokenBadgeProps {
  usage: TokenUsage;
}

export default function TokenBadge({ usage }: TokenBadgeProps) {
  return (
    <div className="mt-3 flex items-center gap-3 border-t border-stroke/40 pt-2 text-[10px] tracking-wide">
      <span className="text-pearl-muted">
        입력 <span className="text-pearl-dim">{usage.prompt_tokens}</span>
      </span>
      <span className="text-pearl-muted/30">·</span>
      <span className="text-pearl-muted">
        출력 <span className="text-pearl-dim">{usage.completion_tokens}</span>
      </span>
      <span className="text-pearl-muted/30">·</span>
      <span className="text-gold/40">
        합계{" "}
        <span className="font-medium text-gold/60">{usage.total_tokens}</span>
      </span>
    </div>
  );
}
