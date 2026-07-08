import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { formatCents } from '@/lib/format'
import { PositionsTable } from './PositionsTable'
import type { Position } from './usePositions'

const mockPositions: Position[] = [
  {
    id: 1,
    ticker: 'ITSA4',
    name: 'Itaúsa',
    asset_type: 'stock',
    quantity: 100,
    is_active: true,
    average_price_cents: 1000,
    last_price_cents: 1200,
    last_price_fetched_at: null,
    price_earnings: null,
    earnings_per_share: null,
    target_yield_pct: null,
    total_return: null,
    valuation: null,
  },
  {
    id: 2,
    ticker: 'BBAS3',
    name: 'Banco do Brasil',
    asset_type: 'stock',
    quantity: 50,
    is_active: true,
    average_price_cents: 2000,
    last_price_cents: 2500,
    last_price_fetched_at: null,
    price_earnings: null,
    earnings_per_share: null,
    target_yield_pct: null,
    total_return: null,
    valuation: null,
  },
  {
    id: 3,
    ticker: 'HGLG11',
    name: 'CSHG Logística',
    asset_type: 'fii',
    quantity: 20,
    is_active: true,
    average_price_cents: 15000,
    last_price_cents: 16000,
    last_price_fetched_at: null,
    price_earnings: null,
    earnings_per_share: null,
    target_yield_pct: null,
    total_return: null,
    valuation: null,
  },
]

vi.mock('./usePositions', () => ({
  usePositions: () => ({ data: mockPositions, isLoading: false }),
  useRefreshQuotes: () => ({ mutate: vi.fn(), isPending: false, isError: false }),
}))

describe('PositionsTable', () => {
  function byExactText(text: string) {
    return (_: string, element: Element | null) => element?.textContent === text
  }

  it('mostra o valor total (quantidade × preço atual) de cada posição', () => {
    render(<PositionsTable />)

    // ITSA4: 100 * 1200 = 120000 centavos
    expect(screen.getAllByText(byExactText(formatCents(120_000))).length).toBeGreaterThan(0)
    // BBAS3: 50 * 2500 = 125000 centavos
    expect(screen.getAllByText(byExactText(formatCents(125_000))).length).toBeGreaterThan(0)
    // HGLG11: 20 * 16000 = 320000 centavos
    expect(screen.getAllByText(byExactText(formatCents(320_000))).length).toBeGreaterThan(0)
  })

  it('soma o total por tipo de ativo', () => {
    render(<PositionsTable />)

    expect(screen.getByText('Total Ações')).toBeInTheDocument()
    expect(screen.getByText('Total FIIs')).toBeInTheDocument()

    // Ações: 120000 + 125000 = 245000 centavos
    expect(screen.getAllByText(byExactText(formatCents(245_000))).length).toBeGreaterThan(0)
  })
})
