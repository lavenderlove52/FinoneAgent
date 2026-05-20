import React, { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ChevronDown, ChevronRight, Brain } from 'lucide-react'
import type { Message } from '../api/types'

interface Props {
  message: Message
  isStreaming?: boolean
  thinking?: string
  isThinkingStreaming?: boolean
}

export default function MessageBubble({
  message,
  isStreaming = false,
  thinking,
  isThinkingStreaming = false,
}: Props) {
  const isUser = message.role === 'user'
  const contentRef = useRef<HTMLDivElement>(null)
  const thinkingRef = useRef<HTMLDivElement>(null)
  const [showThinking, setShowThinking] = useState(false)

  useEffect(() => {
    if (!isStreaming || !contentRef.current) return
    contentRef.current.scrollTop = contentRef.current.scrollHeight
  }, [isStreaming, message.content])

  // 思考流式开始时自动展开思考面板
  useEffect(() => {
    if (isThinkingStreaming) {
      setShowThinking(true)
    }
  }, [isThinkingStreaming])

  // 思考流式时自动滚动到底
  useEffect(() => {
    if (!isThinkingStreaming || !showThinking || !thinkingRef.current) return
    thinkingRef.current.scrollTop = thinkingRef.current.scrollHeight
  }, [isThinkingStreaming, showThinking, thinking])

  const hasThinking = !!thinking && thinking.trim().length > 0

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-blue-600/90 flex items-center justify-center text-xs font-bold mr-3 flex-shrink-0 mt-1 shadow-sm">
          AI
        </div>
      )}

      <div
        className={`${
          isUser
            ? 'max-w-[75%] rounded-2xl px-4 py-3 bg-blue-600 text-white rounded-br-sm'
            : 'w-full max-w-4xl'
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
        ) : (
          <>
            {/* 思考过程折叠区 */}
            {(hasThinking || isThinkingStreaming) && (
              <div className="mb-3">
                <button
                  onClick={() => setShowThinking((v) => !v)}
                  className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors select-none"
                >
                  <Brain size={13} className={isThinkingStreaming && !showThinking ? 'animate-pulse text-blue-400' : ''} />
                  {isThinkingStreaming ? (
                    <span className="text-blue-400">
                      思考中
                      <span className="inline-flex gap-0.5 ml-1">
                        <span className="animate-bounce" style={{ animationDelay: '0ms' }}>·</span>
                        <span className="animate-bounce" style={{ animationDelay: '150ms' }}>·</span>
                        <span className="animate-bounce" style={{ animationDelay: '300ms' }}>·</span>
                      </span>
                    </span>
                  ) : (
                    <span>查看思考过程</span>
                  )}
                  {showThinking ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                </button>

                {showThinking && (
                  <div
                    ref={thinkingRef}
                    className="mt-2 max-h-72 overflow-y-auto rounded-lg border border-slate-700/60 bg-slate-900/60 px-4 py-3"
                  >
                    <div className="prose prose-xs prose-invert max-w-none text-slate-400 leading-relaxed">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {thinking ?? ''}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 正文答案 */}
            <div
              ref={contentRef}
              className={`prose prose-sm prose-invert max-w-none text-slate-200 ${
                isStreaming ? 'h-60 overflow-y-auto pr-3' : ''
              }`}
            >
              {message.content ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
              ) : isStreaming ? (
                <span className="text-slate-500 text-sm">正在生成…</span>
              ) : null}
            </div>
          </>
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
