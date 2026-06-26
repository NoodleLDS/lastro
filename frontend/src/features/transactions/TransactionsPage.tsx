import { useMemo, useState } from 'react'
import { MoneyValue } from '@/components/money-value'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useCards } from '@/features/cards/useCards'
import { useCategories } from '@/features/categories/useCategories'
import type { PeriodPreset } from './periodPresets'
import { rangeForPreset } from './periodPresets'
import { TransactionEditDialog } from './TransactionEditDialog'
import type { Transaction } from './useTransactions'
import { useTransactions } from './useTransactions'

const ALL_CATEGORIES = 'all'

export function TransactionsPage() {
  const [search, setSearch] = useState('')
  const [categoryId, setCategoryId] = useState<string>(ALL_CATEGORIES)
  const [preset, setPreset] = useState<PeriodPreset>('this_month')
  const [customFrom, setCustomFrom] = useState('')
  const [customTo, setCustomTo] = useState('')
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null)

  const { data: categories } = useCategories()
  const { data: cards } = useCards()

  const { dateFrom, dateTo } = useMemo(() => {
    if (preset === 'custom') {
      return { dateFrom: customFrom || undefined, dateTo: customTo || undefined }
    }
    return rangeForPreset(preset)
  }, [preset, customFrom, customTo])

  const { data: transactions, isLoading } = useTransactions({
    search,
    categoryId: categoryId === ALL_CATEGORIES ? undefined : Number(categoryId),
    dateFrom,
    dateTo,
  })

  const categoryNameById = useMemo(() => {
    const map = new Map<number, string>()
    for (const category of categories ?? []) {
      map.set(category.id, category.name)
    }
    return map
  }, [categories])

  const cardById = useMemo(() => {
    const map = new Map<number, { name: string; color: string }>()
    for (const card of cards ?? []) {
      map.set(card.id, { name: card.name, color: card.color })
    }
    return map
  }, [cards])

  return (
    <div className="flex w-full flex-col gap-4">
      <h2 className="text-lg font-semibold">Transações</h2>

      <div className="flex flex-wrap items-end gap-2">
        <div className="flex flex-1 flex-col gap-1">
          <label htmlFor="transactions-search" className="text-sm text-muted-foreground">
            Buscar por descrição
          </label>
          <Input
            id="transactions-search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="ex.: uber, mercado, netflix"
          />
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-sm text-muted-foreground">Categoria</span>
          <Select value={categoryId} onValueChange={setCategoryId}>
            <SelectTrigger>
              <SelectValue placeholder="todas" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_CATEGORIES}>Todas</SelectItem>
              {categories?.map((category) => (
                <SelectItem key={category.id} value={String(category.id)}>
                  {category.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-sm text-muted-foreground">Período</span>
          <Select value={preset} onValueChange={(value) => setPreset(value as PeriodPreset)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="this_month">Este mês</SelectItem>
              <SelectItem value="last_month">Mês passado</SelectItem>
              <SelectItem value="custom">Personalizado</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {preset === 'custom' && (
          <>
            <div className="flex flex-col gap-1">
              <label htmlFor="transactions-date-from" className="text-sm text-muted-foreground">
                De
              </label>
              <Input
                id="transactions-date-from"
                type="date"
                value={customFrom}
                onChange={(e) => setCustomFrom(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label htmlFor="transactions-date-to" className="text-sm text-muted-foreground">
                Até
              </label>
              <Input
                id="transactions-date-to"
                type="date"
                value={customTo}
                onChange={(e) => setCustomTo(e.target.value)}
              />
            </div>
          </>
        )}
      </div>

      {isLoading && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 6 }).map((_, index) => (
            // biome-ignore lint/suspicious/noArrayIndexKey: placeholder estável, sem identidade própria
            <Skeleton key={index} className="h-10 w-full" />
          ))}
        </div>
      )}

      {!isLoading && transactions && transactions.length === 0 && (
        <p className="text-muted-foreground">nenhuma transação encontrada para esse filtro.</p>
      )}

      {transactions && transactions.length > 0 && (
        <>
          <Table className="hidden md:table">
            <TableHeader>
              <TableRow>
                <TableHead>Data</TableHead>
                <TableHead>Descrição</TableHead>
                <TableHead>Cartão</TableHead>
                <TableHead>Categoria</TableHead>
                <TableHead className="text-right">Valor</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions.map((transaction) => {
                const card = cardById.get(transaction.card_id)
                return (
                  <TableRow
                    key={transaction.id}
                    className="cursor-pointer"
                    onClick={() => setEditingTransaction(transaction)}
                  >
                    <TableCell className="tabular-nums">{transaction.date}</TableCell>
                    <TableCell>{transaction.description}</TableCell>
                    <TableCell>
                      {card && (
                        <span className="inline-flex items-center gap-1.5">
                          <span
                            className="size-2 rounded-full"
                            style={{ backgroundColor: card.color }}
                            aria-hidden
                          />
                          {card.name}
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      {transaction.category_id !== null
                        ? (categoryNameById.get(transaction.category_id) ?? '—')
                        : '—'}
                    </TableCell>
                    <TableCell className="text-right">
                      <MoneyValue cents={transaction.amount_cents} className="justify-end" />
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>

          <div className="flex flex-col gap-2 md:hidden">
            {transactions.map((transaction) => {
              const card = cardById.get(transaction.card_id)
              return (
                <button
                  type="button"
                  key={transaction.id}
                  className="flex flex-col gap-1 rounded-lg border border-border p-3 text-left"
                  onClick={() => setEditingTransaction(transaction)}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{transaction.description}</span>
                    <MoneyValue cents={transaction.amount_cents} />
                  </div>
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span className="tabular-nums">{transaction.date}</span>
                    <span className="flex items-center gap-2">
                      {card && (
                        <span className="inline-flex items-center gap-1.5">
                          <span
                            className="size-2 rounded-full"
                            style={{ backgroundColor: card.color }}
                            aria-hidden
                          />
                          {card.name}
                        </span>
                      )}
                      {transaction.category_id !== null
                        ? (categoryNameById.get(transaction.category_id) ?? '—')
                        : '—'}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        </>
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
