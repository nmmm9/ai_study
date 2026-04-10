"use client";

import { useState, useCallback, useRef } from "react";
import type { ChatMessage, ToolCall, ToolResult } from "@/types/chat";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [model, setModel] = useState("gpt-4o-mini");
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (isStreaming) return;

    const userMsg: ChatMessage = { id: uid(), role: "user", content };
    const assistantMsgId = uid();
    const assistantMsg: ChatMessage = {
      id: assistantMsgId, role: "assistant", content: "",
      toolCalls: [], toolResults: [], isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);

    const history = messages.slice(-10).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(`${API}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: content, model, history }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) throw new Error("Stream failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let fullContent = "";
      let toolCalls: ToolCall[] = [];
      let toolResults: ToolResult[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const event = JSON.parse(jsonStr);
            if (event.type === "tool_call") {
              toolCalls = [...toolCalls, event.data];
              setMessages((prev) => prev.map((m) =>
                m.id === assistantMsgId ? { ...m, toolCalls } : m
              ));
            } else if (event.type === "tool_result") {
              toolResults = [...toolResults, event.data];
              setMessages((prev) => prev.map((m) =>
                m.id === assistantMsgId ? { ...m, toolResults } : m
              ));
            } else if (event.type === "token") {
              fullContent += event.data;
              setMessages((prev) => prev.map((m) =>
                m.id === assistantMsgId ? { ...m, content: fullContent } : m
              ));
            } else if (event.type === "done") {
              setMessages((prev) => prev.map((m) =>
                m.id === assistantMsgId ? { ...m, content: fullContent, isStreaming: false } : m
              ));
            }
          } catch { /* ignore */ }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return;
      setMessages((prev) => prev.map((m) =>
        m.id === assistantMsgId ? { ...m, content: "오류가 발생했습니다.", isStreaming: false } : m
      ));
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, [isStreaming, messages, model]);

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, isStreaming, model, setModel, sendMessage, stopStreaming, clearChat };
}
