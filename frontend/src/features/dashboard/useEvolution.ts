import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet, apiPost } from '@/lib/api'

const evolutionPointSchema = z.object({
  month: z.string(),
  portfolio_value_cents: z.number(),
})

const benchmarkComparisonSchema = z.object({
  portfolio_return_pct: z.number(),
  cdi_return_pct: z.number(),
  ivvb11_return_pct: z.number().nullable(),
})

const evolutionResponseSchema = z.object({
  points: z.array(evolutionPointSchema),
  comparison: benchmarkComparisonSchema.nullable(),
})

export type EvolutionResponse = z.infer<typeof evolutionResponseSchema>

export function useEvolution() {
  return useQuery({
    queryKey: ['dashboard', 'evolution'],
    queryFn: async () => evolutionResponseSchema.parse(await apiGet('/dashboard/evolution')),
  })
}

export function useCreateSnapshot() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => apiPost('/snapshots', {}),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['dashboard', 'evolution'] }),
  })
}
