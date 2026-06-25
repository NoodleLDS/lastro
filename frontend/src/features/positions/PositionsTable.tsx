import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { Position } from './usePositions'
import { usePositions, useRefreshQuotes } from './usePositions'

function formatCents(cents: number): string {
  return (cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function PositionsTable({
  onSelectPosition,
}: {
  onSelectPosition?: (position: Position) => void
}) {
  const { data: positions, isLoading } = usePositions()
  const refreshQuotes = useRefreshQuotes()

  return (
    <div className="flex w-full max-w-4xl flex-col gap-4">
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
              <TableHead>Preço médio</TableHead>
              <TableHead>Preço atual</TableHead>
              <TableHead>Total return</TableHead>
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
                <TableCell>{formatCents(position.average_price_cents)}</TableCell>
                <TableCell>
                  {position.last_price_cents !== null
                    ? formatCents(position.last_price_cents)
                    : '—'}
                </TableCell>
                <TableCell>
                  {position.total_return
                    ? `${formatCents(position.total_return.total_return_cents)} (${position.total_return.total_return_pct.toFixed(2)}%)`
                    : '—'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
