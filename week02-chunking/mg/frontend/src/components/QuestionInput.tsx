"use client";

import { useState } from "react";

interface QuestionInputProps {
  onSubmit: (question: string) => void;
  disabled: boolean;
  hasDocument: boolean;
}

export default function QuestionInput({
  onSubmit,
  disabled,
  hasDocument,
}: QuestionInputProps) {
  const [question, setQuestion] = useState("");

  const handleSubmit = () => {
    if (!question.trim() || disabled || !hasDocument) return;
    onSubmit(question);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="animate-fade-in-up flex gap-3">
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={
          hasDocument
            ? "문서에 대해 질문하세요..."
            : "먼저 문서를 선택하세요"
        }
        className="flex-1 rounded-xl border border-stroke bg-base-50 px-4 py-3 text-sm text-pearl placeholder:text-pearl-muted focus:border-gold-dim/50 focus:outline-none disabled:opacity-40"
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !question.trim() || !hasDocument}
        className="rounded-xl bg-gold px-6 py-3 text-sm font-medium text-base transition-all hover:bg-gold-dim disabled:cursor-not-allowed disabled:opacity-25"
      >
        {disabled ? (
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-base/30 border-t-base" />
        ) : (
          "비교 시작"
        )}
      </button>
    </div>
  );
}
