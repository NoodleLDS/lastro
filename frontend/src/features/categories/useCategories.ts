import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { apiGet } from '@/lib/api'

const categorySchema = z.object({
  id: z.number(),
  name: z.string(),
})

export type Category = z.infer<typeof categorySchema>

const categoriesSchema = z.array(categorySchema)

export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: async () => categoriesSchema.parse(await apiGet('/categories')),
  })
}
