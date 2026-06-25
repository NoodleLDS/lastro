import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiDelete, apiGet, apiPost, apiPut } from '@/lib/api'

const cardSchema = z.object({
  id: z.number(),
  name: z.string(),
  color: z.string(),
  closing_day: z.number().nullable(),
  is_active: z.boolean(),
})

export type Card = z.infer<typeof cardSchema>

const cardsSchema = z.array(cardSchema)

export function useCards() {
  return useQuery({
    queryKey: ['cards'],
    queryFn: async () => cardsSchema.parse(await apiGet('/cards')),
  })
}

export function useCreateCard() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { name: string; color?: string }) =>
      cardSchema.parse(await apiPost('/cards', input)),
    onMutate: async (input) => {
      await queryClient.cancelQueries({ queryKey: ['cards'] })
      const previousCards = queryClient.getQueryData<Card[]>(['cards'])
      const optimisticCard: Card = {
        id: -Date.now(),
        name: input.name,
        color: input.color ?? '#c084fc',
        closing_day: null,
        is_active: true,
      }
      queryClient.setQueryData<Card[]>(['cards'], (old) => [...(old ?? []), optimisticCard])
      return { previousCards }
    },
    onError: (_err, _input, context) => {
      if (context?.previousCards) {
        queryClient.setQueryData(['cards'], context.previousCards)
      }
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['cards'] }),
  })
}

export function useUpdateCard() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      id,
      ...input
    }: {
      id: number
      name?: string
      color?: string
      closing_day?: number | null
    }) => cardSchema.parse(await apiPut(`/cards/${id}`, input)),
    onMutate: async ({ id, ...input }) => {
      await queryClient.cancelQueries({ queryKey: ['cards'] })
      const previousCards = queryClient.getQueryData<Card[]>(['cards'])
      queryClient.setQueryData<Card[]>(['cards'], (old) =>
        old?.map((card) => (card.id === id ? { ...card, ...input } : card)),
      )
      return { previousCards }
    },
    onError: (_err, _input, context) => {
      if (context?.previousCards) {
        queryClient.setQueryData(['cards'], context.previousCards)
      }
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['cards'] }),
  })
}

export function useDeactivateCard() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => apiDelete(`/cards/${id}`),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ['cards'] })
      const previousCards = queryClient.getQueryData<Card[]>(['cards'])
      queryClient.setQueryData<Card[]>(['cards'], (old) =>
        old?.map((card) => (card.id === id ? { ...card, is_active: false } : card)),
      )
      return { previousCards }
    },
    onError: (_err, _id, context) => {
      if (context?.previousCards) {
        queryClient.setQueryData(['cards'], context.previousCards)
      }
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['cards'] }),
  })
}
