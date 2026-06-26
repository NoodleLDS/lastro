import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useCreateIncome } from './useIncomes'

export function IncomeForm({ year, month }: { year: number; month: number }) {
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const createIncome = useCreateIncome()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!description || !amount) return
    createIncome.mutate(
      {
        description,
        amount_cents: Math.round(Number(amount) * 100),
        year,
        month,
      },
      {
        onSuccess: () => {
          setDescription('')
          setAmount('')
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <div className="flex flex-wrap items-end gap-2">
        <div className="flex flex-col gap-1">
          <Label htmlFor="income-description">Receita</Label>
          <Input
            id="income-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Salário"
            required
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="income-amount">Valor</Label>
          <Input
            id="income-amount"
            type="number"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </div>
        <Button type="submit" disabled={createIncome.isPending}>
          {createIncome.isPending ? 'Adicionando...' : 'Adicionar receita'}
        </Button>
      </div>

      {createIncome.isError && (
        <p className="text-sm text-destructive">{createIncome.error.message}</p>
      )}
    </form>
  )
}
