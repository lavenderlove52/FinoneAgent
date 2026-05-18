import React, { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { AUTH_UNAUTHORIZED_EVENT } from './api/client'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import PrivateRoute from './components/PrivateRoute'
import AdminRoute from './components/AdminRoute'
import Login from './pages/Login'
import Chat from './pages/Chat'
import Admin from './pages/Admin'

function AuthRedirectHandler() {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout } = useAuth()

  useEffect(() => {
    const handleUnauthorized = () => {
      logout()
      if (location.pathname !== '/login') {
        navigate('/login', { replace: true })
      }
    }

    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized)
    return () => window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized)
  }, [location.pathname, logout, navigate])

  return null
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AuthRedirectHandler />
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/chat"
            element={
              <PrivateRoute>
                <Chat />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <Admin />
              </AdminRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
