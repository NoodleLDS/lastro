import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiDelete, apiGet, apiPatch } from '@/lib/api'

const conversationSchema = z.object({
  id: z.number(),
  title: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type Conversation = z.infer<typeof conversationSchema>

const conversationsSchema = z.array(conversationSchema)

const messageSchema = z.object({
  id: z.number(),
  conversation_id: z.number(),
  role: z.enum(['user', 'assistant']),
  content: z.string(),
  model: z.string().nullable(),
  tokens_per_second: z.number().nullable(),
  created_at: z.string(),
})

export type ConversationMessage = z.infer<typeof messageSchema>

const messagesSchema = z.array(messageSchema)

export function useConversations() {
  return useQuery({
    queryKey: ['analyst', 'conversations'],
    queryFn: async () => conversationsSchema.parse(await apiGet('/analyst/conversations')),
  })
}

export function useConversationMessages(conversationId: number | null) {
  return useQuery({
    queryKey: ['analyst', 'conversations', conversationId, 'messages'],
    queryFn: async () =>
      messagesSchema.parse(await apiGet(`/analyst/conversations/${conversationId}/messages`)),
    enabled: conversationId !== null,
  })
}

export function useRenameConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, title }: { id: number; title: string }) =>
      conversationSchema.parse(await apiPatch(`/analyst/conversations/${id}`, { title })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['analyst', 'conversations'] }),
  })
}

export function useDeleteConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => apiDelete(`/analyst/conversations/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['analyst', 'conversations'] }),
  })
}
