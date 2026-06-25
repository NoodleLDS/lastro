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
    onMutate: async (input) => {
      await queryClient.cancelQueries({ queryKey: ['allocation-targets'] })
      const previousTargets = queryClient.getQueryData<AllocationTarget[]>(['allocation-targets'])
      const optimisticTarget: AllocationTarget = {
        id: -Date.now(),
        asset_type: input.asset_type,
        target_percentage: input.target_percentage,
      }
      queryClient.setQueryData<AllocationTarget[]>(['allocation-targets'], (old) => [
        ...(old ?? []),
        optimisticTarget,
      ])
      return { previousTargets }
    },
    onError: (_err, _input, context) => {
      if (context?.previousTargets) {
        queryClient.setQueryData(['allocation-targets'], context.previousTargets)
      }
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['allocation-targets'] }),
  })
}

export function useUpdateAllocationTarget() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, target_percentage }: { id: number; target_percentage: number }) =>
      allocationTargetSchema.parse(
        await apiPut(`/allocation-targets/${id}`, { target_percentage }),
      ),
    onMutate: async ({ id, target_percentage }) => {
      await queryClient.cancelQueries({ queryKey: ['allocation-targets'] })
      const previousTargets = queryClient.getQueryData<AllocationTarget[]>(['allocation-targets'])
      queryClient.setQueryData<AllocationTarget[]>(['allocation-targets'], (old) =>
        old?.map((target) => (target.id === id ? { ...target, target_percentage } : target)),
      )
      return { previousTargets }
    },
    onError: (_err, _input, context) => {
      if (context?.previousTargets) {
        queryClient.setQueryData(['allocation-targets'], context.previousTargets)
      }
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['allocation-targets'] }),
  })
}

export function useDeleteAllocationTarget() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => apiDelete(`/allocation-targets/${id}`),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ['allocation-targets'] })
      const previousTargets = queryClient.getQueryData<AllocationTarget[]>(['allocation-targets'])
      queryClient.setQueryData<AllocationTarget[]>(['allocation-targets'], (old) =>
        old?.filter((target) => target.id !== id),
      )
      return { previousTargets }
    },
    onError: (_err, _id, context) => {
      if (context?.previousTargets) {
        queryClient.setQueryData(['allocation-targets'], context.previousTargets)
      }
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['allocation-targets'] }),
  })
}
