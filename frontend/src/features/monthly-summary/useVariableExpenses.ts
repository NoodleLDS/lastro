import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiDelete, apiGet, apiPatch, apiPost } from '@/lib/api'

const variableExpenseSchema = z.object({
  id: z.number(),
  description: z.string(),
  amount_cents: z.number(),
  year: z.number(),
  month: z.number(),
  category_id: z.number().nullable(),
})

export type VariableExpense = z.infer<typeof variableExpenseSchema>

const variableExpensesSchema = z.array(variableExpenseSchema)

export function useVariableExpenses(year: number, month: number) {
  return useQuery({
    queryKey: ['variable-expenses', year, month],
    queryFn: async () =>
      variableExpensesSchema.parse(await apiGet(`/variable-expenses?year=${year}&month=${month}`)),
  })
}

export function useCreateVariableExpense() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: {
      description: string
      amount_cents: number
      year: number
      month: number
      category_id?: number
    }) => variableExpenseSchema.parse(await apiPost('/variable-expenses', input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['variable-expenses'] }),
  })
}

export function useUpdateVariableExpense() {
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
    }) => variableExpenseSchema.parse(await apiPatch(`/variable-expenses/${id}`, input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['variable-expenses'] }),
  })
}

export function useDeleteVariableExpense() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => apiDelete(`/variable-expenses/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['variable-expenses'] }),
  })
}
