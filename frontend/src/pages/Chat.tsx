import React, { useCallback, useEffect, useState } from 'react'
import { Menu, X } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import ChatWindow from '../components/ChatWindow'
import type { Session } from '../api/types'
import {
  createSession,
  deleteSession,
  listSessions,
  updateSession,
} from '../api/client'

export default function Chat() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const currentSession = sessions.find((s) => s.id === currentSessionId) ?? null

  const refreshSessions = useCallback(async () => {
    const data = await listSessions()
    setSessions(data)
  }, [])

  useEffect(() => {
    refreshSessions()
  }, [refreshSessions])

  const handleNewSession = async () => {
    const session = await createSession()
    setSessions((prev) => [session, ...prev])
    setCurrentSessionId(session.id)
  }

  const handleDeleteSession = async (id: number) => {
    await deleteSession(id)
    setSessions((prev) => prev.filter((s) => s.id !== id))
    if (currentSessionId === id) {
      setCurrentSessionId(null)
    }
  }

  const handleRenameSession = async (id: number, title: string) => {
    const updated = await updateSession(id, title)
    setSessions((prev) => prev.map((s) => (s.id === id ? updated : s)))
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#1a1a2e]">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-10 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'flex' : 'hidden'
        } md:flex fixed md:relative inset-y-0 left-0 z-20 md:z-auto`}
      >
        <Sidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={(id) => {
            setCurrentSessionId(id)
            setSidebarOpen(false)
          }}
          onNewSession={handleNewSession}
          onDeleteSession={handleDeleteSession}
          onRenameSession={handleRenameSession}
        />
      </div>

      {/* Main Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-0">
        {/* Mobile header toggle */}
        <div className="md:hidden flex items-center px-4 py-3 border-b border-[#1e3a5f] bg-[#16213e]">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-slate-400 hover:text-white transition-colors"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <span className="ml-3 text-white font-medium">
            {currentSession?.title ?? 'FinoneAgent'}
          </span>
        </div>

        <ChatWindow session={currentSession} onSessionUpdated={refreshSessions} />
      </div>
    </div>
  )
}
