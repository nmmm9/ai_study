"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { DocumentInfo } from "@/types/chat";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DocumentPanel() {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/documents`);
      if (res.ok) {
        const data = await res.json();
        setDocs(data.documents || []);
      }
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const onUpload = async (file: File) => {
    setError(null);
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fetch(`${API}/api/documents/upload`, {
        method: "POST",
        body: fd,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || `업로드 실패 (${res.status})`);
      } else {
        await refresh();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "업로드 실패");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  const onDelete = async (docId: string) => {
    try {
      await fetch(`${API}/api/documents/${encodeURIComponent(docId)}`, {
        method: "DELETE",
      });
      await refresh();
    } catch { /* ignore */ }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-stroke/30 px-4 py-3">
        <h2 className="text-[12px] font-semibold uppercase tracking-[0.2em] text-pearl-muted/60">
          Documents
        </h2>
        <p className="text-[10px] text-pearl-muted/40 mt-1">
          PDF / TXT / MD 업로드 → 벡터 인덱스
        </p>
      </div>

      <div className="px-4 py-3 border-b border-stroke/20">
        <label className="block">
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.txt,.md,.markdown"
            disabled={uploading}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onUpload(f);
            }}
            className="hidden"
          />
          <span
            onClick={() => !uploading && inputRef.current?.click()}
            className={`block w-full rounded-lg border border-dashed border-stroke/60 px-3 py-3 text-center text-[11px] transition-colors ${
              uploading
                ? "text-pearl-muted/40 cursor-not-allowed"
                : "text-pearl-dim cursor-pointer hover:border-gold/40 hover:text-pearl"
            }`}
          >
            {uploading ? "업로드 중..." : "+ 파일 선택"}
          </span>
        </label>
        {error && (
          <p className="mt-2 text-[10px] text-red-400">{error}</p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2">
        {docs.length === 0 ? (
          <p className="text-center text-[11px] text-pearl-muted/40 mt-6">
            업로드된 문서 없음
          </p>
        ) : (
          <ul className="space-y-1">
            {docs.map((d) => (
              <li
                key={d.doc_id}
                className="group flex items-center gap-2 rounded-lg px-2 py-2 hover:bg-base-200/40"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-[12px] text-pearl-dim truncate" title={d.doc_name}>
                    {d.doc_name}
                  </p>
                  <p className="text-[10px] text-pearl-muted/50">
                    {d.chunks} chunks
                  </p>
                </div>
                <button
                  onClick={() => onDelete(d.doc_id)}
                  className="opacity-0 group-hover:opacity-100 text-[10px] text-red-400/70 hover:text-red-400 px-1.5 py-0.5"
                  title="삭제"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
