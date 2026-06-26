import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useCategories } from '@/features/categories/useCategories'
import { MerchantRuleForm } from './MerchantRuleForm'
import { useDeleteMerchantRule, useMerchantRules } from './useMerchantRules'

export function MerchantRulesPage() {
  const { data: rules, isLoading } = useMerchantRules()
  const { data: categories } = useCategories()
  const deleteRule = useDeleteMerchantRule()

  function categoryName(categoryId: number): string {
    return categories?.find((c) => c.id === categoryId)?.name ?? '—'
  }

  return (
    <div className="flex w-full max-w-2xl flex-col gap-4">
      <h2 className="text-lg font-semibold">Regras</h2>
      <MerchantRuleForm />

      {isLoading && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 4 }).map((_, index) => (
            // biome-ignore lint/suspicious/noArrayIndexKey: placeholder estável, sem identidade própria
            <Skeleton key={index} className="h-9 w-full" />
          ))}
        </div>
      )}

      {rules && rules.length === 0 && (
        <p className="text-muted-foreground">nenhuma regra cadastrada ainda</p>
      )}

      {rules && rules.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Padrão</TableHead>
              <TableHead>Categoria</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {rules.map((rule) => (
              <TableRow key={rule.id}>
                <TableCell>{rule.pattern}</TableCell>
                <TableCell>{categoryName(rule.category_id)}</TableCell>
                <TableCell>
                  <Button size="sm" variant="ghost" onClick={() => deleteRule.mutate(rule.id)}>
                    remover
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
