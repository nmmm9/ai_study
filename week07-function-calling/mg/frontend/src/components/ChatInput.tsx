"use client";

import { useState, useRef, useEffect } from "react";

interface Props {
  onSend: (message: string) => void;
  onStop: () => void;
  isStreaming: boolean;
}

export default function ChatInput({ onSend, onStop, isStreaming }: Props) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + "px";
    }
  }, [input]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setInput("");
  };

  return (
    <div className="border-t border-stroke/30">
      <div className="mx-auto max-w-3xl px-6 py-4">
        <div className="relative flex items-end rounded-2xl border border-stroke/50 bg-base-50/50 transition-all focus-within:border-pearl-muted/30">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder="무엇이든 물어보세요... 택배, 날씨, 야구, 맛집, 로또"
            rows={1}
            className="flex-1 resize-none bg-transparent px-5 py-3.5 text-[14px] text-pearl placeholder:text-pearl-muted/30 focus:outline-none"
          />
          {isStreaming ? (
            <button onClick={onStop} className="m-2.5 rounded-lg px-3 py-1.5 text-[11px] font-medium text-bad/80 hover:bg-bad/10">
              중지
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!input.trim()}
              className="m-2.5 rounded-lg px-3 py-1.5 text-[11px] font-medium text-gold/70 hover:bg-gold/10 disabled:opacity-0"
            >
              전송
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
