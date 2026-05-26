"use client";

import type { SessionInfo } from "@/hooks/useChat";

interface Props {
  sessions: SessionInfo[];
  activeThreadId: string;
  onSelect: (tid: string) => void;
  onNew: () => void;
  onDelete: (tid: string) => void;
}

export default function SessionSidebar({
  sessions, activeThreadId, onSelect, onNew, onDelete,
}: Props) {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-stroke/30 px-4 py-3">
        <button
          onClick={onNew}
          className="w-full rounded-lg border border-stroke/50 bg-base-50/40 px-3 py-2 text-[12px] text-pearl-dim hover:border-gold/40 hover:text-pearl transition-colors"
        >
          + 새 채팅
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-2">
        <p className="px-2 mb-1 text-[10px] uppercase tracking-[0.2em] text-pearl-muted/40">
          세션 ({sessions.length})
        </p>
        {sessions.length === 0 ? (
          <p className="px-2 py-3 text-[11px] text-pearl-muted/40">
            아직 대화가 없습니다.
          </p>
        ) : (
          <ul className="space-y-0.5">
            {sessions.map((s) => {
              const isActive = s.thread_id === activeThreadId;
              return (
                <li key={s.thread_id}>
                  <div
                    className={`group flex items-center gap-1 rounded-md px-2 py-1.5 transition-colors ${
                      isActive
                        ? "bg-gold/10 border border-gold/30"
                        : "border border-transparent hover:bg-base-200/40"
                    }`}
                  >
                    <button
                      onClick={() => onSelect(s.thread_id)}
                      className="flex-1 min-w-0 text-left"
                    >
                      <p className={`truncate text-[12px] ${isActive ? "text-pearl" : "text-pearl-dim/80"}`}>
                        {s.title}
                      </p>
                      <p className="text-[10px] text-pearl-muted/40 mt-0.5">
                        {s.message_count}개 메시지
                      </p>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm("이 세션을 삭제할까요?")) onDelete(s.thread_id);
                      }}
                      className="opacity-0 group-hover:opacity-100 px-1.5 text-[14px] text-pearl-muted/40 hover:text-red-400 transition-opacity"
                      title="삭제"
                    >
                      ×
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div className="border-t border-stroke/30 px-4 py-2.5">
        <p className="text-[9px] uppercase tracking-[0.2em] text-pearl-muted/30">
          LangGraph Checkpointer
        </p>
        <p className="text-[10px] text-pearl-muted/50 mt-0.5">
          InMemorySaver — 서버 재시작 시 초기화
        </p>
      </div>
    </div>
  );
}
