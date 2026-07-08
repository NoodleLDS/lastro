import { Check } from 'lucide-react'
import { CountUpMoneyValue } from '@/components/money-value'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useMarkInvoicePaid, useUnmarkInvoicePaid } from '@/features/cards/useCardInvoicePayment'
import { formatCents } from '@/lib/format'
import { cn } from '@/lib/utils'
import { useMonthlySummary } from './useMonthlySummary'

export function MonthlySummaryCard({ year, month }: { year: number; month: number }) {
  const { data, isLoading } = useMonthlySummary(year, month)
  const markInvoicePaid = useMarkInvoicePaid()
  const unmarkInvoicePaid = useUnmarkInvoicePaid()

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Resumo do mês</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <Skeleton className="h-10 w-40" />
          {Array.from({ length: 4 }).map((_, index) => (
            // biome-ignore lint/suspicious/noArrayIndexKey: placeholder estável, sem identidade própria
            <Skeleton key={index} className="h-6 w-full" />
          ))}
        </CardContent>
      </Card>
    )
  }

  if (!data) return null

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Resumo do mês</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className="flex flex-col gap-1 rounded-lg bg-accent/40 p-4">
          <span className="text-sm text-muted-foreground">Saldo</span>
          <CountUpMoneyValue
            cents={data.balance_cents}
            showArrow
            className="text-3xl font-semibold"
          />
        </div>

        <div className="flex flex-col gap-3 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Receita</span>
            <span className="tabular-nums">{formatCents(data.income_total_cents)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Despesas fixas</span>
            <span className="tabular-nums">{formatCents(data.fixed_expense_total_cents)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Despesas variáveis</span>
            <span className="tabular-nums">{formatCents(data.variable_expense_total_cents)}</span>
          </div>

          {data.card_spending.length > 0 && (
            <div className="flex flex-col gap-2 border-t border-border pt-3">
              {data.card_spending.map((card) => (
                <div key={card.card_id} className="flex items-center justify-between gap-2">
                  <span
                    className={cn(
                      'text-muted-foreground',
                      card.is_paid && 'text-success line-through',
                    )}
                  >
                    {card.card_name}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="tabular-nums">{formatCents(card.total_cents)}</span>
                    <Button
                      type="button"
                      size="sm"
                      variant={card.is_paid ? 'default' : 'outline'}
                      className={cn(
                        card.is_paid && 'bg-success text-success-foreground hover:bg-success/90',
                      )}
                      onClick={() =>
                        card.is_paid
                          ? unmarkInvoicePaid.mutate({ cardId: card.card_id, year, month })
                          : markInvoicePaid.mutate({ cardId: card.card_id, year, month })
                      }
                    >
                      {card.is_paid && <Check className="size-4" />}
                      {card.is_paid ? 'Paga' : 'Marcar paga'}
                    </Button>
                  </div>
                </div>
              ))}
              <div className="flex items-center justify-between pt-1 font-medium">
                <span>Total cartões</span>
                <span className="tabular-nums">{formatCents(data.card_spending_total_cents)}</span>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
