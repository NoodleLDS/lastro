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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatCents } from '@/lib/format'
import { usePositionHistory } from './usePositionHistory'
import type { Position } from './usePositions'

const EVENT_LABEL: Record<string, string> = {
  contribution: 'Compra',
  sale: 'Venda',
  dividend: 'Dividendo',
}

export function PositionDetailPage({
  position,
  onBack,
}: {
  position: Position
  onBack: () => void
}) {
  const { data, isLoading } = usePositionHistory(position.id)

  const chartData = data?.price_history.map((p) => ({
    date: p.date,
    preco: p.price_cents / 100,
  }))

  return (
    <div className="flex w-full flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          {position.ticker} — {position.name}
        </h2>
        <Button variant="ghost" onClick={onBack}>
          Voltar
        </Button>
      </div>

      <div className="flex gap-4 text-sm text-muted-foreground">
        <span>Quantidade: {position.quantity}</span>
        <span>Preço médio: {formatCents(position.average_price_cents)}</span>
        {position.last_price_cents !== null && (
          <span>Preço atual: {formatCents(position.last_price_cents)}</span>
        )}
        {position.price_earnings !== null && <span>P/L: {position.price_earnings.toFixed(2)}</span>}
        {position.earnings_per_share !== null && (
          <span>LPA: {formatCents(Math.round(position.earnings_per_share * 100))}</span>
        )}
      </div>

      {isLoading && <p className="text-muted-foreground">carregando...</p>}

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
                  <TableHead>Preço/Valor</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.events.map((event) => (
                  <TableRow
                    key={`${event.type}-${event.date}-${event.quantity}-${event.unit_price_cents}-${event.amount_cents}`}
                  >
                    <TableCell>{event.date}</TableCell>
                    <TableCell>{EVENT_LABEL[event.type]}</TableCell>
                    <TableCell>{event.quantity ?? '—'}</TableCell>
                    <TableCell>
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
