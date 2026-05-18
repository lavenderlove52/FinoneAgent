import React, { useState } from 'react'
import { LogOut, MessageSquarePlus, Trash2, Shield } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { Session } from '../api/types'
import { useAuth } from '../contexts/AuthContext'

interface Props {
  sessions: Session[]
  currentSessionId: number | null
  onSelectSession: (id: number) => void
  onNewSession: () => void
  onDeleteSession: (id: number) => void
  onRenameSession: (id: number, title: string) => void
}

export default function Sidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onRenameSession,
}: Props) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [hoveredId, setHoveredId] = useState<number | null>(null)

  const handleDoubleClick = (session: Session) => {
    setEditingId(session.id)
    setEditTitle(session.title)
  }

  const handleRenameSubmit = (sessionId: number) => {
    if (editTitle.trim()) {
      onRenameSession(sessionId, editTitle.trim())
    }
    setEditingId(null)
  }

  return (
    <div className="flex flex-col h-full bg-[#0f3460] w-64 flex-shrink-0">
      {/* Header */}
      <div className="p-4 border-b border-[#1e3a5f]">
        <h1 className="text-lg font-bold text-white mb-3">FinoneAgent</h1>
        <button
          onClick={onNewSession}
          className="w-full flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <MessageSquarePlus size={16} />
          新建会话
        </button>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto p-2">
        {sessions.length === 0 ? (
          <p className="text-slate-400 text-xs text-center mt-8">暂无会话，点击上方新建</p>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className={`group relative flex items-center rounded-lg mb-1 cursor-pointer transition-colors ${
                currentSessionId === session.id
                  ? 'bg-[#1e3a5f] text-white'
                  : 'text-slate-300 hover:bg-[#1a2f50]'
              }`}
              onClick={() => onSelectSession(session.id)}
              onDoubleClick={() => handleDoubleClick(session)}
              onMouseEnter={() => setHoveredId(session.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              {editingId === session.id ? (
                <input
                  className="flex-1 bg-[#16213e] text-white text-sm px-3 py-2 rounded-lg outline-none border border-blue-500"
                  value={editTitle}
                  autoFocus
                  onChange={(e) => setEditTitle(e.target.value)}
                  onBlur={() => handleRenameSubmit(session.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRenameSubmit(session.id)
                    if (e.key === 'Escape') setEditingId(null)
                  }}
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <>
                  <span className="flex-1 px-3 py-2 text-sm truncate">{session.title}</span>
                  {hoveredId === session.id && (
                    <button
                      className="mr-2 p-1 text-slate-400 hover:text-red-400 transition-colors"
                      onClick={(e) => {
                        e.stopPropagation()
                        onDeleteSession(session.id)
                      }}
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-[#1e3a5f]">
        {user?.role === 'admin' && (
          <button
            onClick={() => navigate('/admin')}
            className="w-full flex items-center gap-2 text-slate-300 hover:text-white hover:bg-[#1e3a5f] px-3 py-2 rounded-lg text-sm transition-colors mb-1"
          >
            <Shield size={14} />
            用户管理
          </button>
        )}
        <div className="flex items-center justify-between px-3 py-2">
          <span className="text-slate-300 text-sm truncate">
            {user?.username}
            {user?.role === 'admin' && (
              <span className="ml-1 text-xs text-yellow-400">(管理员)</span>
            )}
          </span>
          <button
            onClick={logout}
            className="text-slate-400 hover:text-red-400 transition-colors"
            title="退出登录"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}
