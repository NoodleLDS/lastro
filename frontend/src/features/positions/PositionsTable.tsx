import { MoneyValue } from '@/components/money-value'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatCents } from '@/lib/format'
import type { Position } from './usePositions'
import { usePositions, useRefreshQuotes } from './usePositions'

export function PositionsTable({
  onSelectPosition,
}: {
  onSelectPosition?: (position: Position) => void
}) {
  const { data: positions, isLoading } = usePositions()
  const refreshQuotes = useRefreshQuotes()

  return (
    <div className="flex w-full flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Carteira</h2>
        <Button onClick={() => refreshQuotes.mutate()} disabled={refreshQuotes.isPending}>
          {refreshQuotes.isPending ? 'Atualizando...' : 'Atualizar cotações'}
        </Button>
      </div>

      {refreshQuotes.isError && (
        <p className="text-sm text-destructive">{refreshQuotes.error.message}</p>
      )}

      {isLoading && <p className="text-muted-foreground">carregando...</p>}

      {positions && positions.length > 0 && (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Ticker</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Qtd</TableHead>
              <TableHead className="text-right">Preço médio</TableHead>
              <TableHead className="text-right">Preço atual</TableHead>
              <TableHead className="text-right">Total return</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {positions.map((position) => (
              <TableRow
                key={position.id}
                className={onSelectPosition ? 'cursor-pointer' : undefined}
                onClick={() => onSelectPosition?.(position)}
              >
                <TableCell className="font-medium">{position.ticker}</TableCell>
                <TableCell>{position.asset_type}</TableCell>
                <TableCell>{position.quantity}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatCents(position.average_price_cents)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {position.last_price_cents !== null
                    ? formatCents(position.last_price_cents)
                    : '—'}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {position.total_return ? (
                    <span className="inline-flex items-center justify-end gap-1.5">
                      <MoneyValue cents={position.total_return.total_return_cents} showArrow />
                      <span className="text-muted-foreground">
                        ({position.total_return.total_return_pct.toFixed(2)}%)
                      </span>
                    </span>
                  ) : (
                    '—'
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
