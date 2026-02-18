import type { ChatMessage } from "@/types/chat";
import TokenBadge from "./TokenBadge";

interface ChatBubbleProps {
  message: ChatMessage;
  isStreaming: boolean;
}

export default function ChatBubble({ message, isStreaming }: ChatBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`animate-fade-in-up flex ${isUser ? "justify-end" : "justify-start"} py-1`}
    >
      <div
        className={`max-w-[78%] rounded-2xl px-5 py-3.5 ${
          isUser
            ? "bg-gold/8 text-pearl"
            : "border border-stroke bg-base-50 text-pearl"
        }`}
      >
        {/* Content */}
        <p className="whitespace-pre-wrap break-words text-[13.5px] leading-[1.8]">
          {message.content}
          {isStreaming && !isUser && (
            <span className="animate-cursor-blink ml-0.5 inline-block h-[14px] w-[1.5px] translate-y-[2px] bg-gold/70" />
          )}
        </p>

        {/* Token badge */}
        {message.usage && <TokenBadge usage={message.usage} />}
      </div>
    </div>
  );
}
