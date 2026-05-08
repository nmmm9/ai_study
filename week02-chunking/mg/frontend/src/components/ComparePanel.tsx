import type { RawResult, ChunkedResult } from "@/types/compare";
import AnswerCard from "./AnswerCard";

interface ComparePanelProps {
  rawResult: RawResult | null;
  chunkedResult: ChunkedResult | null;
  isLoading: boolean;
}

export default function ComparePanel({
  rawResult,
  chunkedResult,
  isLoading,
}: ComparePanelProps) {
  if (!isLoading && !rawResult && !chunkedResult) return null;

  return (
    <div className="flex gap-4">
      <AnswerCard
        title="청킹 없이"
        answer={rawResult?.answer ?? null}
        error={rawResult?.error}
        message={rawResult?.message}
        variant="raw"
        stats={rawResult?.stats ?? null}
        isLoading={isLoading}
      />
      <AnswerCard
        title="청킹 적용"
        answer={chunkedResult?.answer ?? null}
        variant="chunked"
        stats={chunkedResult?.stats ?? null}
        isLoading={isLoading}
      />
    </div>
  );
}
