"use client";

import { useState, useCallback, useRef, useMemo, useEffect } from "react";
import type { ChatMessage, ChatSession, SampleInfo } from "@/types/chat";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DEFAULT_COLLECTION = "startup-guide-500-50";
const STORAGE_KEY = "rag-chat-sessions";
const ACTIVE_KEY = "rag-chat-active";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function createSession(name: string = "새 채팅"): ChatSession {
  return {
    id: uid(),
    name,
    messages: [],
    collections: [DEFAULT_COLLECTION],
    fileNames: ["스타트업 창업 가이드"],
    createdAt: Date.now(),
  };
}

export function useChat() {
  const [sessions, setSessions] = useState<ChatSession[]>(() => [createSession()]);
  const [activeSessionId, setActiveSessionId] = useState(() => sessions[0]?.id ?? "");
  const [hydrated, setHydrated] = useState(false);

  // Load from localStorage AFTER hydration (client only)
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as ChatSession[];
        if (parsed.length > 0) {
          const cleaned = parsed.map((s) => ({
            ...s,
            messages: s.messages.map((m) => ({ ...m, isStreaming: false })),
          }));
          setSessions(cleaned);

          const savedId = localStorage.getItem(ACTIVE_KEY);
          if (savedId && cleaned.find((s) => s.id === savedId)) {
            setActiveSessionId(savedId);
          } else {
            setActiveSessionId(cleaned[0].id);
          }
        }
      }
    } catch { /* ignore */ }
    setHydrated(true);
  }, []);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [samples, setSamples] = useState<SampleInfo[]>([]);
  const [model, setModel] = useState("gpt-4o-mini");
  const abortRef = useRef<AbortController | null>(null);

  // Persist to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    } catch { /* ignore */ }
  }, [sessions]);

  useEffect(() => {
    try {
      localStorage.setItem(ACTIVE_KEY, activeSessionId);
    } catch { /* ignore */ }
  }, [activeSessionId]);

  // Stable ref for activeSessionId (avoid stale closures)
  const activeIdRef = useRef(activeSessionId);
  activeIdRef.current = activeSessionId;

  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeSessionId) ?? sessions[0],
    [sessions, activeSessionId]
  );

  // ─── Session management ───

  const newSession = useCallback(() => {
    const s = createSession();
    setSessions((prev) => [s, ...prev]);
    setActiveSessionId(s.id);
  }, []);

  const switchSession = useCallback((id: string) => {
    setActiveSessionId(id);
  }, []);

  const deleteSession = useCallback((id: string) => {
    setSessions((prev) => {
      const next = prev.filter((s) => s.id !== id);
      if (next.length === 0) next.push(createSession());
      return next;
    });
    setActiveSessionId((prevId) => {
      if (prevId === id) {
        // Will be resolved on next render via sessions
        return "";
      }
      return prevId;
    });
  }, []);

  // Fix: if activeSessionId points to nothing, reset to first session
  if (activeSessionId && !sessions.find((s) => s.id === activeSessionId) && sessions.length > 0) {
    setActiveSessionId(sessions[0].id);
  }

  const updateSession = useCallback((id: string, updater: (s: ChatSession) => ChatSession) => {
    setSessions((prev) => prev.map((s) => (s.id === id ? updater(s) : s)));
  }, []);

  // ─── Samples ───

  const fetchSamples = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/samples`);
      const data = await res.json();
      setSamples(data.samples);
    } catch { /* ignore */ }
  }, []);

  const initDefault = useCallback(async () => {
    try {
      await fetch(`${API}/api/default`);
    } catch { /* ignore */ }
  }, []);

  // ─── File upload (add to current session) ───

  const uploadFile = useCallback(async (file: File) => {
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API}/api/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();

      const id = activeIdRef.current;
      updateSession(id, (s) => ({
        ...s,
        collections: [...new Set([...s.collections, data.collection_name])],
        fileNames: [...s.fileNames, file.name],
      }));
    } catch { /* ignore */ }
    finally { setIsUploading(false); }
  }, [updateSession]);

  const addSampleToSession = useCallback(async (sampleId: string) => {
    try {
      const res = await fetch(`${API}/api/samples/${sampleId}`);
      const data = await res.json();

      const embedRes = await fetch(`${API}/api/embed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document: data.content }),
      });
      const embedData = await embedRes.json();

      const id = activeIdRef.current;
      updateSession(id, (s) => ({
        ...s,
        collections: [...new Set([...s.collections, embedData.collection_name])],
        fileNames: [...s.fileNames, data.title],
      }));
    } catch { /* ignore */ }
  }, [updateSession]);

  // ─── Chat ───

  const sendMessage = useCallback(async (content: string) => {
    if (isStreaming) return;

    const sessionId = activeIdRef.current;

    // Get current session from state
    let currentSession: ChatSession | undefined;
    setSessions((prev) => {
      currentSession = prev.find((s) => s.id === sessionId);
      return prev; // no mutation, just reading
    });

    if (!currentSession || currentSession.collections.length === 0) return;

    const userMsg: ChatMessage = { id: uid(), role: "user", content };
    const assistantMsgId = uid();
    const assistantMsg: ChatMessage = {
      id: assistantMsgId, role: "assistant", content: "", isStreaming: true,
    };

    // Add messages + update name
    updateSession(sessionId, (s) => ({
      ...s,
      name: s.messages.length === 0 ? content.slice(0, 30) : s.name,
      messages: [...s.messages, userMsg, assistantMsg],
    }));

    setIsStreaming(true);

    const history = currentSession.messages.slice(-10).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(`${API}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: content,
          collection_names: currentSession.collections,
          model,
          history,
        }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) throw new Error("Stream failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let fullContent = "";
      let sources: ChatMessage["sources"] = undefined;
      let thinking: ChatMessage["thinking"] = [];

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
            if (event.type === "thinking") {
              thinking = [...(thinking || []), event.data];
              updateSession(sessionId, (s) => ({
                ...s,
                messages: s.messages.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, thinking }
                    : m
                ),
              }));
            } else if (event.type === "sources") {
              sources = event.data;
            } else if (event.type === "token") {
              fullContent += event.data;
              updateSession(sessionId, (s) => ({
                ...s,
                messages: s.messages.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, content: fullContent, sources, thinking }
                    : m
                ),
              }));
            } else if (event.type === "done") {
              updateSession(sessionId, (s) => ({
                ...s,
                messages: s.messages.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, content: fullContent, sources, thinking, isStreaming: false }
                    : m
                ),
              }));
            }
          } catch { /* ignore parse errors */ }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === "AbortError") return;
      updateSession(sessionId, (s) => ({
        ...s,
        messages: s.messages.map((m) =>
          m.id === assistantMsgId
            ? { ...m, content: "오류가 발생했습니다.", isStreaming: false }
            : m
        ),
      }));
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, [isStreaming, model, updateSession]);

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  // Edit a user message: truncate everything after it, resend with new content
  const editMessage = useCallback((messageId: string, newContent: string) => {
    if (isStreaming) return;

    const sessionId = activeIdRef.current;

    // Truncate and get the remaining history in one step
    let truncatedHistory: { role: string; content: string }[] = [];
    let sessionCollections: string[] = [];

    setSessions((prev) => prev.map((s) => {
      if (s.id !== sessionId) return s;
      const idx = s.messages.findIndex((m) => m.id === messageId);
      if (idx === -1) return s;
      const kept = s.messages.slice(0, idx);
      truncatedHistory = kept.slice(-10).map((m) => ({ role: m.role, content: m.content }));
      sessionCollections = s.collections;
      return { ...s, messages: kept };
    }));

    // Use requestAnimationFrame to ensure state is committed before sending
    requestAnimationFrame(() => {
      // Directly create and send the new message
      const userMsg: ChatMessage = { id: uid(), role: "user", content: newContent };
      const assistantMsgId = uid();
      const assistantMsg: ChatMessage = {
        id: assistantMsgId, role: "assistant", content: "", isStreaming: true,
      };

      updateSession(sessionId, (s) => ({
        ...s,
        messages: [...s.messages, userMsg, assistantMsg],
      }));

      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;

      (async () => {
        try {
          const res = await fetch(`${API}/api/chat/stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              question: newContent,
              collection_names: sessionCollections,
              model,
              history: truncatedHistory,
            }),
            signal: controller.signal,
          });

          if (!res.ok || !res.body) throw new Error("Stream failed");

          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";
          let fullContent = "";
          let sources: ChatMessage["sources"] = undefined;
          let thinking: ChatMessage["thinking"] = [];

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
                if (event.type === "thinking") {
                  thinking = [...thinking, event.data];
                  updateSession(sessionId, (s) => ({
                    ...s,
                    messages: s.messages.map((m) =>
                      m.id === assistantMsgId ? { ...m, thinking } : m
                    ),
                  }));
                } else if (event.type === "sources") {
                  sources = event.data;
                } else if (event.type === "token") {
                  fullContent += event.data;
                  updateSession(sessionId, (s) => ({
                    ...s,
                    messages: s.messages.map((m) =>
                      m.id === assistantMsgId ? { ...m, content: fullContent, sources, thinking } : m
                    ),
                  }));
                } else if (event.type === "done") {
                  updateSession(sessionId, (s) => ({
                    ...s,
                    messages: s.messages.map((m) =>
                      m.id === assistantMsgId ? { ...m, content: fullContent, sources, thinking, isStreaming: false } : m
                    ),
                  }));
                }
              } catch { /* ignore */ }
            }
          }
        } catch (err: unknown) {
          if (err instanceof Error && err.name === "AbortError") return;
          updateSession(sessionId, (s) => ({
            ...s,
            messages: s.messages.map((m) =>
              m.id === assistantMsgId ? { ...m, content: "오류가 발생했습니다.", isStreaming: false } : m
            ),
          }));
        } finally {
          setIsStreaming(false);
          abortRef.current = null;
        }
      })();
    });
  }, [isStreaming, model, updateSession]);

  return {
    sessions, activeSession, isStreaming, isUploading, samples, model,
    setModel, fetchSamples, initDefault, newSession, switchSession,
    deleteSession, uploadFile, addSampleToSession, sendMessage, stopStreaming, editMessage,
  };
}
