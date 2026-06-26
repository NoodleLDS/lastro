import { MoneyValue } from '@/components/money-value'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { formatCents } from '@/lib/format'
import { useMonthlySummary } from './useMonthlySummary'

export function MonthlySummaryCard({ year, month }: { year: number; month: number }) {
  const { data, isLoading } = useMonthlySummary(year, month)

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Resumo do mês</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {Array.from({ length: 5 }).map((_, index) => (
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
      <CardContent className="flex flex-col gap-3 text-sm">
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
          <div className="flex flex-col gap-1 border-t border-border pt-2">
            {data.card_spending.map((card) => (
              <div key={card.card_id} className="flex items-center justify-between">
                <span className="text-muted-foreground">{card.card_name}</span>
                <span className="tabular-nums">{formatCents(card.total_cents)}</span>
              </div>
            ))}
            <div className="flex items-center justify-between font-medium">
              <span>Total cartões</span>
              <span className="tabular-nums">{formatCents(data.card_spending_total_cents)}</span>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between border-t border-border pt-2 text-base font-semibold">
          <span>Saldo</span>
          <MoneyValue cents={data.balance_cents} showArrow />
        </div>
      </CardContent>
    </Card>
  )
}
