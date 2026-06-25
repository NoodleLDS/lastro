import { useMutation } from '@tanstack/react-query'
import { z } from 'zod'
import { apiPost } from '@/lib/api'

const askAnalystResponseSchema = z.object({
  answer: z.string(),
})

export function useAskAnalyst() {
  return useMutation({
    mutationFn: async (question: string) =>
      askAnalystResponseSchema.parse(await apiPost('/analyst/ask', { question })),
  })
}
