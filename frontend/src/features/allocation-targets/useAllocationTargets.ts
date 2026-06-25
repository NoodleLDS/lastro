import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { apiDelete, apiGet, apiPost, apiPut } from '@/lib/api'

const allocationTargetSchema = z.object({
  id: z.number(),
  asset_type: z.string(),
  target_percentage: z.number(),
})

export type AllocationTarget = z.infer<typeof allocationTargetSchema>

const allocationTargetsSchema = z.array(allocationTargetSchema)

export function useAllocationTargets() {
  return useQuery({
    queryKey: ['allocation-targets'],
    queryFn: async () => allocationTargetsSchema.parse(await apiGet('/allocation-targets')),
  })
}

export function useCreateAllocationTarget() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { asset_type: string; target_percentage: number }) =>
      allocationTargetSchema.parse(await apiPost('/allocation-targets', input)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['allocation-targets'] }),
  })
}

export function useUpdateAllocationTarget() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, target_percentage }: { id: number; target_percentage: number }) =>
      allocationTargetSchema.parse(
        await apiPut(`/allocation-targets/${id}`, { target_percentage }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['allocation-targets'] }),
  })
}

export function useDeleteAllocationTarget() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => apiDelete(`/allocation-targets/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['allocation-targets'] }),
  })
}
