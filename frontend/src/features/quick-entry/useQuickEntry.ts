import { useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiPost } from '@/lib/api'

const transactionSchema = z.object({
  id: z.number(),
  date: z.string(),
  description: z.string(),
  amount_cents: z.number(),
  card_id: z.number(),
  category_id: z.number().nullable(),
  source: z.string(),
  status: z.string(),
  installment_current: z.number().nullable(),
  installment_total: z.number().nullable(),
  parent_id: z.number().nullable(),
})

const quickEntryResultSchema = z.object({
  transaction: transactionSchema,
  installments: z.array(transactionSchema),
})

export type QuickEntryResult = z.infer<typeof quickEntryResultSchema>

export function useQuickEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { card_id: number; raw: string; date: string }) =>
      quickEntryResultSchema.parse(await apiPost('/transactions/quick-entry', input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transactions'] }),
  })
}
