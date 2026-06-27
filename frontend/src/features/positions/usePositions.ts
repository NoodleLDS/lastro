import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet, apiPatch, apiPost } from '@/lib/api'

const totalReturnSchema = z.object({
  invested_cents: z.number(),
  current_value_cents: z.number(),
  price_appreciation_cents: z.number(),
  dividends_received_cents: z.number(),
  realized_gain_cents: z.number(),
  total_return_cents: z.number(),
  total_return_pct: z.number(),
})

const valuationSchema = z.object({
  dividends_last_12m_cents: z.number(),
  price_ceiling_cents: z.number(),
  margin_of_safety_pct: z.number(),
  is_undervalued: z.boolean(),
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
  target_yield_pct: z.number().nullable(),
  total_return: totalReturnSchema.nullable(),
  valuation: valuationSchema.nullable(),
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

export function useCreatePosition() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { ticker: string; name: string; asset_type: string }) =>
      positionSchema.parse(await apiPost('/positions', input)),
    onSuccess: (position) => {
      queryClient.setQueryData<Position[]>(['positions'], (old) => [...(old ?? []), position])
      queryClient.invalidateQueries({ queryKey: ['positions'] })
    },
  })
}

export function useUpdateTargetYield() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, targetYieldPct }: { id: number; targetYieldPct: number | null }) =>
      positionSchema.parse(
        await apiPatch(`/positions/${id}`, { target_yield_pct: targetYieldPct }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['positions'] }),
  })
}
