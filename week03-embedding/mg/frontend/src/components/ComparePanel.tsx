import type { SearchResult } from "@/types/vector";
import AnswerCard from "./AnswerCard";

interface ComparePanelProps {
  memoryResult: SearchResult | null;
  vectordbResult: SearchResult | null;
  isLoading: boolean;
  hasDocument: boolean;
}

export default function ComparePanel({
  memoryResult,
  vectordbResult,
  isLoading,
  hasDocument,
}: ComparePanelProps) {
  if (!isLoading && !memoryResult && !vectordbResult) return null;

  return (
    <div className="flex gap-4">
      {hasDocument ? (
        <AnswerCard
          title="인메모리 검색"
          result={memoryResult}
          variant="memory"
          isLoading={isLoading}
        />
      ) : (
        vectordbResult && (
          <div className="flex flex-1 flex-col items-center justify-center rounded-2xl border border-stroke bg-base-50 p-5">
            <p className="text-xs text-pearl-muted">
              문서를 입력하면 인메모리 검색과 비교할 수 있습니다
            </p>
          </div>
        )
      )}
      <AnswerCard
        title="Vector DB 검색"
        result={vectordbResult}
        variant="vectordb"
        isLoading={isLoading}
      />
    </div>
  );
}
