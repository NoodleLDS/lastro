import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useCategories } from '@/features/categories/useCategories'
import { useCreateVariableExpense } from './useVariableExpenses'

export function VariableExpenseForm({ year, month }: { year: number; month: number }) {
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [categoryId, setCategoryId] = useState<string>('')
  const { data: categories } = useCategories()
  const createVariableExpense = useCreateVariableExpense()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!description || !amount) return
    createVariableExpense.mutate(
      {
        description,
        amount_cents: Math.round(Number(amount) * 100),
        year,
        month,
        category_id: categoryId ? Number(categoryId) : undefined,
      },
      {
        onSuccess: () => {
          setDescription('')
          setAmount('')
          setCategoryId('')
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <div className="flex flex-wrap items-end gap-2">
        <div className="flex flex-col gap-1">
          <Label htmlFor="variable-expense-description">Despesa variável</Label>
          <Input
            id="variable-expense-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Luz"
            required
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="variable-expense-amount">Valor</Label>
          <Input
            id="variable-expense-amount"
            type="number"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="variable-expense-category">Categoria</Label>
          <Select value={categoryId} onValueChange={setCategoryId}>
            <SelectTrigger id="variable-expense-category">
              <SelectValue placeholder="opcional" />
            </SelectTrigger>
            <SelectContent>
              {categories?.map((category) => (
                <SelectItem key={category.id} value={String(category.id)}>
                  {category.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button type="submit" disabled={createVariableExpense.isPending}>
          {createVariableExpense.isPending ? 'Adicionando...' : 'Adicionar despesa variável'}
        </Button>
      </div>

      {createVariableExpense.isError && (
        <p className="text-sm text-destructive">{createVariableExpense.error.message}</p>
      )}
    </form>
  )
}
