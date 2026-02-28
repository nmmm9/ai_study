"use client";

import { useState } from "react";
import type { SampleInfo } from "@/types/vector";

interface DocumentInputProps {
  document: string;
  setDocument: (doc: string) => void;
  samples: SampleInfo[];
  onLoadSample: (id: string) => void;
  disabled: boolean;
}

export default function DocumentInput({
  document,
  setDocument,
  samples,
  onLoadSample,
  disabled,
}: DocumentInputProps) {
  const [tab, setTab] = useState<"sample" | "direct">("sample");
  const [selectedSample, setSelectedSample] = useState<string | null>(null);

  const handleSelectSample = (id: string) => {
    setSelectedSample(id);
    onLoadSample(id);
  };

  return (
    <div className="animate-fade-in-up space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xs font-medium tracking-widest uppercase text-pearl-dim">
            문서 선택
          </h2>
          <div className="flex rounded-lg border border-stroke bg-base-100 p-0.5">
            <button
              onClick={() => setTab("sample")}
              className={`rounded-md px-3 py-1 text-[11px] transition-all ${
                tab === "sample"
                  ? "bg-base-50 text-pearl"
                  : "text-pearl-muted hover:text-pearl-dim"
              }`}
            >
              샘플 선택
            </button>
            <button
              onClick={() => setTab("direct")}
              className={`rounded-md px-3 py-1 text-[11px] transition-all ${
                tab === "direct"
                  ? "bg-base-50 text-pearl"
                  : "text-pearl-muted hover:text-pearl-dim"
              }`}
            >
              직접 입력
            </button>
          </div>
        </div>
        <span className="text-[10px] text-pearl-muted">
          {document.length.toLocaleString()}자
        </span>
      </div>

      {tab === "sample" ? (
        <div className="flex gap-2">
          {samples.map((s) => (
            <button
              key={s.id}
              onClick={() => handleSelectSample(s.id)}
              disabled={disabled}
              className={`rounded-lg border px-3 py-1.5 text-xs transition-all disabled:opacity-30 ${
                selectedSample === s.id
                  ? "border-gold/40 bg-gold/10 text-gold"
                  : "border-stroke bg-base-50 text-pearl-dim hover:border-gold/30 hover:text-pearl"
              }`}
            >
              {s.title}
              <span className="ml-1.5 text-pearl-muted">
                ({(s.length / 1000).toFixed(1)}k)
              </span>
            </button>
          ))}
        </div>
      ) : (
        <textarea
          value={document}
          onChange={(e) => setDocument(e.target.value)}
          disabled={disabled}
          placeholder="문서를 붙여넣으세요..."
          rows={6}
          className="w-full resize-none rounded-xl border border-stroke bg-base-50 px-4 py-3 text-sm text-pearl placeholder:text-pearl-muted focus:border-gold-dim/50 focus:outline-none disabled:opacity-40"
        />
      )}

      {tab === "sample" && document && (
        <div className="max-h-40 overflow-y-auto rounded-xl border border-stroke bg-base-50 px-4 py-3">
          <p className="line-clamp-6 whitespace-pre-wrap text-xs leading-relaxed text-pearl-dim">
            {document}
          </p>
        </div>
      )}
    </div>
  );
}
