"use client";

import { useState, useRef, useEffect } from "react";

interface Props {
  onSend: (message: string) => void;
  onStop: () => void;
  isStreaming: boolean;
}

export default function ChatInput({ onSend, onStop, isStreaming }: Props) {
  const [input, setInput] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = "auto";
      ref.current.style.height = Math.min(ref.current.scrollHeight, 160) + "px";
    }
  }, [input]);

  const submit = () => { const t = input.trim(); if (t) { onSend(t); setInput(""); } };

  return (
    <div className="border-t border-[#383840]/30">
      <div className="mx-auto max-w-3xl px-6 py-4">
        <div className="relative flex items-end rounded-2xl border border-[#383840]/50 bg-[#212127]/50 focus-within:border-[#7D7972]/30">
          <textarea
            ref={ref}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); submit(); } }}
            placeholder="무엇이든 물어보세요..."
            rows={1}
            className="flex-1 resize-none bg-transparent px-5 py-3.5 text-[14px] text-[#F2EFE9] placeholder:text-[#7D7972]/30 focus:outline-none"
          />
          {isStreaming ? (
            <button onClick={onStop} className="m-2.5 rounded-lg px-3 py-1.5 text-[11px] font-medium text-red-400/80 hover:bg-red-400/10">중지</button>
          ) : (
            <button onClick={submit} disabled={!input.trim()} className="m-2.5 rounded-lg px-3 py-1.5 text-[11px] font-medium text-[#D4B07A]/70 hover:bg-[#D4B07A]/10 disabled:opacity-0">전송</button>
          )}
        </div>
      </div>
    </div>
  );
}
