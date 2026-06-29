import { useMutation } from '@tanstack/react-query'
import { z } from 'zod'
import { apiPost } from '@/lib/api'

const askAnalystResponseSchema = z.object({
  answer: z.string(),
  conversation_id: z.number(),
})

export function useAskAnalyst() {
  return useMutation({
    mutationFn: async ({
      question,
      conversationId,
    }: {
      question: string
      conversationId: number | null
    }) =>
      askAnalystResponseSchema.parse(
        await apiPost('/analyst/ask', { question, conversation_id: conversationId }),
      ),
  })
}
