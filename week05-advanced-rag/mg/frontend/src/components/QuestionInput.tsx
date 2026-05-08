"use client";

import { useState } from "react";

interface Props {
  onSubmit: (question: string) => void;
  disabled: boolean;
  hasCollection: boolean;
}

export default function QuestionInput({
  onSubmit,
  disabled,
  hasCollection,
}: Props) {
  const [question, setQuestion] = useState("");

  const handleSubmit = () => {
    const q = question.trim();
    if (!q) return;
    onSubmit(q);
  };

  return (
    <section className="animate-fade-in-up rounded-2xl border border-stroke bg-base-50 p-5">
      <h2 className="mb-3 text-sm font-medium tracking-wide text-pearl-dim">
        3. 질문 입력
      </h2>
      <div className="flex gap-3">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          disabled={disabled || !hasCollection}
          placeholder={
            hasCollection
              ? "질문을 입력하세요 (Basic vs Advanced 비교)"
              : "먼저 컬렉션을 선택하세요"
          }
          className="flex-1 rounded-xl border border-stroke bg-base-100 px-4 py-3 text-sm text-pearl placeholder-pearl-muted transition-all focus:border-gold-dim focus:outline-none disabled:opacity-30"
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !hasCollection || !question.trim()}
          className="rounded-xl bg-gold/15 px-6 py-3 text-sm font-medium text-gold transition-all hover:bg-gold/25 disabled:opacity-30"
        >
          {disabled ? "비교 중..." : "비교 검색"}
        </button>
      </div>
    </section>
  );
}
