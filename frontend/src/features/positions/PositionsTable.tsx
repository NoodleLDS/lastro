import { Fragment } from 'react'
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

const ASSET_TYPE_ORDER = ['stock', 'fii', 'etf', 'fixed_income', 'crypto']

const ASSET_TYPE_LABELS: Record<string, string> = {
  stock: 'Ações',
  fii: 'FIIs',
  etf: 'ETFs',
  fixed_income: 'Renda fixa',
  crypto: 'Cripto',
}

function groupByAssetType(positions: Position[]) {
  const groups = new Map<string, Position[]>()
  for (const position of positions) {
    const group = groups.get(position.asset_type) ?? []
    group.push(position)
    groups.set(position.asset_type, group)
  }
  return [...groups.entries()].sort(([a], [b]) => {
    const indexA = ASSET_TYPE_ORDER.indexOf(a)
    const indexB = ASSET_TYPE_ORDER.indexOf(b)
    return (
      (indexA === -1 ? ASSET_TYPE_ORDER.length : indexA) -
      (indexB === -1 ? ASSET_TYPE_ORDER.length : indexB)
    )
  })
}

function positionValueCents(position: Position): number {
  if (position.total_return) {
    return position.total_return.current_value_cents
  }
  const price = position.last_price_cents ?? position.average_price_cents
  return Math.round(position.quantity * price)
}

function groupTotalCents(group: Position[]): number {
  return group.reduce((sum, position) => sum + positionValueCents(position), 0)
}

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
                <TableHead className="text-right">Valor total</TableHead>
                <TableHead className="text-right">Total return</TableHead>
                <TableHead className="text-right">Margem de segurança</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {groupByAssetType(positions).map(([assetType, group]) => (
                <Fragment key={assetType}>
                  <TableRow className="hover:bg-transparent">
                    <TableCell
                      colSpan={8}
                      className="bg-muted/30 py-1.5 text-xs font-semibold text-muted-foreground"
                    >
                      {ASSET_TYPE_LABELS[assetType] ?? assetType}
                    </TableCell>
                  </TableRow>
                  {group.map((position) => (
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
                      <TableCell className="text-right font-medium tabular-nums">
                        {formatCents(positionValueCents(position))}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {position.total_return ? (
                          <span className="inline-flex items-center justify-end gap-1.5">
                            <MoneyValue
                              cents={position.total_return.total_return_cents}
                              showArrow
                            />
                            <span className="text-muted-foreground">
                              ({position.total_return.total_return_pct.toFixed(2)}%)
                            </span>
                          </span>
                        ) : (
                          '—'
                        )}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {position.valuation ? (
                          <span
                            className={
                              position.valuation.is_undervalued
                                ? 'text-success'
                                : 'text-destructive'
                            }
                          >
                            {position.valuation.margin_of_safety_pct.toFixed(1)}%
                          </span>
                        ) : (
                          '—'
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="hover:bg-transparent">
                    <TableCell colSpan={5} className="text-right text-xs text-muted-foreground">
                      Total {ASSET_TYPE_LABELS[assetType] ?? assetType}
                    </TableCell>
                    <TableCell className="text-right font-semibold tabular-nums">
                      {formatCents(groupTotalCents(group))}
                    </TableCell>
                    <TableCell colSpan={2} />
                  </TableRow>
                </Fragment>
              ))}
            </TableBody>
          </Table>

          <div className="flex flex-col gap-4 md:hidden">
            {groupByAssetType(positions).map(([assetType, group]) => (
              <div key={assetType} className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold text-muted-foreground">
                    {ASSET_TYPE_LABELS[assetType] ?? assetType}
                  </h3>
                  <span className="text-xs font-semibold tabular-nums text-muted-foreground">
                    {formatCents(groupTotalCents(group))}
                  </span>
                </div>
                {group.map((position) => (
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
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Valor total</span>
                      <span className="font-medium tabular-nums">
                        {formatCents(positionValueCents(position))}
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
            ))}
          </div>
        </>
      )}
    </div>
  )
}
