import React, { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import type { Message } from '../api/types'

interface Props {
  message: Message
  isStreaming?: boolean
}

export default function MessageBubble({ message, isStreaming = false }: Props) {
  const isUser = message.role === 'user'
  const contentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isStreaming || !contentRef.current) return
    contentRef.current.scrollTop = contentRef.current.scrollHeight
  }, [isStreaming, message.content])

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-blue-600/90 flex items-center justify-center text-xs font-bold mr-3 flex-shrink-0 mt-1 shadow-sm">
          AI
        </div>
      )}
      <div
        className={`rounded-2xl px-4 py-3 ${
          isUser
            ? 'max-w-[75%] bg-blue-600 text-white rounded-br-sm'
            : 'w-full max-w-4xl bg-transparent text-slate-200 px-1 py-1 rounded-none'
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
        ) : (
          <div
            ref={contentRef}
            className={`prose prose-sm prose-invert max-w-none ${
              isStreaming ? 'h-60 overflow-y-auto pr-3' : ''
            }`}
          >
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center text-xs font-bold ml-3 flex-shrink-0 mt-1">
          U
        </div>
      )}
    </div>
  )
}
