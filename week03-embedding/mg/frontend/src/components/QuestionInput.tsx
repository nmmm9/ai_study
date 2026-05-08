"use client";

import { useState } from "react";

interface QuestionInputProps {
  onSubmit: (question: string) => void;
  disabled: boolean;
  hasDocument: boolean;
  hasCollection: boolean;
}

export default function QuestionInput({
  onSubmit,
  disabled,
  hasDocument,
  hasCollection,
}: QuestionInputProps) {
  const [question, setQuestion] = useState("");

  const canSubmit = !disabled && question.trim() && hasDocument && hasCollection;

  const handleSubmit = () => {
    if (!canSubmit) return;
    onSubmit(question);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  const placeholder = hasCollection
    ? "문서에 대해 질문하세요..."
    : hasDocument
      ? "먼저 임베딩을 저장하세요"
      : "먼저 문서를 선택하세요";

  return (
    <div className="animate-fade-in-up flex gap-3">
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled || !hasCollection}
        placeholder={placeholder}
        className="flex-1 rounded-xl border border-stroke bg-base-50 px-4 py-3 text-sm text-pearl placeholder:text-pearl-muted focus:border-gold-dim/50 focus:outline-none disabled:opacity-40"
      />
      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className="rounded-xl bg-gold px-6 py-3 text-sm font-medium text-base transition-all hover:bg-gold-dim disabled:cursor-not-allowed disabled:opacity-25"
      >
        {disabled ? (
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-base/30 border-t-base" />
        ) : (
          "검색!"
        )}
      </button>
    </div>
  );
}
