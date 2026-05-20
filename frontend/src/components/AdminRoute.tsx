import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user, initializing } = useAuth()
  if (initializing) return null  // 等待 /me 校验完成，避免闪跳
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (user?.role !== 'admin') return <Navigate to="/chat" replace />
  return <>{children}</>
}
