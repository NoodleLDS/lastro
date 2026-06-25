import { useMutation } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet } from '@/lib/api'

const projectionResponseSchema = z.object({
  values_cents: z.array(z.number()),
})

export function useProjection() {
  return useMutation({
    mutationFn: async (input: {
      monthly_contribution_cents: number
      monthly_return_rate: number
      months: number
    }) => {
      const params = new URLSearchParams({
        monthly_contribution_cents: String(input.monthly_contribution_cents),
        monthly_return_rate: String(input.monthly_return_rate),
        months: String(input.months),
      })
      return projectionResponseSchema.parse(await apiGet(`/dashboard/projection?${params}`))
    },
  })
}
