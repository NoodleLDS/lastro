import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiDelete, apiGet, apiPost, apiPut } from '@/lib/api'

const merchantRuleSchema = z.object({
  id: z.number(),
  pattern: z.string(),
  category_id: z.number(),
  is_active: z.boolean(),
})

export type MerchantRule = z.infer<typeof merchantRuleSchema>

const merchantRulesSchema = z.array(merchantRuleSchema)

export function useMerchantRules() {
  return useQuery({
    queryKey: ['merchant-rules'],
    queryFn: async () => merchantRulesSchema.parse(await apiGet('/merchant-rules')),
  })
}

export function useCreateMerchantRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { pattern: string; category_id: number }) =>
      merchantRuleSchema.parse(await apiPost('/merchant-rules', input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['merchant-rules'] }),
  })
}

export function useUpdateMerchantRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      id,
      ...input
    }: {
      id: number
      pattern?: string
      category_id?: number
      is_active?: boolean
    }) => merchantRuleSchema.parse(await apiPut(`/merchant-rules/${id}`, input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['merchant-rules'] }),
  })
}

export function useDeleteMerchantRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => apiDelete(`/merchant-rules/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['merchant-rules'] }),
  })
}
