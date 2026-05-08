"use client";

import { useState, useCallback } from "react";
import type { ChatSession, SampleInfo } from "@/types/chat";

interface Props {
  sessions: ChatSession[];
  activeSession: ChatSession;
  samples: SampleInfo[];
  model: string;
  isUploading: boolean;
  onNewSession: () => void;
  onSwitchSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  onUploadFile: (file: File) => void;
  onAddSample: (id: string) => void;
  onSetModel: (model: string) => void;
}

export default function Sidebar({
  sessions, activeSession, samples, model, isUploading,
  onNewSession, onSwitchSession, onDeleteSession,
  onUploadFile, onAddSample, onSetModel,
}: Props) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) onUploadFile(file);
  }, [onUploadFile]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onUploadFile(file);
    e.target.value = "";
  }, [onUploadFile]);

  return (
    <aside className="flex h-screen w-[280px] flex-col border-r border-stroke/50 bg-base-50">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-5">
        <h1 className="text-[15px] font-semibold tracking-tight text-pearl">RAG Chat</h1>
        <button
          onClick={onNewSession}
          className="rounded-md px-2.5 py-1 text-[11px] text-pearl-muted transition-colors hover:bg-base-200 hover:text-pearl-dim"
        >
          새 채팅
        </button>
      </div>

      <div className="mx-5 h-px bg-stroke/40" />

      {/* Session list */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-3 py-3 space-y-0.5">
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`group flex items-center rounded-lg px-3 py-2.5 transition-all cursor-pointer ${
                s.id === activeSession.id
                  ? "bg-base-200/80"
                  : "hover:bg-base-200/40"
              }`}
              onClick={() => onSwitchSession(s.id)}
            >
              <div className="flex-1 min-w-0">
                <p className={`text-[13px] truncate ${
                  s.id === activeSession.id ? "text-pearl" : "text-pearl-dim"
                }`}>
                  {s.name}
                </p>
                <p className="text-[10px] text-pearl-muted/40">
                  {s.fileNames.length}개 문서 · {s.messages.length}개 메시지
                </p>
              </div>
              {sessions.length > 1 && (
                <button
                  onClick={(e) => { e.stopPropagation(); onDeleteSession(s.id); }}
                  className="text-[10px] text-pearl-muted/20 opacity-0 group-hover:opacity-100 transition-all hover:text-bad ml-2"
                >
                  삭제
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="mx-5 h-px bg-stroke/40" />

      {/* Current session: attached files */}
      <div className="px-5 py-3">
        <p className="mb-2 text-[10px] font-medium uppercase tracking-[0.15em] text-pearl-muted/50">
          현재 세션 문서 ({activeSession.fileNames.length})
        </p>
        <div className="space-y-1 mb-3 max-h-24 overflow-y-auto">
          {activeSession.fileNames.map((name, i) => (
            <p key={i} className="text-[11px] text-pearl-dim/70 truncate">
              {name}
            </p>
          ))}
        </div>

        {/* File drop zone */}
        <label
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          className={`flex cursor-pointer flex-col items-center rounded-xl border-2 border-dashed px-3 py-3 transition-all ${
            isDragOver ? "border-gold/50 bg-gold/5"
              : isUploading ? "border-stroke/40 opacity-60"
              : "border-stroke/30 hover:border-stroke/60"
          }`}
        >
          <p className="text-[11px] text-pearl-muted">
            {isUploading ? "업로드 중..." : "파일 추가 (드래그 또는 클릭)"}
          </p>
          <p className="text-[9px] text-pearl-muted/40">.txt .md .pdf .csv</p>
          <input type="file" accept=".txt,.md,.pdf,.csv" onChange={handleFileSelect} disabled={isUploading} className="hidden" />
        </label>

        {/* Add sample */}
        {samples.length > 0 && (
          <div className="mt-2">
            <select
              onChange={(e) => { if (e.target.value) { onAddSample(e.target.value); e.target.value = ""; } }}
              className="w-full appearance-none rounded-lg bg-base-200/30 px-3 py-1.5 text-[11px] text-pearl-muted focus:outline-none"
              defaultValue=""
            >
              <option value="" disabled>샘플 문서 추가...</option>
              {samples.map((s) => (
                <option key={s.id} value={s.id}>{s.title}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="mx-5 h-px bg-stroke/40" />

      {/* Model */}
      <div className="px-5 py-3">
        <select
          value={model}
          onChange={(e) => onSetModel(e.target.value)}
          className="w-full appearance-none rounded-lg bg-base-200/40 px-3 py-2 text-[12px] text-pearl-dim focus:outline-none focus:ring-1 focus:ring-gold/30"
        >
          <option value="gpt-4o-mini">GPT-4o Mini</option>
          <option value="gpt-4o">GPT-4o</option>
        </select>
      </div>
    </aside>
  );
}
