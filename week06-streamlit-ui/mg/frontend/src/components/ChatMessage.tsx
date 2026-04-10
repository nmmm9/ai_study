"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import type { ChatMessage as ChatMessageType } from "@/types/chat";

interface Props {
  message: ChatMessageType;
  onEdit?: (messageId: string, newContent: string) => void;
}

export default function ChatMessage({ message, onEdit }: Props) {
  const [showSources, setShowSources] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(message.content);
  const isUser = message.role === "user";

  const handleEditSubmit = () => {
    const trimmed = editText.trim();
    if (trimmed && trimmed !== message.content && onEdit) {
      onEdit(message.id, trimmed);
    }
    setIsEditing(false);
  };

  const handleEditKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleEditSubmit();
    }
    if (e.key === "Escape") {
      setEditText(message.content);
      setIsEditing(false);
    }
  };

  return (
    <div className={`group py-5 ${isUser ? "" : "bg-base-50/20"}`}>
      <div className="mx-auto max-w-3xl px-6">
        <div className="flex gap-5">
          {/* Avatar */}
          <div
            className={`mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full text-[10px] font-bold tracking-tight ${
              isUser
                ? "bg-pearl/8 text-pearl-dim"
                : "bg-gold/10 text-gold"
            }`}
          >
            {isUser ? "나" : "AI"}
          </div>

          {/* Content */}
          <div className="min-w-0 flex-1 pt-0.5">
            {isUser ? (
              <div>
                {isEditing ? (
                  <div className="space-y-2">
                    <textarea
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      onKeyDown={handleEditKeyDown}
                      className="w-full resize-none rounded-lg border border-stroke bg-base-100 px-3 py-2 text-[14px] text-pearl focus:border-gold-dim focus:outline-none"
                      rows={2}
                      autoFocus
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={handleEditSubmit}
                        className="rounded-md px-3 py-1 text-[11px] font-medium text-gold bg-gold/10 hover:bg-gold/20 transition-colors"
                      >
                        전송
                      </button>
                      <button
                        onClick={() => { setEditText(message.content); setIsEditing(false); }}
                        className="rounded-md px-3 py-1 text-[11px] text-pearl-muted hover:text-pearl-dim transition-colors"
                      >
                        취소
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start gap-2">
                    <p className="flex-1 text-[14px] leading-relaxed text-pearl">{message.content}</p>
                    {onEdit && (
                      <button
                        onClick={() => setIsEditing(true)}
                        className="mt-0.5 text-[10px] text-pearl-muted/0 group-hover:text-pearl-muted/50 hover:!text-pearl-muted transition-colors"
                      >
                        수정
                      </button>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <>
                {/* Thinking steps */}
                {message.thinking && message.thinking.length > 0 && (
                  <div className="mb-3 space-y-1.5">
                    {message.thinking.map((t, i) => (
                      <div key={i} className="flex items-start gap-2 text-[12px] text-pearl-muted/50">
                        <span className="mt-0.5 text-gold/40">
                          {message.isStreaming && i === message.thinking!.length - 1 ? "●" : "✓"}
                        </span>
                        <span>
                          <strong className="text-pearl-muted/70">{t.step}</strong>
                          {" — "}{t.detail}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {message.content ? (
                  <div className="chat-markdown text-[14px] leading-[1.8] text-pearl-dim">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                    {message.isStreaming && (
                      <span className="inline-block h-[18px] w-[2px] animate-blink bg-gold/60 ml-0.5 align-text-bottom" />
                    )}
                  </div>
                ) : message.isStreaming && (!message.thinking || message.thinking.length === 0) ? (
                  <div className="flex items-center gap-2 text-[13px] text-pearl-muted/60">
                    <span className="flex gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-gold/40 animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="h-1.5 w-1.5 rounded-full bg-gold/40 animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="h-1.5 w-1.5 rounded-full bg-gold/40 animate-bounce" style={{ animationDelay: "300ms" }} />
                    </span>
                    문서를 검색하고 있습니다...
                  </div>
                ) : null}

                {/* Sources */}
                {message.sources && message.sources.length > 0 && !message.isStreaming && (
                  <div className="mt-4 pt-3 border-t border-stroke/30">
                    <button
                      onClick={() => setShowSources(!showSources)}
                      className="text-[11px] text-pearl-muted/60 transition-colors hover:text-pearl-muted"
                    >
                      {showSources ? "소스 접기" : `참조 소스 ${message.sources.length}개 보기`}
                    </button>

                    {showSources && (
                      <div className="mt-3 space-y-2 animate-fade-in">
                        {message.sources.map((s, i) => (
                          <div
                            key={i}
                            className="rounded-lg bg-base-100/60 px-4 py-3"
                          >
                            <div className="mb-1.5 flex items-center gap-3">
                              <span className="text-[10px] font-medium text-pearl-muted/50">
                                #{s.index}
                              </span>
                              <span className="text-[10px] text-gold/60">
                                {(s.score * 100).toFixed(0)}% 일치
                              </span>
                            </div>
                            <p className="text-[12px] leading-relaxed text-pearl-muted/70">
                              {s.text}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
