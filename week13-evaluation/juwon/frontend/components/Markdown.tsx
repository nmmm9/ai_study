import ReactMarkdown from "react-markdown";

export default function Markdown({ content }: { content: string }) {
  return (
    <ReactMarkdown
      components={{
        h1: ({ children }) => <h1 className="text-base font-bold text-[#c9d1d9] mb-2 mt-3">{children}</h1>,
        h2: ({ children }) => <h2 className="text-sm font-bold text-[#c9d1d9] mb-2 mt-3 border-b border-[#21262d] pb-1">{children}</h2>,
        h3: ({ children }) => <h3 className="text-xs font-bold text-[#58a6ff] mb-1 mt-2">{children}</h3>,
        h4: ({ children }) => <h4 className="text-xs font-semibold text-[#8b949e] mb-1 mt-2">{children}</h4>,
        p:  ({ children }) => <p  className="text-xs text-[#8b949e] leading-relaxed mb-2">{children}</p>,
        ul: ({ children }) => <ul className="space-y-1 mb-2 pl-3">{children}</ul>,
        ol: ({ children }) => <ol className="space-y-1 mb-2 pl-3 list-decimal">{children}</ol>,
        li: ({ children }) => (
          <li className="text-xs text-[#8b949e] leading-relaxed flex gap-1.5">
            <span className="text-[#58a6ff] mt-0.5 shrink-0">•</span>
            <span>{children}</span>
          </li>
        ),
        strong: ({ children }) => <strong className="text-[#c9d1d9] font-semibold">{children}</strong>,
        em:     ({ children }) => <em className="text-[#8b949e] italic">{children}</em>,
        code:   ({ children }) => (
          <code className="bg-[#0d1117] text-[#79c0ff] rounded px-1 py-0.5 text-xs font-mono">{children}</code>
        ),
        hr: () => <hr className="border-[#21262d] my-3" />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
