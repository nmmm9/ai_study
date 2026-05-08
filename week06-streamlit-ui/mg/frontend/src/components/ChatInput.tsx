"use client";

import { useState, useRef, useEffect } from "react";

interface Props {
  onSend: (message: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled: boolean;
}

export default function ChatInput({ onSend, onStop, isStreaming, disabled }: Props) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 160) + "px";
    }
  }, [input]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-stroke/30">
      <div className="mx-auto max-w-3xl px-6 py-4">
        <div className="relative flex items-end rounded-2xl border border-stroke/50 bg-base-50/50 transition-all focus-within:border-pearl-muted/30">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? "문서를 먼저 선택해주세요" : "메시지를 입력하세요..."}
            disabled={disabled}
            rows={1}
            className="flex-1 resize-none bg-transparent px-5 py-3.5 text-[14px] text-pearl placeholder:text-pearl-muted/30 focus:outline-none disabled:opacity-20"
          />
          {isStreaming ? (
            <button
              onClick={onStop}
              className="m-2.5 rounded-lg px-3 py-1.5 text-[11px] font-medium text-bad/80 transition-colors hover:bg-bad/10"
            >
              중지
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || disabled}
              className="m-2.5 rounded-lg px-3 py-1.5 text-[11px] font-medium text-gold/70 transition-colors hover:bg-gold/10 disabled:opacity-0"
            >
              전송
            </button>
          )}
        </div>
        <p className="mt-2.5 text-center text-[10px] tracking-wide text-pearl-muted/25">
          문서 기반 RAG 답변 — 문서에 없는 내용은 답변하지 않습니다
        </p>
      </div>
    </div>
  );
}
