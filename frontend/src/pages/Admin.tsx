import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Trash2, UserPlus, ArrowLeft, X } from 'lucide-react'
import type { User } from '../api/types'
import { createUser, deleteUser, listUsers } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

export default function Admin() {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState({ username: '', password: '', role: 'user' })
  const [formError, setFormError] = useState('')
  const [formLoading, setFormLoading] = useState(false)

  const refresh = async () => {
    setLoading(true)
    try {
      const data = await listUsers()
      setUsers(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  const handleDelete = async (userId: number) => {
    if (!window.confirm('确认删除该用户？')) return
    await deleteUser(userId)
    setUsers((prev) => prev.filter((u) => u.id !== userId))
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')
    if (!form.username.trim() || !form.password.trim()) {
      setFormError('用户名和密码不能为空')
      return
    }
    setFormLoading(true)
    try {
      const newUser = await createUser(form.username, form.password, form.role)
      setUsers((prev) => [...prev, newUser])
      setShowModal(false)
      setForm({ username: '', password: '', role: 'user' })
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setFormError(detail ?? '创建失败')
    } finally {
      setFormLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#1a1a2e] text-slate-200">
      {/* Top Nav */}
      <div className="bg-[#0f3460] border-b border-[#1e3a5f] px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/chat"
            className="flex items-center gap-1.5 text-slate-300 hover:text-white text-sm transition-colors"
          >
            <ArrowLeft size={16} />
            返回聊天
          </Link>
          <h1 className="text-white font-semibold">用户管理</h1>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <UserPlus size={15} />
          创建用户
        </button>
      </div>

      {/* Table */}
      <div className="p-6">
        <div className="bg-[#16213e] rounded-xl border border-[#1e3a5f] overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-slate-500">加载中...</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#1e3a5f]">
                  <th className="text-left px-6 py-3 text-slate-400 font-medium">ID</th>
                  <th className="text-left px-6 py-3 text-slate-400 font-medium">用户名</th>
                  <th className="text-left px-6 py-3 text-slate-400 font-medium">角色</th>
                  <th className="text-left px-6 py-3 text-slate-400 font-medium">创建时间</th>
                  <th className="px-6 py-3 text-slate-400 font-medium text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-[#1e3a5f] hover:bg-[#1e3a5f]/30 transition-colors">
                    <td className="px-6 py-3 text-slate-400">{u.id}</td>
                    <td className="px-6 py-3 text-white font-medium">{u.username}</td>
                    <td className="px-6 py-3">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          u.role === 'admin'
                            ? 'bg-yellow-900/40 text-yellow-400 border border-yellow-700'
                            : 'bg-blue-900/40 text-blue-400 border border-blue-700'
                        }`}
                      >
                        {u.role === 'admin' ? '管理员' : '普通用户'}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-slate-400">{u.created_at}</td>
                    <td className="px-6 py-3 text-right">
                      {u.id !== currentUser?.id && (
                        <button
                          onClick={() => handleDelete(u.id)}
                          className="text-slate-400 hover:text-red-400 transition-colors p-1"
                          title="删除用户"
                        >
                          <Trash2 size={15} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
          <div className="bg-[#16213e] rounded-2xl p-6 w-full max-w-sm border border-[#1e3a5f] shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-white font-semibold">创建用户</h3>
              <button
                onClick={() => {
                  setShowModal(false)
                  setFormError('')
                  setForm({ username: '', password: '', role: 'user' })
                }}
                className="text-slate-400 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm text-slate-300 mb-1.5">用户名</label>
                <input
                  type="text"
                  value={form.username}
                  onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                  className="w-full bg-[#0f3460] text-white border border-[#1e3a5f] rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-500 transition-colors"
                  placeholder="用户名"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1.5">密码</label>
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                  className="w-full bg-[#0f3460] text-white border border-[#1e3a5f] rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-500 transition-colors"
                  placeholder="密码"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1.5">角色</label>
                <select
                  value={form.role}
                  onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}
                  className="w-full bg-[#0f3460] text-white border border-[#1e3a5f] rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-500 transition-colors"
                >
                  <option value="user">普通用户</option>
                  <option value="admin">管理员</option>
                </select>
              </div>
              {formError && (
                <div className="bg-red-900/30 border border-red-700 rounded-lg px-3 py-2 text-red-400 text-xs">
                  {formError}
                </div>
              )}
              <div className="flex gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false)
                    setFormError('')
                  }}
                  className="flex-1 bg-[#0f3460] hover:bg-[#1e3a5f] text-slate-300 py-2.5 rounded-lg text-sm transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={formLoading}
                  className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white py-2.5 rounded-lg text-sm transition-colors"
                >
                  {formLoading ? '创建中...' : '创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
