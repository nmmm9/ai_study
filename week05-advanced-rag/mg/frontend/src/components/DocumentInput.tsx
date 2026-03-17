"use client";

import { useState } from "react";
import type { SampleInfo } from "@/types/rag";

interface Props {
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
}: Props) {
  const [tab, setTab] = useState<"sample" | "direct">("sample");

  return (
    <section className="animate-fade-in-up rounded-2xl border border-stroke bg-base-50 p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-medium tracking-wide text-pearl-dim">
          1. 문서 선택
        </h2>
        <div className="flex gap-1 rounded-lg bg-base-100 p-0.5">
          {(["sample", "direct"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              disabled={disabled}
              className={`rounded-md px-3 py-1 text-xs transition-all ${
                tab === t
                  ? "bg-base-200 text-pearl"
                  : "text-pearl-muted hover:text-pearl-dim"
              }`}
            >
              {t === "sample" ? "샘플" : "직접 입력"}
            </button>
          ))}
        </div>
      </div>

      {tab === "sample" ? (
        <div className="flex flex-wrap gap-2">
          {samples.map((s) => (
            <button
              key={s.id}
              onClick={() => onLoadSample(s.id)}
              disabled={disabled}
              className="rounded-xl border border-stroke bg-base-100 px-4 py-2.5 text-left transition-all hover:border-gold-dim hover:bg-base-200 disabled:opacity-30"
            >
              <span className="block text-sm font-medium text-pearl">
                {s.title}
              </span>
              <span className="text-xs text-pearl-muted">
                {s.length.toLocaleString()}자
              </span>
            </button>
          ))}
        </div>
      ) : (
        <textarea
          value={document}
          onChange={(e) => setDocument(e.target.value)}
          disabled={disabled}
          placeholder="문서 내용을 직접 입력하세요..."
          className="h-40 w-full resize-none rounded-xl border border-stroke bg-base-100 p-4 text-sm text-pearl placeholder-pearl-muted focus:border-gold-dim focus:outline-none disabled:opacity-30"
        />
      )}

      {document && (
        <p className="mt-3 text-xs text-pearl-muted">
          {document.length.toLocaleString()}자 로드됨
        </p>
      )}
    </section>
  );
}
