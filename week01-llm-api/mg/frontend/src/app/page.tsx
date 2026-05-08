"use client";

import { useEffect } from "react";
import { useChat } from "@/hooks/useChat";
import ChatWindow from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";
import ModelSelector from "@/components/ModelSelector";

export default function Home() {
  const {
    messages,
    isStreaming,
    selectedModel,
    setSelectedModel,
    models,
    fetchModels,
    sendMessage,
    clearMessages,
  } = useChat();

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  return (
    <div className="relative flex h-screen flex-col overflow-hidden bg-base">
      {/* Warm ambient glow */}
      <div
        className="pointer-events-none absolute -top-60 left-1/2 h-[400px] w-[600px] -translate-x-1/2 rounded-full opacity-[0.04]"
        style={{
          background: "radial-gradient(ellipse, #C9A96E, transparent 70%)",
        }}
      />

      {/* Header */}
      <header className="glass relative z-10 flex items-center justify-between border-b border-stroke px-6 py-4">
        <h1 className="font-serif text-xl font-light tracking-wide text-pearl">
          LLM Chat
        </h1>
        <div className="flex items-center gap-3">
          <ModelSelector
            models={models}
            selected={selectedModel}
            onChange={setSelectedModel}
            disabled={isStreaming}
          />
          <button
            onClick={clearMessages}
            disabled={isStreaming || messages.length === 0}
            className="rounded-xl border border-stroke bg-transparent px-3.5 py-1.5 text-xs tracking-wide text-pearl-dim transition-all hover:border-stroke-hover hover:text-pearl disabled:cursor-not-allowed disabled:opacity-25"
          >
            초기화
          </button>
        </div>
      </header>

      {/* Chat Area */}
      <ChatWindow messages={messages} isStreaming={isStreaming} />

      {/* Input Area */}
      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  );
}
