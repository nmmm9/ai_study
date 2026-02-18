"use client";

import { useState, useCallback } from "react";
import type { SampleInfo, RawResult, ChunkedResult } from "@/types/compare";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useCompare() {
  const [document, setDocument] = useState("");
  const [selectedModel, setSelectedModel] = useState("gpt-4o-mini");
  const [samples, setSamples] = useState<SampleInfo[]>([]);
  const [rawResult, setRawResult] = useState<RawResult | null>(null);
  const [chunkedResult, setChunkedResult] = useState<ChunkedResult | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);

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

  const compare = useCallback(
    async (question: string) => {
      if (!document.trim() || !question.trim() || isLoading) return;

      setIsLoading(true);
      setRawResult(null);
      setChunkedResult(null);

      try {
        const [rawRes, chunkedRes] = await Promise.all([
          fetch(`${API_URL}/api/ask-raw`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              document,
              question,
              model: selectedModel,
            }),
          }),
          fetch(`${API_URL}/api/ask-chunked`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              document,
              question,
              model: selectedModel,
              chunk_size: 500,
              chunk_overlap: 50,
              top_k: 3,
            }),
          }),
        ]);

        const [rawData, chunkedData] = await Promise.all([
          rawRes.json(),
          chunkedRes.json(),
        ]);

        setRawResult(rawData);
        setChunkedResult(chunkedData);
      } catch (err) {
        console.error("Compare error:", err);
      } finally {
        setIsLoading(false);
      }
    },
    [document, selectedModel, isLoading]
  );

  const reset = useCallback(() => {
    setRawResult(null);
    setChunkedResult(null);
  }, []);

  return {
    document,
    setDocument,
    selectedModel,
    setSelectedModel,
    samples,
    fetchSamples,
    loadSample,
    rawResult,
    chunkedResult,
    isLoading,
    compare,
    reset,
  };
}
