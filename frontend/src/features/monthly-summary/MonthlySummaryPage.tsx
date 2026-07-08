import { useMemo, useState } from 'react'
import { MoneyValue } from '@/components/money-value'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { FixedExpenseForm } from './FixedExpenseForm'
import { IncomeForm } from './IncomeForm'
import { MonthlySummaryCard } from './MonthlySummaryCard'
import { useDeleteFixedExpense, useFixedExpenses, useUpdateFixedExpense } from './useFixedExpenses'
import { useDeleteIncome, useIncomes } from './useIncomes'
import { useMonthlySummary } from './useMonthlySummary'
import {
  useDeleteVariableExpense,
  useUpdateVariableExpense,
  useVariableExpenses,
} from './useVariableExpenses'
import { VariableExpenseForm } from './VariableExpenseForm'

const MONTH_NAMES = [
  'Janeiro',
  'Fevereiro',
  'Março',
  'Abril',
  'Maio',
  'Junho',
  'Julho',
  'Agosto',
  'Setembro',
  'Outubro',
  'Novembro',
  'Dezembro',
]

export function MonthlySummaryPage() {
  const now = new Date()
  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth() + 1)

  const { data: incomes, isLoading: incomesLoading } = useIncomes(year, month)
  const { data: fixedExpenses, isLoading: fixedExpensesLoading } = useFixedExpenses(year, month)
  const { data: variableExpenses, isLoading: variableExpensesLoading } = useVariableExpenses(
    year,
    month,
  )
  const { data: monthlySummary } = useMonthlySummary(year, month)
  const deleteIncome = useDeleteIncome()
  const deleteFixedExpense = useDeleteFixedExpense()
  const deleteVariableExpense = useDeleteVariableExpense()
  const updateFixedExpense = useUpdateFixedExpense()
  const updateVariableExpense = useUpdateVariableExpense()

  const remainingCents = useMemo(() => {
    const fixedRemaining = (fixedExpenses ?? [])
      .filter((expense) => !expense.is_paid)
      .reduce((sum, expense) => sum + expense.amount_cents, 0)
    const variableRemaining = (variableExpenses ?? [])
      .filter((expense) => !expense.is_paid)
      .reduce((sum, expense) => sum + expense.amount_cents, 0)
    const cardsRemaining = (monthlySummary?.card_spending ?? [])
      .filter((card) => !card.is_paid)
      .reduce((sum, card) => sum + card.total_cents, 0)
    return fixedRemaining + variableRemaining + cardsRemaining
  }, [fixedExpenses, variableExpenses, monthlySummary])

  const totalExpensesCents = useMemo(() => {
    const fixedTotal = (fixedExpenses ?? []).reduce((sum, expense) => sum + expense.amount_cents, 0)
    const variableTotal = (variableExpenses ?? []).reduce(
      (sum, expense) => sum + expense.amount_cents,
      0,
    )
    const cardsTotal = monthlySummary?.card_spending_total_cents ?? 0
    return fixedTotal + variableTotal + cardsTotal
  }, [fixedExpenses, variableExpenses, monthlySummary])

  return (
    <div className="flex w-full flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Resumo mensal</h2>
        <div className="flex gap-2">
          <Select value={String(month)} onValueChange={(value) => setMonth(Number(value))}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MONTH_NAMES.map((name, index) => (
                <SelectItem key={name} value={String(index + 1)}>
                  {name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={String(year)} onValueChange={(value) => setYear(Number(value))}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[now.getFullYear() - 1, now.getFullYear(), now.getFullYear() + 1].map((y) => (
                <SelectItem key={y} value={String(y)}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1 rounded-lg border border-border p-3">
          <span className="text-xs text-muted-foreground">Total de despesas</span>
          <MoneyValue cents={totalExpensesCents} className="text-lg font-semibold" />
        </div>
        <div className="flex flex-col gap-1 rounded-lg border border-border p-3">
          <span className="text-xs text-muted-foreground">Falta pagar</span>
          <MoneyValue cents={remainingCents} className="text-lg font-semibold" />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-muted-foreground">Receita</h3>
            <IncomeForm year={year} month={month} />
            {incomesLoading && <Skeleton className="h-9 w-full" />}
            {incomes?.map((income) => (
              <div
                key={income.id}
                className="flex items-center justify-between rounded-lg border border-border p-2 text-sm"
              >
                <span>{income.description}</span>
                <div className="flex items-center gap-2">
                  <MoneyValue cents={income.amount_cents} />
                  <Button size="sm" variant="ghost" onClick={() => deleteIncome.mutate(income.id)}>
                    remover
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-muted-foreground">Despesas fixas</h3>
            <FixedExpenseForm year={year} month={month} />
            {fixedExpensesLoading && <Skeleton className="h-9 w-full" />}
            {fixedExpenses?.map((expense) => (
              <div
                key={expense.id}
                className={cn(
                  'flex items-center justify-between rounded-lg border border-border p-2 text-sm',
                  expense.is_paid && 'border-success/40 bg-success/5',
                )}
              >
                <div className="flex items-center gap-2">
                  <Checkbox
                    checked={expense.is_paid}
                    onCheckedChange={(checked) =>
                      updateFixedExpense.mutate({ id: expense.id, is_paid: checked === true })
                    }
                    aria-label="marcar despesa como paga"
                  />
                  <span className={cn(expense.is_paid && 'text-muted-foreground line-through')}>
                    {expense.description}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <MoneyValue cents={expense.amount_cents} />
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => deleteFixedExpense.mutate(expense.id)}
                  >
                    remover
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-muted-foreground">Despesas variáveis</h3>
            <VariableExpenseForm year={year} month={month} />
            {variableExpensesLoading && <Skeleton className="h-9 w-full" />}
            {variableExpenses?.map((expense) => (
              <div
                key={expense.id}
                className={cn(
                  'flex items-center justify-between rounded-lg border border-border p-2 text-sm',
                  expense.is_paid && 'border-success/40 bg-success/5',
                )}
              >
                <div className="flex items-center gap-2">
                  <Checkbox
                    checked={expense.is_paid}
                    onCheckedChange={(checked) =>
                      updateVariableExpense.mutate({ id: expense.id, is_paid: checked === true })
                    }
                    aria-label="marcar despesa como paga"
                  />
                  <span className={cn(expense.is_paid && 'text-muted-foreground line-through')}>
                    {expense.description}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <MoneyValue cents={expense.amount_cents} />
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => deleteVariableExpense.mutate(expense.id)}
                  >
                    remover
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <MonthlySummaryCard year={year} month={month} />
      </div>
    </div>
  )
}
