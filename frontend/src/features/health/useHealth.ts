import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet } from '@/lib/api'

const healthSchema = z.object({ status: z.string() })

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => healthSchema.parse(await apiGet('/health')),
  })
}
