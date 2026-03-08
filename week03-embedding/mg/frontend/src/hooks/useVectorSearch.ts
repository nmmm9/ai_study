"use client";

import { useState, useCallback, useEffect } from "react";
import type {
  SampleInfo,
  EmbedResult,
  SearchResult,
  VizData,
  CollectionItem,
} from "@/types/vector";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useVectorSearch() {
  const [document, setDocument] = useState("");
  const [selectedModel, setSelectedModel] = useState("gpt-4o-mini");
  const [samples, setSamples] = useState<SampleInfo[]>([]);

  const [embedResult, setEmbedResult] = useState<EmbedResult | null>(null);
  const [isEmbedding, setIsEmbedding] = useState(false);

  const [memoryResult, setMemoryResult] = useState<SearchResult | null>(null);
  const [vectordbResult, setVectordbResult] = useState<SearchResult | null>(
    null
  );
  const [isSearching, setIsSearching] = useState(false);
  const [lastQuestion, setLastQuestion] = useState("");

  const [vizData, setVizData] = useState<VizData | null>(null);
  const [collections, setCollections] = useState<CollectionItem[]>([]);

  // Reset embed/search state when document changes
  useEffect(() => {
    setEmbedResult(null);
    setMemoryResult(null);
    setVectordbResult(null);
    setVizData(null);
    setLastQuestion("");
  }, [document]);

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
      setMemoryResult(null);
      setVectordbResult(null);
      setVizData(null);
      setLastQuestion("");
    },
    []
  );

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

  const deleteCollection = useCallback(
    async (name: string) => {
      try {
        await fetch(`${API_URL}/api/collections/${name}`, {
          method: "DELETE",
        });
        if (embedResult?.collection_name === name) {
          setEmbedResult(null);
          setMemoryResult(null);
          setVectordbResult(null);
          setVizData(null);
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
    setMemoryResult(null);
    setVectordbResult(null);
    setVizData(null);

    try {
      const res = await fetch(`${API_URL}/api/embed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document,
          chunk_size: 500,
          chunk_overlap: 50,
        }),
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

  const search = useCallback(
    async (question: string) => {
      if (!question.trim() || !embedResult || isSearching) return;
      setIsSearching(true);
      setMemoryResult(null);
      setVectordbResult(null);
      setLastQuestion(question);

      const hasDocument = document.trim().length > 0;

      try {
        // VectorDB search always runs
        const vecPromise = fetch(`${API_URL}/api/search/vectordb`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question,
            collection_name: embedResult.collection_name,
            model: selectedModel,
            top_k: 3,
          }),
        });

        // Memory search only if document is available
        const memPromise = hasDocument
          ? fetch(`${API_URL}/api/search/memory`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                question,
                document,
                model: selectedModel,
                chunk_size: 500,
                chunk_overlap: 50,
                top_k: 3,
              }),
            })
          : null;

        const [vecRes, memRes] = await Promise.all([
          vecPromise,
          memPromise,
        ]);

        const vecData = await vecRes.json();
        setVectordbResult(vecData);

        if (memRes) {
          const memData = await memRes.json();
          setMemoryResult(memData);
        }

        // Fetch viz with query
        try {
          const vizUrl = new URL(
            `${API_URL}/api/visualize/${embedResult.collection_name}`
          );
          vizUrl.searchParams.set("query", question);
          const vizRes = await fetch(vizUrl.toString());
          const vizJson: VizData = await vizRes.json();
          setVizData(vizJson);
        } catch (vizErr) {
          console.error("Viz error:", vizErr);
        }
      } catch (err) {
        console.error("Search error:", err);
      } finally {
        setIsSearching(false);
      }
    },
    [document, embedResult, selectedModel, isSearching]
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
    memoryResult,
    vectordbResult,
    isSearching,
    search,
    lastQuestion,
    vizData,
    collections,
    fetchCollections,
    deleteCollection,
    selectCollection,
  };
}
