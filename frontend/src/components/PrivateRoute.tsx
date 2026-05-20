import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, initializing } = useAuth()
  if (initializing) return null  // 等待 /me 校验完成，避免闪跳
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}
