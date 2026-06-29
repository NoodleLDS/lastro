import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet } from '@/lib/api'

const memorySchema = z.object({
  master_prompt: z.string(),
  portfolio_context: z.string(),
})

export function useAnalystMemory(enabled: boolean) {
  return useQuery({
    queryKey: ['analyst', 'memory'],
    queryFn: async () => memorySchema.parse(await apiGet('/analyst/memory')),
    enabled,
  })
}
