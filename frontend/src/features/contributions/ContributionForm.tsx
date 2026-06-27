import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useCreatePosition, usePositions } from '@/features/positions/usePositions'
import { useCreateContribution } from './useContributions'
import { useCreateSale } from './useSales'

const NEW_POSITION_VALUE = '__new__'

const ASSET_TYPE_OPTIONS = [
  { value: 'stock', label: 'Ação' },
  { value: 'fii', label: 'FII' },
  { value: 'etf', label: 'ETF' },
  { value: 'fixed_income', label: 'Renda fixa' },
  { value: 'crypto', label: 'Cripto' },
]

export function ContributionForm() {
  const [positionId, setPositionId] = useState('')
  const [pendingTicker, setPendingTicker] = useState('')
  const [operation, setOperation] = useState<'contribution' | 'sale'>('contribution')
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [quantity, setQuantity] = useState('')
  const [unitPrice, setUnitPrice] = useState('')

  const [newPositionOpen, setNewPositionOpen] = useState(false)
  const [newTicker, setNewTicker] = useState('')
  const [newName, setNewName] = useState('')
  const [newAssetType, setNewAssetType] = useState('stock')

  const { data: positions } = usePositions()
  const createContribution = useCreateContribution()
  const createSale = useCreateSale()
  const createPosition = useCreatePosition()

  function handlePositionChange(value: string) {
    if (value === NEW_POSITION_VALUE || !value) {
      setNewPositionOpen(value === NEW_POSITION_VALUE)
      return
    }
    setPendingTicker('')
    setPositionId(value)
  }

  function handleCreatePosition(event: React.FormEvent) {
    event.preventDefault()
    if (!newTicker || !newName) return
    createPosition.mutate(
      { ticker: newTicker.toUpperCase(), name: newName, asset_type: newAssetType },
      {
        onSuccess: (position) => {
          setPendingTicker(position.ticker)
          setPositionId(String(position.id))
          setNewTicker('')
          setNewName('')
          setNewAssetType('stock')
          setNewPositionOpen(false)
        },
      },
    )
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!positionId || !quantity || !unitPrice) return
    const input = {
      position_id: Number(positionId),
      date,
      quantity: Number(quantity),
      unit_price_cents: Math.round(Number(unitPrice) * 100),
    }
    const mutation = operation === 'sale' ? createSale : createContribution
    mutation.mutate(input, {
      onSuccess: () => {
        setQuantity('')
        setUnitPrice('')
      },
    })
  }

  const isPending = createContribution.isPending || createSale.isPending
  const error = createContribution.error ?? createSale.error

  return (
    <>
      <form onSubmit={handleSubmit} className="flex flex-col gap-2">
        <div className="flex flex-wrap items-end gap-2">
          <div className="flex flex-col gap-1">
            <Label htmlFor="contribution-position">Posição</Label>
            <Select value={positionId} onValueChange={handlePositionChange}>
              <SelectTrigger id="contribution-position">
                <SelectValue placeholder="selecione">
                  {positions?.find((position) => String(position.id) === positionId)?.ticker ??
                    pendingTicker}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {positions?.map((position) => (
                  <SelectItem key={position.id} value={String(position.id)}>
                    {position.ticker}
                  </SelectItem>
                ))}
                <SelectItem value={NEW_POSITION_VALUE}>+ novo ativo</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="contribution-operation">Operação</Label>
            <Select
              value={operation}
              onValueChange={(value) => setOperation(value as 'contribution' | 'sale')}
            >
              <SelectTrigger id="contribution-operation">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="contribution">Compra</SelectItem>
                <SelectItem value="sale">Venda</SelectItem>
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
          <Button type="submit" disabled={isPending}>
            {isPending
              ? 'Registrando...'
              : operation === 'sale'
                ? 'Registrar venda'
                : 'Registrar aporte'}
          </Button>
        </div>

        {error && <p className="text-sm text-destructive">{error.message}</p>}
      </form>

      <Dialog open={newPositionOpen} onOpenChange={setNewPositionOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Novo ativo</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreatePosition} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="new-position-ticker">Ticker</Label>
              <Input
                id="new-position-ticker"
                value={newTicker}
                onChange={(e) => setNewTicker(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="new-position-name">Nome</Label>
              <Input
                id="new-position-name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="new-position-type">Tipo</Label>
              <Select value={newAssetType} onValueChange={setNewAssetType}>
                <SelectTrigger id="new-position-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ASSET_TYPE_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {createPosition.isError && (
              <p className="text-sm text-destructive">{createPosition.error.message}</p>
            )}

            <DialogFooter>
              <Button type="submit" disabled={createPosition.isPending}>
                {createPosition.isPending ? 'Criando...' : 'Criar ativo'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  )
}
