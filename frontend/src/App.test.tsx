import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'
import { ThemeProvider } from './lib/theme-context'

describe('App', () => {
  it('renderiza o título Lastro', () => {
    const queryClient = new QueryClient()
    render(
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <App />
        </QueryClientProvider>
      </ThemeProvider>,
    )

    expect(screen.getByText('Lastro')).toBeInTheDocument()
  })
})
