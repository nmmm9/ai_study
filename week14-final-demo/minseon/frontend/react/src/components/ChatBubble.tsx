import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Message } from '../types'

interface Props {
  message: Message
  isStreaming?: boolean
}

export default function ChatBubble({ message, isStreaming }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-[#3a3a3a] flex items-center justify-center text-sm mr-2 mt-1 flex-shrink-0">
          AI
        </div>
      )}

      <div
        className={`
          max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed
          ${isUser
            ? 'bg-[#4a7cff] text-white rounded-br-sm'
            : 'bg-[#2a2a2a] text-gray-100 rounded-bl-sm border border-[#3a3a3a]'
          }
        `}
      >
        {isUser ? (
          message.content
        ) : (
          <div className="markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content || (isStreaming ? '▍' : '')}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
