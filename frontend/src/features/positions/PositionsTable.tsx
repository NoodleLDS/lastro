import { MoneyValue } from '@/components/money-value'
import { Button } from '@/components/ui/button'
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

      {isLoading && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }).map((_, index) => (
            // biome-ignore lint/suspicious/noArrayIndexKey: placeholder estável, sem identidade própria
            <Skeleton key={index} className="h-10 w-full" />
          ))}
        </div>
      )}

      {positions && positions.length > 0 && (
        <>
          <Table className="hidden md:table">
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
                  <TableCell className="font-medium">
                    <span className="inline-flex items-center gap-2">
                      {getTickerIcon(position.ticker, position.asset_type) && (
                        <img
                          src={getTickerIcon(position.ticker, position.asset_type)!}
                          alt=""
                          className="size-5 rounded-full object-contain"
                          aria-hidden
                        />
                      )}
                      {position.ticker}
                    </span>
                  </TableCell>
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

          <div className="flex flex-col gap-2 md:hidden">
            {positions.map((position) => (
              <button
                type="button"
                key={position.id}
                className="flex flex-col gap-2 rounded-lg border border-border p-3 text-left"
                onClick={() => onSelectPosition?.(position)}
              >
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-2 font-medium">
                    {getTickerIcon(position.ticker, position.asset_type) && (
                      <img
                        src={getTickerIcon(position.ticker, position.asset_type)!}
                        alt=""
                        className="size-5 rounded-full object-contain"
                        aria-hidden
                      />
                    )}
                    {position.ticker}
                  </span>
                  <span className="text-sm text-muted-foreground">{position.asset_type}</span>
                </div>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>Qtd: {position.quantity}</span>
                  <span className="tabular-nums">
                    {position.last_price_cents !== null
                      ? formatCents(position.last_price_cents)
                      : formatCents(position.average_price_cents)}
                  </span>
                </div>
                {position.total_return && (
                  <div className="flex items-center justify-end gap-1.5 text-sm">
                    <MoneyValue cents={position.total_return.total_return_cents} showArrow />
                    <span className="text-muted-foreground">
                      ({position.total_return.total_return_pct.toFixed(2)}%)
                    </span>
                  </div>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
