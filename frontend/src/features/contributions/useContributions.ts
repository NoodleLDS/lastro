import { useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import type { Position } from '@/features/positions/usePositions'
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
    // Otimismo parcial: preço médio e total return dependem do histórico
    // completo de aportes/vendas, calculado no servidor. Replicar essa
    // lógica no cliente arriscaria divergir do back. Em vez disso,
    // atualizamos otimisticamente só a quantidade da posição (soma simples,
    // sempre correta) para a UI refletir o aporte instantaneamente; preço
    // médio e total return continuam vindo do servidor após o onSettled.
    onMutate: async (input) => {
      await queryClient.cancelQueries({ queryKey: ['positions'] })
      const previousPositions = queryClient.getQueryData<Position[]>(['positions'])
      queryClient.setQueryData<Position[]>(['positions'], (old) =>
        old?.map((position) =>
          position.id === input.position_id
            ? { ...position, quantity: position.quantity + input.quantity }
            : position,
        ),
      )
      return { previousPositions }
    },
    onError: (_err, _input, context) => {
      if (context?.previousPositions) {
        queryClient.setQueryData(['positions'], context.previousPositions)
      }
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['positions'] }),
  })
}
