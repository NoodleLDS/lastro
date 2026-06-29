import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet, apiPut } from '@/lib/api'

const instructionsSchema = z.object({
  content: z.string(),
})

export function useAnalystInstructions() {
  return useQuery({
    queryKey: ['analyst', 'instructions'],
    queryFn: async () => instructionsSchema.parse(await apiGet('/analyst/instructions')),
  })
}

export function useUpdateAnalystInstructions() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (content: string) =>
      instructionsSchema.parse(await apiPut('/analyst/instructions', { content })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['analyst', 'instructions'] }),
  })
}
