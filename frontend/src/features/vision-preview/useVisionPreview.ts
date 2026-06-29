import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet, apiPatch, apiPost, apiUpload } from '@/lib/api'

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

export type PreviewTransaction = z.infer<typeof transactionSchema>

const transactionsSchema = z.array(transactionSchema)

export function usePendingReview(cardId: number | null) {
  return useQuery({
    queryKey: ['transactions', 'pending_review', cardId],
    queryFn: async () =>
      transactionsSchema.parse(
        await apiGet(`/transactions?card_id=${cardId}&status=pending_review`),
      ),
    enabled: cardId !== null,
  })
}

export function useUploadVisionPreview() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      cardId,
      file,
      referenceYear,
      referenceMonth,
    }: {
      cardId: number
      file: File
      referenceYear: number
      referenceMonth: number
    }) => {
      const formData = new FormData()
      formData.append('file', file)
      const params = new URLSearchParams({
        card_id: String(cardId),
        reference_year: String(referenceYear),
        reference_month: String(referenceMonth),
      })
      return transactionsSchema.parse(
        await apiUpload(`/transactions/vision-preview?${params}`, formData),
      )
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transactions'] }),
  })
}

export function useUpdatePreviewTransaction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      id,
      ...input
    }: {
      id: number
      description?: string
      amount_cents?: number
      category_id?: number | null
    }) => transactionSchema.parse(await apiPatch(`/transactions/${id}`, input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transactions'] }),
  })
}

export function useConfirmBatch() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (ids: number[]) =>
      transactionsSchema.parse(await apiPost('/transactions/confirm-batch', { ids })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transactions'] }),
  })
}
