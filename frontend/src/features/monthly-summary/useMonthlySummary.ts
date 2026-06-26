import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet } from '@/lib/api'

const cardSpendingSchema = z.object({
  card_id: z.number(),
  card_name: z.string(),
  total_cents: z.number(),
})

const monthlySummarySchema = z.object({
  year: z.number(),
  month: z.number(),
  income_total_cents: z.number(),
  fixed_expense_total_cents: z.number(),
  variable_expense_total_cents: z.number(),
  card_spending: z.array(cardSpendingSchema),
  card_spending_total_cents: z.number(),
  balance_cents: z.number(),
})

export type MonthlySummary = z.infer<typeof monthlySummarySchema>

export function useMonthlySummary(year: number, month: number) {
  return useQuery({
    queryKey: ['monthly-summary', year, month],
    queryFn: async () =>
      monthlySummarySchema.parse(await apiGet(`/monthly-summary?year=${year}&month=${month}`)),
  })
}
