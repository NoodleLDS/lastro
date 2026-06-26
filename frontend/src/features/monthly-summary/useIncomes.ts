import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiDelete, apiGet, apiPatch, apiPost } from '@/lib/api'

const incomeSchema = z.object({
  id: z.number(),
  description: z.string(),
  amount_cents: z.number(),
  year: z.number(),
  month: z.number(),
})

export type Income = z.infer<typeof incomeSchema>

const incomesSchema = z.array(incomeSchema)

export function useIncomes(year: number, month: number) {
  return useQuery({
    queryKey: ['incomes', year, month],
    queryFn: async () => incomesSchema.parse(await apiGet(`/incomes?year=${year}&month=${month}`)),
  })
}

export function useCreateIncome() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: {
      description: string
      amount_cents: number
      year: number
      month: number
    }) => incomeSchema.parse(await apiPost('/incomes', input)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomes'] })
      queryClient.invalidateQueries({ queryKey: ['monthly-summary'] })
    },
  })
}

export function useUpdateIncome() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      id,
      ...input
    }: {
      id: number
      description?: string
      amount_cents?: number
    }) => incomeSchema.parse(await apiPatch(`/incomes/${id}`, input)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomes'] })
      queryClient.invalidateQueries({ queryKey: ['monthly-summary'] })
    },
  })
}

export function useDeleteIncome() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => apiDelete(`/incomes/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomes'] })
      queryClient.invalidateQueries({ queryKey: ['monthly-summary'] })
    },
  })
}
