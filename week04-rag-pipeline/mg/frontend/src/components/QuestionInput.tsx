"use client";

import { useState } from "react";

interface QuestionInputProps {
  onSubmit: (question: string) => void;
  disabled: boolean;
  hasCollection: boolean;
}

export default function QuestionInput({
  onSubmit,
  disabled,
  hasCollection,
}: QuestionInputProps) {
  const [question, setQuestion] = useState("");

  const handleSubmit = () => {
    if (question.trim() && !disabled && hasCollection) {
      onSubmit(question.trim());
      setQuestion("");
    }
  };

  const placeholder = hasCollection
    ? "질문을 입력하세요 — RAG 파이프라인으로 답변을 생성합니다"
    : "먼저 컬렉션을 선택하거나 문서를 임베딩하세요";

  return (
    <section className="animate-fade-in-up rounded-2xl border border-stroke bg-base-50 p-5">
      <h2 className="mb-3 font-serif text-sm font-light text-pearl">
        단일 질의응답
      </h2>
      <div className="flex gap-3">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder={placeholder}
          disabled={disabled || !hasCollection}
          className="flex-1 rounded-xl border border-stroke bg-base px-4 py-2.5 text-sm text-pearl placeholder:text-pearl-muted/50 focus:border-gold-dim focus:outline-none disabled:opacity-30"
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !question.trim() || !hasCollection}
          className="rounded-xl bg-gold px-5 py-2.5 text-xs font-medium text-base transition-all hover:bg-gold-bright active:scale-95 disabled:opacity-30"
        >
          {disabled ? (
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-base border-t-transparent" />
              검색 중...
            </span>
          ) : (
            "검색!"
          )}
        </button>
      </div>
    </section>
  );
}
