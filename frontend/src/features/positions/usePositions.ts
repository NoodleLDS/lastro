import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet, apiPost } from '@/lib/api'

const totalReturnSchema = z.object({
  invested_cents: z.number(),
  current_value_cents: z.number(),
  price_appreciation_cents: z.number(),
  dividends_received_cents: z.number(),
  realized_gain_cents: z.number(),
  total_return_cents: z.number(),
  total_return_pct: z.number(),
})

const positionSchema = z.object({
  id: z.number(),
  ticker: z.string(),
  name: z.string(),
  asset_type: z.string(),
  quantity: z.number(),
  is_active: z.boolean(),
  average_price_cents: z.number(),
  last_price_cents: z.number().nullable(),
  last_price_fetched_at: z.string().nullable(),
  price_earnings: z.number().nullable(),
  earnings_per_share: z.number().nullable(),
  total_return: totalReturnSchema.nullable(),
})

export type Position = z.infer<typeof positionSchema>

const positionsSchema = z.array(positionSchema)

export function usePositions() {
  return useQuery({
    queryKey: ['positions'],
    queryFn: async () => positionsSchema.parse(await apiGet('/positions')),
  })
}

export function useRefreshQuotes() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => positionsSchema.parse(await apiPost('/positions/refresh-quotes', {})),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['positions'] }),
  })
}
