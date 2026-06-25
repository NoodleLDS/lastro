import { useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiPost } from '@/lib/api'

const transactionSchema = z.object({
  id: z.number(),
  date: z.string(),
  description: z.string(),
  amount_cents: z.number(),
  card_id: z.number(),
  category_id: z.number().nullable(),
  source: z.string(),
  status: z.string(),
  installment_current: z.number().nullable(),
  installment_total: z.number().nullable(),
  parent_id: z.number().nullable(),
})

const quickEntryResultSchema = z.object({
  transaction: transactionSchema,
  installments: z.array(transactionSchema),
})

export type QuickEntryResult = z.infer<typeof quickEntryResultSchema>

export function useQuickEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { card_id: number; raw: string; date: string }) =>
      quickEntryResultSchema.parse(await apiPost('/transactions/quick-entry', input)),
    // Otimismo parcial: o servidor decide categoria e projeção de parcelas a
    // partir do texto cru (`raw`), então não há como montar um item de
    // transação confiável no cliente sem duplicar essa lógica. Em vez de
    // inserir um item completo no cache de `transactions` (arriscando
    // categoria/parcelas erradas que depois "trocam" quando a resposta real
    // chega), o componente usa `isPending` para mostrar um estado de
    // "salvando..." instantâneo. A lista só é atualizada de fato em
    // onSettled, com o dado real do servidor.
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['transactions'] }),
  })
}
