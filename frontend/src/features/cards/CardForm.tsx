import { useEffect, useState } from 'react'
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
import { type Card, useCreateCard, useDeactivateCard, useUpdateCard } from './useCards'

interface CardFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  card: Card | null
}

export function CardForm({ open, onOpenChange, card }: CardFormProps) {
  const [name, setName] = useState('')
  const [color, setColor] = useState('#c084fc')
  const [closingDay, setClosingDay] = useState('')
  const [dueDay, setDueDay] = useState('')

  const createCard = useCreateCard()
  const updateCard = useUpdateCard()
  const deactivateCard = useDeactivateCard()

  useEffect(() => {
    setName(card?.name ?? '')
    setColor(card?.color ?? '#c084fc')
    setClosingDay(card?.closing_day ? String(card.closing_day) : '')
    setDueDay(card?.due_day ? String(card.due_day) : '')
  }, [card])

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const closing_day = closingDay ? Number(closingDay) : null
    const due_day = dueDay ? Number(dueDay) : null
    if (card) {
      updateCard.mutate(
        { id: card.id, name, color, closing_day, due_day },
        { onSuccess: () => onOpenChange(false) },
      )
    } else {
      createCard.mutate(
        { name, color, closing_day, due_day },
        { onSuccess: () => onOpenChange(false) },
      )
    }
  }

  function handleDeactivate() {
    if (!card) return
    deactivateCard.mutate(card.id, { onSuccess: () => onOpenChange(false) })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{card ? 'Editar cartão' : 'Novo cartão'}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="card-name">Nome</Label>
            <Input id="card-name" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="card-color">Cor</Label>
            <Input
              id="card-color"
              type="color"
              value={color}
              onChange={(e) => setColor(e.target.value)}
            />
          </div>
          <div className="flex gap-4">
            <div className="flex flex-1 flex-col gap-2">
              <Label htmlFor="card-closing-day">Dia de fechamento</Label>
              <Input
                id="card-closing-day"
                type="number"
                min={1}
                max={31}
                value={closingDay}
                onChange={(e) => setClosingDay(e.target.value)}
                placeholder="ex.: 7"
              />
            </div>
            <div className="flex flex-1 flex-col gap-2">
              <Label htmlFor="card-due-day">Dia de vencimento</Label>
              <Input
                id="card-due-day"
                type="number"
                min={1}
                max={31}
                value={dueDay}
                onChange={(e) => setDueDay(e.target.value)}
                placeholder="ex.: 15"
              />
            </div>
          </div>
          {(createCard.isError || updateCard.isError || deactivateCard.isError) && (
            <p className="text-sm text-destructive">
              {createCard.error?.message ??
                updateCard.error?.message ??
                deactivateCard.error?.message}
            </p>
          )}

          <DialogFooter>
            {card && (
              <Button
                type="button"
                variant="destructive"
                onClick={handleDeactivate}
                disabled={deactivateCard.isPending}
              >
                {deactivateCard.isPending ? 'Removendo...' : 'Remover'}
              </Button>
            )}
            <Button type="submit" disabled={createCard.isPending || updateCard.isPending}>
              {createCard.isPending || updateCard.isPending
                ? 'Salvando...'
                : card
                  ? 'Salvar'
                  : 'Criar'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
