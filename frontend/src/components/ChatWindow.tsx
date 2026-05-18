import React, { useCallback, useEffect, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import type { Message, Session } from '../api/types'
import MessageBubble from './MessageBubble'
import { listMessages } from '../api/client'

interface Props {
  session: Session | null
  onSessionUpdated?: () => void
}

let msgIdCounter = -1
function tempId() {
  return msgIdCounter--
}

export default function ChatWindow({ session, onSessionUpdated }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [streamingMessageId, setStreamingMessageId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const messagesRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (!session) {
      setMessages([])
      return
    }
    setLoading(true)
    listMessages(session.id)
      .then(setMessages)
      .finally(() => setLoading(false))
  }, [session?.id])

  useEffect(() => {
    const container = messagesRef.current
    if (!container) return

    // Streaming 时使用立即滚动，避免每个 chunk 都触发平滑动画导致输入区抖动。
    container.scrollTo({
      top: container.scrollHeight,
      behavior: 'auto',
    })
  }, [messages, streaming])

  const sendMessage = useCallback(async () => {
    if (!session || !input.trim() || streaming) return

    const query = input.trim()
    setInput('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    setStreaming(true)

    const userMsg: Message = {
      id: tempId(),
      session_id: session.id,
      user_id: 0,
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])

    const assistantMsgId = tempId()
    const assistantMsg: Message = {
      id: assistantMsgId,
      session_id: session.id,
      user_id: 0,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, assistantMsg])
    setStreamingMessageId(assistantMsgId)

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/chat/${session.id}/stream`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      })

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const jsonStr = line.slice(6).trim()
          if (!jsonStr) continue
          try {
            const event = JSON.parse(jsonStr)
            if (event.type === 'chunk') {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, content: m.content + event.content }
                    : m
                )
              )
            } else if (event.type === 'done') {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId ? { ...m, id: event.message_id } : m
                )
              )
              setStreamingMessageId(null)
              onSessionUpdated?.()
            } else if (event.type === 'error') {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, content: `错误：${event.message}` }
                    : m
                )
              )
              setStreamingMessageId(null)
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? { ...m, content: `请求失败：${String(err)}` }
            : m
        )
      )
      setStreamingMessageId(null)
    } finally {
      setStreaming(false)
      textareaRef.current?.focus()
    }
  }, [session, input, streaming, onSessionUpdated])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  if (!session) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#1a1a2e]">
        <div className="text-center text-slate-500">
          <p className="text-xl mb-2">欢迎使用 FinoneAgent</p>
          <p className="text-sm">请从左侧选择会话或新建一个会话</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col bg-[#1a1a2e] min-w-0 min-h-0">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[#1e3a5f] bg-[#16213e]">
        <h2 className="text-white font-semibold truncate">{session.title}</h2>
      </div>

      {/* Messages */}
      <div ref={messagesRef} className="flex-1 min-h-0 overflow-y-auto overscroll-contain px-4 py-4">
        {loading ? (
          <div className="flex items-center justify-center h-full text-slate-500">加载中...</div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-slate-500 text-sm">
            发送第一条消息开始对话
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isStreaming={streaming && msg.id === streamingMessageId}
            />
          ))
        )}
      </div>

      {/* Input */}
      <div className="px-4 py-4 border-t border-[#1e3a5f] bg-[#16213e]">
        <div className="flex items-end gap-3 bg-[#0f3460] rounded-xl px-4 py-3 border border-[#1e3a5f] focus-within:border-blue-500 transition-colors">
          <textarea
            ref={textareaRef}
            className="flex-1 bg-transparent text-slate-200 placeholder-slate-500 text-sm resize-none outline-none min-h-[20px] max-h-[120px]"
            placeholder="输入消息（Enter 发送，Shift+Enter 换行）"
            rows={1}
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              e.target.style.height = 'auto'
              e.target.style.height = `${e.target.scrollHeight}px`
            }}
            onKeyDown={handleKeyDown}
            disabled={streaming}
          />
          <button
            onClick={sendMessage}
            disabled={streaming || !input.trim()}
            className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {streaming ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send size={15} className="text-white" />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
