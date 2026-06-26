import { useMemo, useState } from 'react'
import { MoneyValue } from '@/components/money-value'
import { Skeleton } from '@/components/ui/skeleton'
import { useCategories } from '@/features/categories/useCategories'
import { rangeForPreset } from '@/features/transactions/periodPresets'
import { TransactionEditDialog } from '@/features/transactions/TransactionEditDialog'
import type { Transaction } from '@/features/transactions/useTransactions'
import { useTransactions } from '@/features/transactions/useTransactions'

export function CardMonthSpending({ cardId }: { cardId: number }) {
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null)
  const { dateFrom, dateTo } = useMemo(() => rangeForPreset('this_month'), [])
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

  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        <Skeleton className="h-8 w-48" />
        {Array.from({ length: 3 }).map((_, index) => (
          // biome-ignore lint/suspicious/noArrayIndexKey: placeholder estável, sem identidade própria
          <Skeleton key={index} className="h-10 w-full" />
        ))}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm text-muted-foreground">Gasto neste mês</h3>
        <MoneyValue cents={totalCents} className="text-lg font-semibold" />
      </div>

      {transactions && transactions.length === 0 && (
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
