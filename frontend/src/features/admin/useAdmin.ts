import { useMutation } from '@tanstack/react-query'
import { apiPost } from '@/lib/api'

export function useRestartContainers() {
  return useMutation({
    mutationFn: () => apiPost<{ status: string }>('/admin/restart', {}),
  })
}

export function useShutdownContainers() {
  return useMutation({
    mutationFn: () => apiPost<{ status: string }>('/admin/shutdown', {}),
  })
}
