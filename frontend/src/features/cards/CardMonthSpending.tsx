import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { MoneyValue } from '@/components/money-value'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useCategories } from '@/features/categories/useCategories'
import { TransactionEditDialog } from '@/features/transactions/TransactionEditDialog'
import type { Transaction } from '@/features/transactions/useTransactions'
import { useTransactions } from '@/features/transactions/useTransactions'

const MONTH_LABELS = [
  'janeiro',
  'fevereiro',
  'março',
  'abril',
  'maio',
  'junho',
  'julho',
  'agosto',
  'setembro',
  'outubro',
  'novembro',
  'dezembro',
]

function addMonths(year: number, month: number, delta: number): { year: number; month: number } {
  const total = year * 12 + (month - 1) + delta
  return { year: Math.floor(total / 12), month: (total % 12) + 1 }
}

function toIsoDate(date: Date): string {
  return date.toISOString().slice(0, 10)
}

function calendarMonthRange(year: number, month: number): { dateFrom: string; dateTo: string } {
  return {
    dateFrom: toIsoDate(new Date(year, month - 1, 1)),
    dateTo: toIsoDate(new Date(year, month, 0)),
  }
}

export function CardMonthSpending({ cardId }: { cardId: number }) {
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null)
  const [{ year, month }, setReference] = useState(() => {
    const now = new Date()
    return { year: now.getFullYear(), month: now.getMonth() + 1 }
  })

  // biome-ignore lint/correctness/useExhaustiveDependencies: cardId dispara o reset de mês ao trocar de cartão, mesmo sem ser lido no corpo
  useEffect(() => {
    const now = new Date()
    setReference({ year: now.getFullYear(), month: now.getMonth() + 1 })
  }, [cardId])

  const { dateFrom, dateTo } = useMemo(() => calendarMonthRange(year, month), [year, month])
  const { data: transactions, isLoading } = useTransactions({ cardId, dateFrom, dateTo })
  const { data: categories } = useCategories()

  const categoryNameById = useMemo(() => {
    const map = new Map<number, string>()
    for (const category of categories ?? []) {
      map.set(category.id, category.name)
    }
    return map
  }, [categories])

  const totalCents = useMemo(
    () => (transactions ?? []).reduce((sum, t) => sum + t.amount_cents, 0),
    [transactions],
  )

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            type="button"
            size="icon"
            variant="ghost"
            className="size-7"
            aria-label="Mês anterior"
            onClick={() => setReference(addMonths(year, month, -1))}
          >
            <ChevronLeft className="size-4" />
          </Button>
          <h3 className="text-sm text-muted-foreground capitalize">
            {MONTH_LABELS[month - 1]} {year}
          </h3>
          <Button
            type="button"
            size="icon"
            variant="ghost"
            className="size-7"
            aria-label="Próximo mês"
            onClick={() => setReference(addMonths(year, month, 1))}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
        {!isLoading && <MoneyValue cents={totalCents} className="text-lg font-semibold" />}
      </div>

      {isLoading && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 3 }).map((_, index) => (
            // biome-ignore lint/suspicious/noArrayIndexKey: placeholder estável, sem identidade própria
            <Skeleton key={index} className="h-10 w-full" />
          ))}
        </div>
      )}

      {!isLoading && transactions && transactions.length === 0 && (
        <p className="text-sm text-muted-foreground">nenhum lançamento neste mês ainda.</p>
      )}

      {transactions && transactions.length > 0 && (
        <div className="flex flex-col gap-1">
          {transactions.map((transaction) => (
            <button
              type="button"
              key={transaction.id}
              className="flex items-center justify-between rounded-lg border border-border p-2.5 text-left text-sm hover:border-primary"
              onClick={() => setEditingTransaction(transaction)}
            >
              <div className="flex flex-col">
                <span>{transaction.description}</span>
                <span className="text-xs text-muted-foreground">
                  {transaction.date}
                  {transaction.category_id !== null &&
                    ` · ${categoryNameById.get(transaction.category_id) ?? '—'}`}
                  {transaction.installment_total &&
                    ` · ${transaction.installment_current}/${transaction.installment_total}`}
                </span>
              </div>
              <MoneyValue cents={transaction.amount_cents} />
            </button>
          ))}
        </div>
      )}

      <TransactionEditDialog
        open={editingTransaction !== null}
        onOpenChange={(open) => {
          if (!open) setEditingTransaction(null)
        }}
        transaction={editingTransaction}
      />
    </div>
  )
}
