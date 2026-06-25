import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet } from '@/lib/api'

const transactionSchema = z.object({
  id: z.number(),
  date: z.string(),
  description: z.string(),
  amount_cents: z.number(),
  card_id: z.number(),
  category_id: z.number().nullable(),
  categorized_by: z.string(),
  source: z.string(),
  status: z.string(),
  installment_current: z.number().nullable(),
  installment_total: z.number().nullable(),
  parent_id: z.number().nullable(),
})

export type Transaction = z.infer<typeof transactionSchema>

const transactionsSchema = z.array(transactionSchema)

export interface TransactionFilters {
  search?: string
  categoryId?: number
  cardId?: number
  dateFrom?: string
  dateTo?: string
}

function buildQueryString(filters: TransactionFilters): string {
  const params = new URLSearchParams()
  if (filters.search && filters.search.trim() !== '') {
    params.set('search', filters.search.trim())
  }
  if (filters.categoryId !== undefined) {
    params.set('category_id', String(filters.categoryId))
  }
  if (filters.cardId !== undefined) {
    params.set('card_id', String(filters.cardId))
  }
  if (filters.dateFrom) {
    params.set('date_from', filters.dateFrom)
  }
  if (filters.dateTo) {
    params.set('date_to', filters.dateTo)
  }
  const query = params.toString()
  return query ? `?${query}` : ''
}

export function useTransactions(filters: TransactionFilters = {}) {
  return useQuery({
    queryKey: ['transactions', filters],
    queryFn: async () =>
      transactionsSchema.parse(await apiGet(`/transactions${buildQueryString(filters)}`)),
  })
}
