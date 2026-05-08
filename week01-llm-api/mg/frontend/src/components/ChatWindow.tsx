"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/types/chat";
import ChatBubble from "./ChatBubble";

interface ChatWindowProps {
  messages: ChatMessage[];
  isStreaming: boolean;
}

export default function ChatWindow({ messages, isStreaming }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto">
      {messages.length === 0 ? (
        <div className="flex h-full flex-col items-center justify-center gap-8">
          {/* Golden orb */}
          <div className="relative flex h-20 w-20 items-center justify-center">
            <div className="animate-breathe absolute inset-0 rounded-full bg-gold/20 blur-2xl" />
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-gold/70 to-gold-dim/50" />
          </div>
          <div className="text-center">
            <p className="font-serif text-2xl font-light tracking-wide text-pearl/70">
              대화를 시작해보세요
            </p>
            <p className="mt-3 text-xs tracking-wide text-pearl-muted">
              모델을 선택하고 메시지를 입력하세요
            </p>
          </div>
        </div>
      ) : (
        <div className="mx-auto flex max-w-3xl flex-col gap-2 px-4 py-8">
          {messages.map((msg, idx) => (
            <ChatBubble
              key={msg.id}
              message={msg}
              isStreaming={
                isStreaming &&
                idx === messages.length - 1 &&
                msg.role === "assistant"
              }
            />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
