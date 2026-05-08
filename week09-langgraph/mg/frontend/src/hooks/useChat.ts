"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import type { ChatMessage, AgentTrace, AgentNode, ToolTrace } from "@/types/chat";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const ACTIVE_THREAD_KEY = "k-agent:active-thread";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function newThreadId() {
  return `t-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
}

const KNOWN_NODES: AgentNode[] = [
  "supervisor", "shopping", "lifestyle", "sports",
  "news", "finance", "government", "education", "info", "writer",
];

export interface GraphLiveState {
  active: Set<AgentNode>;
  done: Set<AgentNode>;
  activeEdge: { from: string; to: string } | null;
  plan: string[];
}

export interface SessionInfo {
  thread_id: string;
  title: string;
  message_count: number;
}

const emptyGraphState = (): GraphLiveState => ({
  active: new Set(),
  done: new Set(),
  activeEdge: null,
  plan: [],
});

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [model, setModel] = useState("auto");
  const [graphState, setGraphState] = useState<GraphLiveState>(emptyGraphState());
  const [threadId, setThreadId] = useState<string>("");
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const threadRef = useRef<string>("");

  // Initialize thread_id from localStorage on mount
  useEffect(() => {
    const stored = typeof window !== "undefined"
      ? localStorage.getItem(ACTIVE_THREAD_KEY)
      : null;
    const tid = stored || newThreadId();
    setThreadId(tid);
    threadRef.current = tid;
    if (!stored && typeof window !== "undefined") {
      localStorage.setItem(ACTIVE_THREAD_KEY, tid);
    }
  }, []);

  // Refresh sessions list
  const refreshSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/sessions`);
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  // Load history when switching to a different thread
  const loadThread = useCallback(async (tid: string) => {
    setThreadId(tid);
    threadRef.current = tid;
    if (typeof window !== "undefined") {
      localStorage.setItem(ACTIVE_THREAD_KEY, tid);
    }
    try {
      const res = await fetch(`${API}/api/sessions/${encodeURIComponent(tid)}`);
      if (res.ok) {
        const data = await res.json();
        const msgs: ChatMessage[] = (data.messages || []).map((m: { role: string; content: string }) => ({
          id: uid(),
          role: m.role as "user" | "assistant",
          content: m.content,
        }));
        setMessages(msgs);
      } else {
        setMessages([]);
      }
    } catch {
      setMessages([]);
    }
    setGraphState(emptyGraphState());
  }, []);

  const newChat = useCallback(() => {
    const tid = newThreadId();
    setThreadId(tid);
    threadRef.current = tid;
    if (typeof window !== "undefined") {
      localStorage.setItem(ACTIVE_THREAD_KEY, tid);
    }
    setMessages([]);
    setGraphState(emptyGraphState());
  }, []);

  const deleteSession = useCallback(async (tid: string) => {
    try {
      await fetch(`${API}/api/sessions/${encodeURIComponent(tid)}`, { method: "DELETE" });
      await refreshSessions();
      if (tid === threadRef.current) newChat();
    } catch { /* ignore */ }
  }, [newChat, refreshSessions]);

  const sendMessage = useCallback(async (content: string) => {
    if (isStreaming) return;
    const currentThread = threadRef.current;

    const userMsg: ChatMessage = { id: uid(), role: "user", content };
    const aId = uid();
    const assistantMsg: ChatMessage = {
      id: aId, role: "assistant", content: "",
      traces: [], plan: [], reasoning: "", isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);
    setGraphState(emptyGraphState());

    const controller = new AbortController();
    abortRef.current = controller;

    let traces: AgentTrace[] = [];
    let plan: string[] = [];
    let reasoning = "";
    let fullContent = "";
    const liveState: GraphLiveState = emptyGraphState();

    const upsertTrace = (node: AgentNode, patch: Partial<AgentTrace>) => {
      const idx = traces.findIndex((t) => t.node === node);
      if (idx === -1) {
        traces = [...traces, { node, status: "idle", tools: [], ...patch }];
      } else {
        traces = traces.map((t, i) => (i === idx ? { ...t, ...patch } : t));
      }
    };

    const flush = () => {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aId
            ? { ...m, content: fullContent, traces, plan, reasoning }
            : m,
        ),
      );
      setGraphState({
        active: new Set(liveState.active),
        done: new Set(liveState.done),
        activeEdge: liveState.activeEdge,
        plan: [...liveState.plan],
      });
    };

    try {
      const res = await fetch(`${API}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: content,
          model,
          thread_id: currentThread,
        }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) throw new Error("Stream failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

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
            const d = event.data;

            if (event.type === "supervisor_decision") {
              plan = (d.plan || []) as string[];
              reasoning = (d.reasoning || "") as string;
              liveState.plan = plan;
            } else if (event.type === "node_start") {
              const node = d.node as AgentNode;
              if (KNOWN_NODES.includes(node)) {
                liveState.active.add(node);
                upsertTrace(node, { status: "active", startedAt: Date.now() });
              }
            } else if (event.type === "node_end") {
              const node = d.node as AgentNode;
              if (KNOWN_NODES.includes(node)) {
                liveState.active.delete(node);
                liveState.done.add(node);
                upsertTrace(node, {
                  status: "done",
                  endedAt: Date.now(),
                  summary: d.result_summary as string | undefined,
                });
              }
            } else if (event.type === "edge") {
              liveState.activeEdge = { from: d.from as string, to: d.to as string };
            } else if (event.type === "tool_call") {
              const tt: ToolTrace = {
                domain: d.domain as string,
                tool: d.tool as string,
                args: d.args as Record<string, unknown>,
              };
              const node = d.domain as AgentNode;
              const existing = traces.find((t) => t.node === node);
              upsertTrace(node, {
                tools: [...(existing?.tools || []), tt],
              });
            } else if (event.type === "tool_result") {
              const node = d.domain as AgentNode;
              const existing = traces.find((t) => t.node === node);
              if (existing) {
                const updatedTools = [...existing.tools];
                for (let i = updatedTools.length - 1; i >= 0; i--) {
                  if (updatedTools[i].tool === d.tool && !updatedTools[i].result) {
                    updatedTools[i] = { ...updatedTools[i], result: d.result as string };
                    break;
                  }
                }
                upsertTrace(node, { tools: updatedTools });
              }
            } else if (event.type === "token") {
              fullContent += d as string;
            } else if (event.type === "done") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === aId
                    ? { ...m, content: fullContent, traces, plan, reasoning, isStreaming: false }
                    : m,
                ),
              );
              setGraphState(emptyGraphState());
              // Refresh sessions sidebar
              refreshSessions();
              continue;
            }
            flush();
          } catch { /* ignore parse errors */ }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return;
      setMessages((prev) => prev.map((m) =>
        m.id === aId ? { ...m, content: "오류가 발생했습니다.", isStreaming: false } : m
      ));
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, [isStreaming, model, refreshSessions]);

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
    setGraphState(emptyGraphState());
  }, []);

  return {
    messages,
    isStreaming,
    model,
    setModel,
    sendMessage,
    stopStreaming,
    graphState,
    threadId,
    sessions,
    newChat,
    loadThread,
    deleteSession,
    refreshSessions,
  };
}
