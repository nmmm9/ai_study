"use client";

import { useState, useCallback } from "react";

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSubmit = useCallback(() => {
    if (!input.trim() || disabled) return;
    onSend(input);
    setInput("");
  }, [input, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="glass relative z-10 border-t border-stroke px-4 py-4">
      <div className="focus-glow mx-auto flex max-w-3xl items-end gap-3 rounded-2xl border border-stroke bg-base-50 p-2 transition-all">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="메시지를 입력하세요..."
          rows={1}
          disabled={disabled}
          className="flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-pearl placeholder:text-pearl-muted focus:outline-none disabled:cursor-not-allowed disabled:opacity-40"
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !input.trim()}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gold text-base transition-all hover:bg-gold-dim disabled:cursor-not-allowed disabled:opacity-25"
        >
          {disabled ? (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-base/30 border-t-base" />
          ) : (
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18"
              />
            </svg>
          )}
        </button>
      </div>
      <p className="mt-2.5 text-center text-[10px] tracking-widest text-pearl-muted">
        ENTER 전송 · SHIFT+ENTER 줄바꿈
      </p>
    </div>
  );
}
