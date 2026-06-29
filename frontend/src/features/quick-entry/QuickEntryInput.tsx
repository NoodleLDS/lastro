import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useQuickEntry } from './useQuickEntry'

interface QuickEntryInputProps {
  cardId: number
  cardName: string
  referenceYear: number
  referenceMonth: number
}

function defaultDateForReference(year: number, month: number): string {
  const today = new Date()
  if (year === today.getFullYear() && month === today.getMonth() + 1) {
    return today.toISOString().slice(0, 10)
  }
  return new Date(year, month - 1, 1).toISOString().slice(0, 10)
}

export function QuickEntryInput({
  cardId,
  cardName,
  referenceYear,
  referenceMonth,
}: QuickEntryInputProps) {
  const [raw, setRaw] = useState('')
  const [date, setDate] = useState(() => defaultDateForReference(referenceYear, referenceMonth))
  const quickEntry = useQuickEntry()

  useEffect(() => {
    setDate(defaultDateForReference(referenceYear, referenceMonth))
  }, [referenceYear, referenceMonth])

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    quickEntry.mutate({ card_id: cardId, raw, date }, { onSuccess: () => setRaw('') })
  }

  return (
    <Card className="w-full max-w-lg">
      <CardHeader>
        <CardTitle>Lançar em {cardName}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            placeholder="zebu 22 ou tablet 335,98 3/9"
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            autoFocus
          />
          <Input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-40 shrink-0"
          />
          <Button type="submit" disabled={quickEntry.isPending || !raw.trim()}>
            Lançar
          </Button>
        </form>

        {quickEntry.isPending && <p className="text-sm text-muted-foreground">Salvando...</p>}

        {quickEntry.isError && (
          <p className="text-sm text-destructive">{quickEntry.error.message}</p>
        )}

        {!quickEntry.isPending && quickEntry.isSuccess && (
          <p className="text-sm text-muted-foreground">
            {quickEntry.data.transaction.description} — R${' '}
            {(quickEntry.data.transaction.amount_cents / 100).toFixed(2)}
            {quickEntry.data.installments.length > 0 &&
              ` + ${quickEntry.data.installments.length} parcela(s) futura(s)`}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
