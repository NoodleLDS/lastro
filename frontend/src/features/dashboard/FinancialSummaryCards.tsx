import { useEffect, useState } from 'react'
import { MoneyValue } from '@/components/money-value'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatCents } from '@/lib/format'
import {
  useEmergencyReserves,
  useFinancialSummary,
  useUpsertEmergencyReserve,
} from './useFinancialSummary'

function SummaryCard({ label, cents }: { label: string; cents: number }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-1 p-4">
        <span className="text-xs text-muted-foreground">{label}</span>
        <MoneyValue cents={cents} className="text-lg font-semibold" />
      </CardContent>
    </Card>
  )
}

function EmergencyReserveCard() {
  const { data: reserves, isLoading: isLoadingReserves } = useEmergencyReserves()
  const upsertReserve = useUpsertEmergencyReserve()
  const reserve = reserves?.[0] ?? null

  const [balanceInput, setBalanceInput] = useState('')

  useEffect(() => {
    if (reserve) {
      setBalanceInput((reserve.balance_cents / 100).toString())
    }
  }, [reserve])

  const now = new Date()
  const { data: summary } = useFinancialSummary(now.getFullYear(), now.getMonth() + 1)

  function handleBalanceBlur() {
    const parsed = Number(balanceInput.replace(',', '.'))
    if (Number.isNaN(parsed)) return
    const cents = Math.round(parsed * 100)
    if (reserve && cents === reserve.balance_cents) return
    upsertReserve.mutate({ id: reserve?.id ?? null, balanceCents: cents })
  }

  if (isLoadingReserves) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Reserva de emergência</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-40" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Reserva de emergência</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <Label htmlFor="reserve-balance">Valor guardado (R$)</Label>
          <Input
            id="reserve-balance"
            type="number"
            step="0.01"
            min="0"
            className="w-32"
            value={balanceInput}
            onChange={(e) => setBalanceInput(e.target.value)}
            onBlur={handleBalanceBlur}
          />
        </div>

        {summary && (
          <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
            <span className="tabular-nums">
              Despesa média (3 meses):{' '}
              {formatCents(summary.emergency_reserve.average_monthly_expense_cents)}
            </span>
            <span className="tabular-nums">
              Cobertura:{' '}
              {summary.emergency_reserve.months_covered !== null
                ? `${summary.emergency_reserve.months_covered.toFixed(1)} meses`
                : '—'}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function CategoryCardBreakdownTable({
  breakdown,
}: {
  breakdown: {
    category_id: number | null
    category_name: string
    card_id: number
    card_name: string
    total_cents: number
  }[]
}) {
  if (breakdown.length === 0) {
    return <p className="text-sm text-muted-foreground">nenhum gasto categorizado neste mês</p>
  }

  const cardNames = Array.from(new Set(breakdown.map((b) => b.card_name))).sort()
  const categoryNames = Array.from(new Set(breakdown.map((b) => b.category_name))).sort()

  const totalByKey = new Map(
    breakdown.map((b) => [`${b.category_name}::${b.card_name}`, b.total_cents]),
  )
  const totalByCategory = new Map<string, number>()
  for (const b of breakdown) {
    totalByCategory.set(
      b.category_name,
      (totalByCategory.get(b.category_name) ?? 0) + b.total_cents,
    )
  }
  const grandTotal = breakdown.reduce((sum, b) => sum + b.total_cents, 0)

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Categoria</TableHead>
          {cardNames.map((name) => (
            <TableHead key={name} className="text-right">
              {name}
            </TableHead>
          ))}
          <TableHead className="text-right">Total</TableHead>
          <TableHead className="text-right">% do total</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {categoryNames.map((categoryName) => {
          const categoryTotal = totalByCategory.get(categoryName) ?? 0
          return (
            <TableRow key={categoryName}>
              <TableCell>{categoryName}</TableCell>
              {cardNames.map((cardName) => (
                <TableCell key={cardName} className="text-right tabular-nums">
                  {formatCents(totalByKey.get(`${categoryName}::${cardName}`) ?? 0)}
                </TableCell>
              ))}
              <TableCell className="text-right tabular-nums font-semibold">
                {formatCents(categoryTotal)}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {grandTotal > 0 ? `${((categoryTotal / grandTotal) * 100).toFixed(1)}%` : '—'}
              </TableCell>
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )
}

export function FinancialSummaryCards() {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  const { data, isLoading } = useFinancialSummary(year, month)

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {['receita', 'despesas', 'aportes', 'saldo'].map((label) => (
          <Skeleton key={label} className="h-20 w-full" />
        ))}
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <SummaryCard label="Receita do mês" cents={data.monthly.income_total_cents} />
        <SummaryCard label="Despesas do mês" cents={data.monthly.expense_total_cents} />
        <SummaryCard label="Aportado no mês" cents={data.monthly.contribution_total_cents} />
        <SummaryCard label="Saldo do mês" cents={data.monthly.balance_cents} />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <SummaryCard label="Receita do ano" cents={data.yearly.income_total_cents} />
        <SummaryCard label="Despesas do ano" cents={data.yearly.expense_total_cents} />
        <SummaryCard label="Saldo do ano" cents={data.yearly.balance_cents} />
      </div>

      <EmergencyReserveCard />

      <Card>
        <CardHeader>
          <CardTitle>Gastos por categoria × cartão</CardTitle>
        </CardHeader>
        <CardContent>
          <CategoryCardBreakdownTable breakdown={data.category_card_breakdown} />
        </CardContent>
      </Card>
    </div>
  )
}
