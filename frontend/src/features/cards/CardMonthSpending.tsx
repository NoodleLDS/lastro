import { Check, ChevronLeft, ChevronRight } from 'lucide-react'
import { useMemo, useState } from 'react'
import { MoneyValue } from '@/components/money-value'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useCategories } from '@/features/categories/useCategories'
import { TransactionEditDialog } from '@/features/transactions/TransactionEditDialog'
import type { Transaction } from '@/features/transactions/useTransactions'
import { useTransactions } from '@/features/transactions/useTransactions'
import { cn } from '@/lib/utils'
import {
  useCardInvoicePayment,
  useMarkInvoicePaid,
  useUnmarkInvoicePaid,
} from './useCardInvoicePayment'

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

interface CardMonthSpendingProps {
  cardId: number
  year: number
  month: number
  onReferenceChange: (reference: { year: number; month: number }) => void
}

export function CardMonthSpending({
  cardId,
  year,
  month,
  onReferenceChange,
}: CardMonthSpendingProps) {
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null)

  const { dateFrom, dateTo } = useMemo(() => calendarMonthRange(year, month), [year, month])
  const { data: transactions, isLoading } = useTransactions({ cardId, dateFrom, dateTo })
  const { data: categories } = useCategories()
  const { data: invoicePayment, isLoading: isLoadingInvoicePayment } = useCardInvoicePayment(
    cardId,
    year,
    month,
  )
  const markInvoicePaid = useMarkInvoicePaid()
  const unmarkInvoicePaid = useUnmarkInvoicePaid()
  const isInvoicePaid = invoicePayment !== null && invoicePayment !== undefined

  function toggleInvoicePaid() {
    if (isInvoicePaid) {
      unmarkInvoicePaid.mutate({ cardId, year, month })
    } else {
      markInvoicePaid.mutate({ cardId, year, month })
    }
  }

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
            onClick={() => onReferenceChange(addMonths(year, month, -1))}
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
            onClick={() => onReferenceChange(addMonths(year, month, 1))}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
        <div className="flex items-center gap-2">
          {!isLoading && <MoneyValue cents={totalCents} className="text-lg font-semibold" />}
          {!isLoadingInvoicePayment && (
            <Button
              type="button"
              size="sm"
              variant={isInvoicePaid ? 'default' : 'outline'}
              className={cn(
                isInvoicePaid && 'bg-success text-success-foreground hover:bg-success/90',
              )}
              onClick={toggleInvoicePaid}
            >
              {isInvoicePaid && <Check className="size-4" />}
              {isInvoicePaid ? 'Fatura paga' : 'Marcar fatura como paga'}
            </Button>
          )}
        </div>
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
