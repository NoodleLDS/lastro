import { useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiPost } from '@/lib/api'

const contributionSchema = z.object({
  id: z.number(),
  position_id: z.number(),
  date: z.string(),
  quantity: z.number(),
  unit_price_cents: z.number(),
})

export function useCreateContribution() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: {
      position_id: number
      date: string
      quantity: number
      unit_price_cents: number
    }) => contributionSchema.parse(await apiPost('/contributions', input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['positions'] }),
  })
}
