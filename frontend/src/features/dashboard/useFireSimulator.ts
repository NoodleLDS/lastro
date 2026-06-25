import { useMutation } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet } from '@/lib/api'

const fireResultSchema = z.object({
  annualized_dividend_yield_pct: z.number(),
  safe_withdrawal_rate_pct: z.number(),
  sustainable_monthly_income_cents: z.number(),
  has_reached_target: z.boolean(),
  required_portfolio_cents: z.number().nullable(),
  missing_portfolio_cents: z.number().nullable(),
})

export type FireResult = z.infer<typeof fireResultSchema>

export function useFireSimulator() {
  return useMutation({
    mutationFn: async (input: { target_monthly_expense_cents: number }) => {
      const params = new URLSearchParams({
        target_monthly_expense_cents: String(input.target_monthly_expense_cents),
      })
      return fireResultSchema.parse(await apiGet(`/dashboard/fire-simulator?${params}`))
    },
  })
}
