import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet } from '@/lib/api'

const positionEventSchema = z.object({
  type: z.enum(['contribution', 'sale', 'dividend', 'stock_split']),
  date: z.string(),
  quantity: z.number().nullable(),
  unit_price_cents: z.number().nullable(),
  amount_cents: z.number().nullable(),
  ratio_from: z.number().nullable().optional(),
  ratio_to: z.number().nullable().optional(),
})

const pricePointSchema = z.object({
  date: z.string(),
  price_cents: z.number(),
})

const positionHistorySchema = z.object({
  events: z.array(positionEventSchema),
  price_history: z.array(pricePointSchema),
})

export type PositionEvent = z.infer<typeof positionEventSchema>
export type PositionHistory = z.infer<typeof positionHistorySchema>

export function usePositionHistory(positionId: number | null) {
  return useQuery({
    queryKey: ['positions', positionId, 'history'],
    queryFn: async () =>
      positionHistorySchema.parse(await apiGet(`/positions/${positionId}/history`)),
    enabled: positionId !== null,
  })
}
