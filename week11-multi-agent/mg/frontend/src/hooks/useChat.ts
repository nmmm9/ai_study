"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import type {
  ChatMessage, AgentTrace, AgentNode, ToolTrace, CriticReport,
  PlanStep, ReplanRecord, StepStatus,
} from "@/types/chat";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const ACTIVE_THREAD_KEY = "k-agent:active-thread";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function newThreadId() {
  return `t-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
}

const KNOWN_NODES: AgentNode[] = [
  "supervisor", "planner", "executor", "replanner",
  "shopping", "lifestyle", "sports",
  "news", "finance", "government", "education", "info", "writer", "critic",
];

export interface GraphLiveState {
  active: Set<AgentNode>;
  done: Set<AgentNode>;
  activeEdge: { from: string; to: string } | null;
  plan: PlanStep[];
  currentStepId: number | null;
  iteration: number;
  lastScore: number | null;
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
  currentStepId: null,
  iteration: 0,
  lastScore: null,
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
      traces: [], plan: [], planReasoning: "", replans: [],
      reasoning: "", isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);
    setGraphState(emptyGraphState());

    const controller = new AbortController();
    abortRef.current = controller;

    let traces: AgentTrace[] = [];
    let plan: PlanStep[] = [];
    let planReasoning = "";
    let replans: ReplanRecord[] = [];
    let currentStepId: number | null = null;
    let fullContent = "";
    let critiques: CriticReport[] = [];
    let iterations = 0;
    let finalScore: number | null = null;
    const liveState: GraphLiveState = emptyGraphState();

    const upsertTrace = (node: AgentNode, patch: Partial<AgentTrace>) => {
      const idx = traces.findIndex((t) => t.node === node);
      if (idx === -1) {
        traces = [...traces, { node, status: "idle", tools: [], ...patch }];
      } else {
        traces = traces.map((t, i) => (i === idx ? { ...t, ...patch } : t));
      }
    };

    const updateStep = (stepId: number, patch: Partial<PlanStep>) => {
      plan = plan.map((s) => (s.id === stepId ? { ...s, ...patch } : s));
    };

    const flush = () => {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aId
            ? {
                ...m,
                content: fullContent,
                traces,
                plan: [...plan],
                planReasoning,
                replans: [...replans],
                critiques: [...critiques],
                iterations,
                finalScore: finalScore ?? undefined,
              }
            : m,
        ),
      );
      setGraphState({
        active: new Set(liveState.active),
        done: new Set(liveState.done),
        activeEdge: liveState.activeEdge,
        plan: [...plan],
        currentStepId,
        iteration: liveState.iteration,
        lastScore: liveState.lastScore,
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

            if (event.type === "plan_created") {
              const rawSteps = (d.plan || []) as Array<{ id: number; domain: string | null; task: string }>;
              plan = rawSteps.map((s) => ({
                id: s.id,
                domain: s.domain,
                task: s.task,
                status: "pending" as StepStatus,
              }));
              planReasoning = (d.reasoning || "") as string;
            } else if (event.type === "step_start") {
              const s = d.step as { id: number };
              currentStepId = s.id;
              updateStep(s.id, { status: "active" });
            } else if (event.type === "step_done") {
              const s = d.step as { id: number; tool_count?: number; results_summary?: string };
              updateStep(s.id, {
                status: "done",
                tool_count: s.tool_count,
                results_summary: s.results_summary,
              });
              currentStepId = null;
            } else if (event.type === "replan_decision") {
              const dd = d as { action: ReplanRecord["action"]; reasoning: string; new_plan?: PlanStep[] };
              const lastStepId = currentStepId ?? (plan.length ? plan[plan.length - 1].id : 0);
              replans = [...replans, {
                step_id: lastStepId,
                action: dd.action,
                reasoning: dd.reasoning,
                new_plan: dd.new_plan,
              }];
              // If revise, append new_plan to plan
              if (dd.action === "revise" && dd.new_plan && dd.new_plan.length > 0) {
                plan = [
                  ...plan,
                  ...dd.new_plan.map((s) => ({
                    id: s.id,
                    domain: s.domain,
                    task: s.task,
                    status: "pending" as StepStatus,
                  })),
                ];
              }
              // If finish, mark remaining pending as skipped
              if (dd.action === "finish") {
                plan = plan.map((s) =>
                  s.status === "pending" ? { ...s, status: "skipped" as StepStatus } : s,
                );
              }
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
            } else if (event.type === "writer_iteration") {
              const iter = (d.iteration as number) || 1;
              const isRev = (d.is_revision as boolean) || false;
              iterations = iter;
              liveState.iteration = iter;
              if (isRev) fullContent = "";
            } else if (event.type === "revision_start") {
              fullContent = "";
            } else if (event.type === "critic_score") {
              const report = d as unknown as CriticReport;
              critiques = [...critiques, report];
              liveState.lastScore = report.score;
              finalScore = report.score;
            } else if (event.type === "token") {
              fullContent += d as string;
            } else if (event.type === "done") {
              const finished = d as { final_score?: number; iterations?: number } | null;
              if (finished?.final_score) finalScore = finished.final_score;
              if (finished?.iterations) iterations = finished.iterations;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === aId
                    ? {
                        ...m,
                        content: fullContent,
                        traces,
                        plan: [...plan],
                        planReasoning,
                        replans: [...replans],
                        critiques: [...critiques],
                        iterations,
                        finalScore: finalScore ?? undefined,
                        isStreaming: false,
                      }
                    : m,
                ),
              );
              setGraphState(emptyGraphState());
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
