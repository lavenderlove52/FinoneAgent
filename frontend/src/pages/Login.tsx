import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login as apiLogin } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login, isAuthenticated } = useAuth()

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/chat', { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password.trim()) return
    setError('')
    setLoading(true)
    try {
      const data = await apiLogin(username, password)
      login(data.access_token, data.user)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? '登录失败，请检查用户名和密码')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#1a1a2e] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">FinoneAgent</h1>
          <p className="text-slate-400 mt-2 text-sm">AI 知识库问答助手</p>
        </div>

        <div className="bg-[#16213e] rounded-2xl p-8 border border-[#1e3a5f] shadow-2xl">
          <h2 className="text-xl font-semibold text-white mb-6">登录账号</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-slate-300 mb-1.5">用户名</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-[#0f3460] text-white placeholder-slate-500 border border-[#1e3a5f] rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-500 transition-colors"
                placeholder="请输入用户名"
                autoFocus
                disabled={loading}
              />
            </div>

            <div>
              <label className="block text-sm text-slate-300 mb-1.5">密码</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#0f3460] text-white placeholder-slate-500 border border-[#1e3a5f] rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-500 transition-colors"
                placeholder="请输入密码"
                disabled={loading}
              />
            </div>

            {error && (
              <div className="bg-red-900/30 border border-red-700 rounded-lg px-4 py-2.5 text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !username.trim() || !password.trim()}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg text-sm transition-colors"
            >
              {loading ? '登录中...' : '登录'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
