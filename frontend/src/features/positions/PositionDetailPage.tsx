import { useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Button } from '@/components/ui/button'
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
import { getTickerIcon } from './ticker-icons'
import { usePositionHistory } from './usePositionHistory'
import type { Position } from './usePositions'
import { useUpdateTargetYield } from './usePositions'

const EVENT_LABEL: Record<string, string> = {
  contribution: 'Compra',
  sale: 'Venda',
  dividend: 'Dividendo',
  stock_split: 'Desdobramento',
}

export function PositionDetailPage({
  position,
  onBack,
}: {
  position: Position
  onBack: () => void
}) {
  const { data, isLoading } = usePositionHistory(position.id)
  const updateTargetYield = useUpdateTargetYield()
  const [targetYieldInput, setTargetYieldInput] = useState(
    position.target_yield_pct?.toString() ?? '',
  )

  const chartData = data?.price_history.map((p) => ({
    date: p.date,
    preco: p.price_cents / 100,
  }))

  function handleTargetYieldBlur() {
    const parsed = targetYieldInput.trim() === '' ? null : Number(targetYieldInput)
    if (parsed === position.target_yield_pct) return
    if (parsed !== null && Number.isNaN(parsed)) return
    updateTargetYield.mutate({ id: position.id, targetYieldPct: parsed })
  }

  return (
    <div className="flex w-full flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          {getTickerIcon(position.ticker, position.asset_type) && (
            <img
              src={getTickerIcon(position.ticker, position.asset_type)!}
              alt=""
              className="size-6 rounded-full object-contain"
              aria-hidden
            />
          )}
          {position.ticker} — {position.name}
        </h2>
        <Button variant="ghost" onClick={onBack}>
          Voltar
        </Button>
      </div>

      <div className="flex gap-4 text-sm text-muted-foreground">
        <span>Quantidade: {position.quantity}</span>
        <span className="tabular-nums">
          Preço médio: {formatCents(position.average_price_cents)}
        </span>
        {position.last_price_cents !== null && (
          <span className="tabular-nums">
            Preço atual: {formatCents(position.last_price_cents)}
          </span>
        )}
        {position.price_earnings !== null && (
          <span className="tabular-nums">P/L: {position.price_earnings.toFixed(2)}</span>
        )}
        {position.earnings_per_share !== null && (
          <span className="tabular-nums">
            LPA: {formatCents(Math.round(position.earnings_per_share * 100))}
          </span>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Valuation (DY-alvo)</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <Label htmlFor="target-yield">Yield-alvo anual (%)</Label>
            <Input
              id="target-yield"
              type="number"
              step="0.1"
              min="0"
              className="w-24"
              value={targetYieldInput}
              onChange={(e) => setTargetYieldInput(e.target.value)}
              onBlur={handleTargetYieldBlur}
            />
          </div>

          {position.valuation ? (
            <div className="flex flex-wrap gap-4 text-sm">
              <span className="tabular-nums">
                Dividendos 12m: {formatCents(position.valuation.dividends_last_12m_cents)}
              </span>
              <span className="tabular-nums">
                Preço-teto: {formatCents(position.valuation.price_ceiling_cents)}
              </span>
              <span
                className={
                  position.valuation.is_undervalued
                    ? 'tabular-nums text-success'
                    : 'tabular-nums text-destructive'
                }
              >
                Margem de segurança: {position.valuation.margin_of_safety_pct.toFixed(1)}% (
                {position.valuation.is_undervalued ? 'subvalorizado' : 'sobrevalorizado'})
              </span>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              defina o yield-alvo e garanta preço atual + dividendos nos últimos 12 meses para
              calcular o preço-teto
            </p>
          )}
        </CardContent>
      </Card>

      {isLoading && <Skeleton className="h-[220px] w-full" />}

      {chartData && chartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Preço ao longo do tempo</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="date" stroke="var(--muted-foreground)" />
                <YAxis stroke="var(--muted-foreground)" />
                <Tooltip formatter={(value) => formatCents(Number(value) * 100)} />
                <Line type="monotone" dataKey="preco" stroke="var(--primary)" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {data && data.events.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Extrato</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data</TableHead>
                  <TableHead>Evento</TableHead>
                  <TableHead>Quantidade</TableHead>
                  <TableHead className="text-right">Preço/Valor</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.events.map((event) => (
                  <TableRow
                    key={`${event.type}-${event.date}-${event.quantity}-${event.unit_price_cents}-${event.amount_cents}`}
                  >
                    <TableCell>{event.date}</TableCell>
                    <TableCell>{EVENT_LABEL[event.type]}</TableCell>
                    <TableCell>
                      {event.type === 'stock_split'
                        ? `${event.ratio_from} → ${event.ratio_to}`
                        : (event.quantity ?? '—')}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {event.unit_price_cents !== null
                        ? formatCents(event.unit_price_cents)
                        : event.amount_cents !== null
                          ? formatCents(event.amount_cents)
                          : '—'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {data && data.events.length === 0 && (
        <p className="text-muted-foreground">nenhum evento registrado ainda</p>
      )}
    </div>
  )
}
