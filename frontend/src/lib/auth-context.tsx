import { createContext, type ReactNode, useContext, useState } from 'react'
import { apiPost, clearToken, getToken, setToken } from '@/lib/api'

interface LoginResponse {
  access_token: string
  token_type: string
}

interface AuthContextValue {
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => getToken() !== null)

  async function login(username: string, password: string): Promise<boolean> {
    try {
      const response = await apiPost<LoginResponse>('/auth/login', { username, password })
      setToken(response.access_token)
      setIsAuthenticated(true)
      return true
    } catch {
      return false
    }
  }

  function logout(): void {
    clearToken()
    setIsAuthenticated(false)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider')
  }
  return context
}
