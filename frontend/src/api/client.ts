import axios from 'axios'
import type { LoginResponse, Message, Session, User } from './types'

export const AUTH_UNAUTHORIZED_EVENT = 'auth:unauthorized'

const api = axios.create({
  baseURL: '',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')

      // 交给路由层做 SPA 跳转，避免整页刷新回到登录页。
      if (err.config?.url !== '/api/auth/login') {
        window.dispatchEvent(new CustomEvent(AUTH_UNAUTHORIZED_EVENT))
      }
    }
    return Promise.reject(err)
  }
)

// Auth
export const login = (username: string, password: string) =>
  api.post<LoginResponse>('/api/auth/login', { username, password }).then((r) => r.data)

export const getMe = () =>
  api.get<User>('/api/auth/me').then((r) => r.data)

// Users (admin)
export const listUsers = () =>
  api.get<User[]>('/api/users').then((r) => r.data)

export const createUser = (username: string, password: string, role: string) =>
  api.post<User>('/api/users', { username, password, role }).then((r) => r.data)

export const deleteUser = (userId: number) =>
  api.delete(`/api/users/${userId}`)

// Sessions
export const listSessions = () =>
  api.get<Session[]>('/api/sessions').then((r) => r.data)

export const createSession = (title?: string) =>
  api.post<Session>('/api/sessions', { title: title ?? '新会话' }).then((r) => r.data)

export const updateSession = (sessionId: number, title: string) =>
  api.patch<Session>(`/api/sessions/${sessionId}`, { title }).then((r) => r.data)

export const deleteSession = (sessionId: number) =>
  api.delete(`/api/sessions/${sessionId}`)

export const listMessages = (sessionId: number) =>
  api.get<Message[]>(`/api/sessions/${sessionId}/messages`).then((r) => r.data)

export default api
