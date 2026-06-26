import { createContext, type ReactNode, useContext, useEffect, useState } from 'react'
import { THEME_VARIABLES, type ThemeName, themes } from './themes'

const STORAGE_KEY = 'lastro-theme'

interface ThemeContextValue {
  theme: ThemeName
  setTheme: (theme: ThemeName) => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

function applyTheme(theme: ThemeName) {
  const palette = themes[theme]
  for (const variable of THEME_VARIABLES) {
    document.documentElement.style.setProperty(`--${variable}`, palette[variable])
  }
}

function readStoredTheme(): ThemeName {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'warm' || stored === 'matrix' || stored === 'hotline-miami') {
    return stored
  }
  return 'warm'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeName>(readStoredTheme)

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  function setTheme(next: ThemeName) {
    localStorage.setItem(STORAGE_KEY, next)
    setThemeState(next)
  }

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme deve ser usado dentro de ThemeProvider')
  }
  return context
}
