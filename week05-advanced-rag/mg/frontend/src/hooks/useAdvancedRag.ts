"use client";

import { useState, useCallback, useEffect } from "react";
import type {
  SampleInfo,
  CollectionItem,
  EmbedResult,
  CompareResult,
} from "@/types/rag";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useAdvancedRag() {
  const [document, setDocument] = useState("");
  const [selectedModel, setSelectedModel] = useState("gpt-4o-mini");
  const [samples, setSamples] = useState<SampleInfo[]>([]);

  const [embedResult, setEmbedResult] = useState<EmbedResult | null>(null);
  const [isEmbedding, setIsEmbedding] = useState(false);

  const [collections, setCollections] = useState<CollectionItem[]>([]);

  const [compareResult, setCompareResult] = useState<CompareResult | null>(
    null
  );
  const [isComparing, setIsComparing] = useState(false);

  // Reset results when document changes
  useEffect(() => {
    setCompareResult(null);
  }, [document]);

  // ─── Samples ───

  const fetchSamples = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/samples`);
      const data = await res.json();
      setSamples(data.samples);
    } catch {
      /* ignore */
    }
  }, []);

  const loadSample = useCallback(async (id: string) => {
    try {
      const res = await fetch(`${API}/api/samples/${id}`);
      const data = await res.json();
      setDocument(data.content);
      setEmbedResult(null);
      setCompareResult(null);
    } catch {
      /* ignore */
    }
  }, []);

  // ─── Collections ───

  const fetchCollections = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/collections`);
      const data = await res.json();
      setCollections(data.collections);
    } catch {
      /* ignore */
    }
  }, []);

  const selectCollection = useCallback(
    (name: string, count: number) => {
      setEmbedResult({
        collection_name: name,
        chunk_count: count,
        dimension: 1536,
        embed_time_ms: 0,
        store_time_ms: 0,
        total_time_ms: 0,
        embed_cost: 0,
      });
      setCompareResult(null);
    },
    []
  );

  const deleteCollection = useCallback(
    async (name: string) => {
      try {
        await fetch(`${API}/api/collections/${name}`, { method: "DELETE" });
        if (embedResult?.collection_name === name) {
          setEmbedResult(null);
          setCompareResult(null);
        }
        fetchCollections();
      } catch {
        /* ignore */
      }
    },
    [embedResult, fetchCollections]
  );

  // ─── Embed ───

  const embedDocument = useCallback(async () => {
    if (!document) return;
    setIsEmbedding(true);
    try {
      const res = await fetch(`${API}/api/embed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document }),
      });
      if (!res.ok) throw new Error("Embed failed");
      const data: EmbedResult = await res.json();
      setEmbedResult(data);
      fetchCollections();
    } catch {
      /* ignore */
    } finally {
      setIsEmbedding(false);
    }
  }, [document, fetchCollections]);

  // ─── Compare ───

  const compare = useCallback(
    async (question: string) => {
      if (!embedResult) return;
      setIsComparing(true);
      setCompareResult(null);
      try {
        const res = await fetch(`${API}/api/compare`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question,
            collection_name: embedResult.collection_name,
            top_k: 5,
            model: selectedModel,
          }),
        });
        if (!res.ok) throw new Error("Compare failed");
        const data: CompareResult = await res.json();
        setCompareResult(data);
      } catch {
        /* ignore */
      } finally {
        setIsComparing(false);
      }
    },
    [embedResult, selectedModel]
  );

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
    collections,
    fetchCollections,
    selectCollection,
    deleteCollection,
    compareResult,
    isComparing,
    compare,
  };
}
