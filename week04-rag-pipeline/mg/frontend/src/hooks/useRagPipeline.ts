"use client";

import { useState, useCallback, useEffect } from "react";
import type {
  SampleInfo,
  EmbedResult,
  RagResponse,
  CollectionItem,
  ChatMessage,
} from "@/types/rag";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useRagPipeline() {
  const [document, setDocument] = useState("");
  const [selectedModel, setSelectedModel] = useState("gpt-4o-mini");
  const [samples, setSamples] = useState<SampleInfo[]>([]);

  const [embedResult, setEmbedResult] = useState<EmbedResult | null>(null);
  const [isEmbedding, setIsEmbedding] = useState(false);

  // Single RAG
  const [ragResult, setRagResult] = useState<RagResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  // Chat
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatSources, setChatSources] = useState<RagResponse | null>(null);
  const [isChatting, setIsChatting] = useState(false);

  const [collections, setCollections] = useState<CollectionItem[]>([]);

  // Reset when document changes
  useEffect(() => {
    setEmbedResult(null);
    setRagResult(null);
    setChatMessages([]);
    setChatSources(null);
  }, [document]);

  const fetchSamples = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/samples`);
      const data = await res.json();
      setSamples(data.samples);
    } catch (err) {
      console.error("Failed to fetch samples:", err);
    }
  }, []);

  const loadSample = useCallback(async (id: string) => {
    try {
      const res = await fetch(`${API_URL}/api/samples/${id}`);
      const data = await res.json();
      setDocument(data.content);
    } catch (err) {
      console.error("Failed to load sample:", err);
    }
  }, []);

  const fetchCollections = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/collections`);
      const data = await res.json();
      setCollections(data.collections);
    } catch (err) {
      console.error("Failed to fetch collections:", err);
    }
  }, []);

  const selectCollection = useCallback((name: string, count: number) => {
    setEmbedResult({
      collection_name: name,
      chunk_count: count,
      dimension: 1536,
      embed_time_ms: 0,
      store_time_ms: 0,
      total_time_ms: 0,
      embed_cost: 0,
    });
    setRagResult(null);
    setChatMessages([]);
    setChatSources(null);
  }, []);

  const deleteCollection = useCallback(
    async (name: string) => {
      try {
        await fetch(`${API_URL}/api/collections/${name}`, { method: "DELETE" });
        if (embedResult?.collection_name === name) {
          setEmbedResult(null);
          setRagResult(null);
          setChatMessages([]);
          setChatSources(null);
        }
        fetchCollections();
      } catch (err) {
        console.error("Failed to delete collection:", err);
      }
    },
    [embedResult, fetchCollections]
  );

  const embedDocument = useCallback(async () => {
    if (!document.trim() || isEmbedding) return;
    setIsEmbedding(true);
    setEmbedResult(null);
    setRagResult(null);

    try {
      const res = await fetch(`${API_URL}/api/embed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document, chunk_size: 500, chunk_overlap: 50 }),
      });
      const data: EmbedResult = await res.json();
      setEmbedResult(data);
      fetchCollections();
    } catch (err) {
      console.error("Embed error:", err);
    } finally {
      setIsEmbedding(false);
    }
  }, [document, isEmbedding, fetchCollections]);

  // Single RAG search
  const search = useCallback(
    async (question: string) => {
      if (!question.trim() || !embedResult || isSearching) return;
      setIsSearching(true);
      setRagResult(null);

      try {
        const res = await fetch(`${API_URL}/api/rag`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question,
            collection_name: embedResult.collection_name,
            model: selectedModel,
            top_k: 5,
          }),
        });
        const data: RagResponse = await res.json();
        setRagResult(data);
      } catch (err) {
        console.error("Search error:", err);
      } finally {
        setIsSearching(false);
      }
    },
    [embedResult, selectedModel, isSearching]
  );

  // Chat RAG
  const sendChatMessage = useCallback(
    async (question: string) => {
      if (!question.trim() || !embedResult || isChatting) return;
      setIsChatting(true);

      const newMessages: ChatMessage[] = [
        ...chatMessages,
        { role: "user", content: question },
      ];
      setChatMessages(newMessages);

      try {
        const res = await fetch(`${API_URL}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question,
            collection_name: embedResult.collection_name,
            history: chatMessages,
            model: selectedModel,
            top_k: 5,
          }),
        });
        const data: RagResponse = await res.json();
        setChatMessages([
          ...newMessages,
          { role: "assistant", content: data.answer },
        ]);
        setChatSources(data);
      } catch (err) {
        console.error("Chat error:", err);
        // Remove the user message on error
        setChatMessages(chatMessages);
      } finally {
        setIsChatting(false);
      }
    },
    [embedResult, selectedModel, isChatting, chatMessages]
  );

  const clearChat = useCallback(() => {
    setChatMessages([]);
    setChatSources(null);
  }, []);

  return {
    document,
    setDocument,
    selectedModel,
    setSelectedModel,
    samples,
    fetchSamples,
    loadSample,
    embedResult,
    isEmbedding,
    embedDocument,
    ragResult,
    isSearching,
    search,
    chatMessages,
    chatSources,
    isChatting,
    sendChatMessage,
    clearChat,
    collections,
    fetchCollections,
    selectCollection,
    deleteCollection,
  };
}
