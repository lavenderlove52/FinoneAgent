export interface User {
  id: number
  username: string
  role: string
  created_at?: string
}

export interface Session {
  id: number
  user_id: number
  title: string
  created_at: string
  updated_at: string
}

export interface Message {
  id: number
  session_id: number
  user_id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}
