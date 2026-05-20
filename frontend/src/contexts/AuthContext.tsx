import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { User } from '../api/types'
import { getMe } from '../api/client'

interface AuthContextValue {
  user: User | null
  token: string | null
  login: (token: string, user: User) => void
  logout: () => void
  isAuthenticated: boolean
  /** true 表示正在校验 localStorage 中的 Token，此时不应渲染路由 */
  initializing: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [initializing, setInitializing] = useState(true)

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
  }, [])

  const login = useCallback((newToken: string, newUser: User) => {
    localStorage.setItem('token', newToken)
    localStorage.setItem('user', JSON.stringify(newUser))
    setToken(newToken)
    setUser(newUser)
  }, [])

  // 启动时用 /api/auth/me 校验 localStorage 中的 Token 是否仍有效
  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    if (!storedToken) {
      setInitializing(false)
      return
    }
    setToken(storedToken)
    getMe()
      .then((me) => {
        setUser(me)
      })
      .catch(() => {
        // Token 无效或过期，清除本地存储
        logout()
      })
      .finally(() => {
        setInitializing(false)
      })
  }, [logout])

  return (
    <AuthContext.Provider
      value={{ user, token, login, logout, isAuthenticated: !!token, initializing }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
