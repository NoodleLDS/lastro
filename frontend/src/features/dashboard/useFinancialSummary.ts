import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet, apiPatch, apiPost } from '@/lib/api'

const monthlyTotalsSchema = z.object({
  year: z.number(),
  month: z.number(),
  income_total_cents: z.number(),
  expense_total_cents: z.number(),
  contribution_total_cents: z.number(),
  balance_cents: z.number(),
})

const yearlyTotalsSchema = z.object({
  year: z.number(),
  income_total_cents: z.number(),
  expense_total_cents: z.number(),
  balance_cents: z.number(),
})

const emergencyReserveSummarySchema = z.object({
  balance_cents: z.number(),
  average_monthly_expense_cents: z.number(),
  months_covered: z.number().nullable(),
})

const categoryCardBreakdownSchema = z.object({
  category_id: z.number().nullable(),
  category_name: z.string(),
  card_id: z.number(),
  card_name: z.string(),
  total_cents: z.number(),
})

const financialSummarySchema = z.object({
  monthly: monthlyTotalsSchema,
  yearly: yearlyTotalsSchema,
  emergency_reserve: emergencyReserveSummarySchema,
  category_card_breakdown: z.array(categoryCardBreakdownSchema),
})

export type FinancialSummary = z.infer<typeof financialSummarySchema>

export function useFinancialSummary(year: number, month: number) {
  return useQuery({
    queryKey: ['dashboard', 'financial-summary', year, month],
    queryFn: async () =>
      financialSummarySchema.parse(
        await apiGet(`/dashboard/financial-summary?year=${year}&month=${month}`),
      ),
  })
}

const emergencyReserveSchema = z.object({
  id: z.number(),
  institution: z.string(),
  balance_cents: z.number(),
  cdi_percentage: z.number(),
})

export function useEmergencyReserves() {
  return useQuery({
    queryKey: ['emergency-reserve'],
    queryFn: async () => z.array(emergencyReserveSchema).parse(await apiGet('/emergency-reserve')),
  })
}

export function useUpsertEmergencyReserve() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, balanceCents }: { id: number | null; balanceCents: number }) =>
      id === null
        ? apiPost('/emergency-reserve', {
            institution: 'Reserva de emergência',
            balance_cents: balanceCents,
            cdi_percentage: 100,
          })
        : apiPatch(`/emergency-reserve/${id}`, { balance_cents: balanceCents }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emergency-reserve'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'financial-summary'] })
    },
  })
}
