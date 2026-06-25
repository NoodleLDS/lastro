import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { usePositions } from '@/features/positions/usePositions'
import { useCreateContribution } from './useContributions'

export function ContributionForm() {
  const [positionId, setPositionId] = useState('')
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [quantity, setQuantity] = useState('')
  const [unitPrice, setUnitPrice] = useState('')
  const { data: positions } = usePositions()
  const createContribution = useCreateContribution()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!positionId || !quantity || !unitPrice) return
    createContribution.mutate(
      {
        position_id: Number(positionId),
        date,
        quantity: Number(quantity),
        unit_price_cents: Math.round(Number(unitPrice) * 100),
      },
      {
        onSuccess: () => {
          setQuantity('')
          setUnitPrice('')
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
      <div className="flex flex-col gap-1">
        <Label htmlFor="contribution-position">Posição</Label>
        <Select value={positionId} onValueChange={setPositionId}>
          <SelectTrigger id="contribution-position">
            <SelectValue placeholder="selecione" />
          </SelectTrigger>
          <SelectContent>
            {positions?.map((position) => (
              <SelectItem key={position.id} value={String(position.id)}>
                {position.ticker}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="contribution-date">Data</Label>
        <Input
          id="contribution-date"
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          required
        />
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="contribution-quantity">Quantidade</Label>
        <Input
          id="contribution-quantity"
          type="number"
          step="any"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          required
        />
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="contribution-price">Preço unitário</Label>
        <Input
          id="contribution-price"
          type="number"
          step="0.01"
          value={unitPrice}
          onChange={(e) => setUnitPrice(e.target.value)}
          required
        />
      </div>
      <Button type="submit" disabled={createContribution.isPending}>
        Registrar aporte
      </Button>
    </form>
  )
}
