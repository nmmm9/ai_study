import type { ModelInfo } from "@/types/chat";

interface ModelSelectorProps {
  models: ModelInfo[];
  selected: string;
  onChange: (model: string) => void;
  disabled: boolean;
}

export default function ModelSelector({
  models,
  selected,
  onChange,
  disabled,
}: ModelSelectorProps) {
  return (
    <div className="relative">
      <select
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="appearance-none rounded-xl border border-stroke bg-base-50 px-3.5 py-1.5 pr-8 text-xs tracking-wide text-pearl-dim transition-all hover:border-stroke-hover hover:text-pearl focus:border-gold-dim focus:outline-none disabled:cursor-not-allowed disabled:opacity-25"
      >
        {models.length === 0 && <option value={selected}>{selected}</option>}
        {models.map((m) => (
          <option key={m.id} value={m.id}>
            {m.name}
          </option>
        ))}
      </select>
      <svg
        className="pointer-events-none absolute right-2.5 top-1/2 h-3 w-3 -translate-y-1/2 text-pearl-muted"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M19.5 8.25l-7.5 7.5-7.5-7.5"
        />
      </svg>
    </div>
  );
}
