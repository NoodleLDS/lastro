import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiDelete, apiGetOrNull, apiPut } from '@/lib/api'

const cardInvoicePaymentSchema = z.object({
  card_id: z.number(),
  year: z.number(),
  month: z.number(),
  paid_at: z.string(),
})

export type CardInvoicePayment = z.infer<typeof cardInvoicePaymentSchema>

function invoicePaymentQueryKey(cardId: number, year: number, month: number) {
  return ['card-invoice-payment', cardId, year, month]
}

export function useCardInvoicePayment(cardId: number, year: number, month: number) {
  return useQuery({
    queryKey: invoicePaymentQueryKey(cardId, year, month),
    queryFn: async () => {
      const result = await apiGetOrNull(
        `/cards/${cardId}/invoice-payment?year=${year}&month=${month}`,
      )
      return result === null ? null : cardInvoicePaymentSchema.parse(result)
    },
  })
}

export function useMarkInvoicePaid() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ cardId, year, month }: { cardId: number; year: number; month: number }) =>
      cardInvoicePaymentSchema.parse(
        await apiPut(`/cards/${cardId}/invoice-payment?year=${year}&month=${month}`, {}),
      ),
    onSuccess: (_, { cardId, year, month }) => {
      queryClient.invalidateQueries({ queryKey: invoicePaymentQueryKey(cardId, year, month) })
      queryClient.invalidateQueries({ queryKey: ['monthly-summary'] })
    },
  })
}

export function useUnmarkInvoicePaid() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ cardId, year, month }: { cardId: number; year: number; month: number }) =>
      apiDelete(`/cards/${cardId}/invoice-payment?year=${year}&month=${month}`),
    onSuccess: (_, { cardId, year, month }) => {
      queryClient.invalidateQueries({ queryKey: invoicePaymentQueryKey(cardId, year, month) })
      queryClient.invalidateQueries({ queryKey: ['monthly-summary'] })
    },
  })
}
