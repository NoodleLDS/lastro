import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiDelete, apiGet, apiPatch, apiPost } from '@/lib/api'

const fixedExpenseSchema = z.object({
  id: z.number(),
  description: z.string(),
  amount_cents: z.number(),
  year: z.number(),
  month: z.number(),
  category_id: z.number().nullable(),
})

export type FixedExpense = z.infer<typeof fixedExpenseSchema>

const fixedExpensesSchema = z.array(fixedExpenseSchema)

export function useFixedExpenses(year: number, month: number) {
  return useQuery({
    queryKey: ['fixed-expenses', year, month],
    queryFn: async () =>
      fixedExpensesSchema.parse(await apiGet(`/fixed-expenses?year=${year}&month=${month}`)),
  })
}

export function useCreateFixedExpense() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: {
      description: string
      amount_cents: number
      year: number
      month: number
      category_id?: number
    }) => fixedExpenseSchema.parse(await apiPost('/fixed-expenses', input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['fixed-expenses'] }),
  })
}

export function useUpdateFixedExpense() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      id,
      ...input
    }: {
      id: number
      description?: string
      amount_cents?: number
      category_id?: number
    }) => fixedExpenseSchema.parse(await apiPatch(`/fixed-expenses/${id}`, input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['fixed-expenses'] }),
  })
}

export function useDeleteFixedExpense() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => apiDelete(`/fixed-expenses/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['fixed-expenses'] }),
  })
}
