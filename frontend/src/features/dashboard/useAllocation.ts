import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet } from '@/lib/api'

const allocationBreakdownSchema = z.object({
  asset_type: z.string(),
  current_value_cents: z.number(),
  current_percentage: z.number(),
  target_percentage: z.number().nullable(),
  deviation_pct: z.number().nullable(),
  is_deviation_alert: z.boolean(),
})

export type AllocationBreakdown = z.infer<typeof allocationBreakdownSchema>

const allocationSchema = z.array(allocationBreakdownSchema)

export function useAllocation() {
  return useQuery({
    queryKey: ['dashboard', 'allocation'],
    queryFn: async () => allocationSchema.parse(await apiGet('/dashboard/allocation')),
  })
}
