import { useState } from 'react'
import { MoneyValue } from '@/components/money-value'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { FixedExpenseForm } from './FixedExpenseForm'
import { IncomeForm } from './IncomeForm'
import { MonthlySummaryCard } from './MonthlySummaryCard'
import { useDeleteFixedExpense, useFixedExpenses } from './useFixedExpenses'
import { useDeleteIncome, useIncomes } from './useIncomes'
import { useDeleteVariableExpense, useVariableExpenses } from './useVariableExpenses'
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
  const deleteIncome = useDeleteIncome()
  const deleteFixedExpense = useDeleteFixedExpense()
  const deleteVariableExpense = useDeleteVariableExpense()

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
                className="flex items-center justify-between rounded-lg border border-border p-2 text-sm"
              >
                <span>{expense.description}</span>
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
                className="flex items-center justify-between rounded-lg border border-border p-2 text-sm"
              >
                <span>{expense.description}</span>
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
