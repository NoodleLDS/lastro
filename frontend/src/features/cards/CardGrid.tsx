import { Plus } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { CardContent, Card as CardPrimitive } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { CardForm } from './CardForm'
import { type Card, useCards } from './useCards'

interface CardGridProps {
  selectedCardId: number | null
  onSelectCard: (cardId: number) => void
}

export function CardGrid({ selectedCardId, onSelectCard }: CardGridProps) {
  const { data: cards, isLoading } = useCards()
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingCard, setEditingCard] = useState<Card | null>(null)

  return (
    <div className="w-full">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Cartões</h2>
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            setEditingCard(null)
            setIsFormOpen(true)
          }}
        >
          <Plus className="size-4" />
          Novo cartão
        </Button>
      </div>

      {isLoading && <p className="text-muted-foreground">carregando...</p>}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
        {cards?.map((card) => (
          <button
            key={card.id}
            type="button"
            onClick={() => onSelectCard(card.id)}
            onDoubleClick={() => {
              setEditingCard(card)
              setIsFormOpen(true)
            }}
          >
            <CardPrimitive
              className={cn(
                'cursor-pointer border-2 transition-colors hover:border-primary',
                selectedCardId === card.id ? 'border-primary' : 'border-border',
              )}
            >
              <CardContent className="flex flex-col items-center gap-2 py-4">
                <div
                  className="size-8 rounded-full"
                  style={{ backgroundColor: card.color }}
                  aria-hidden
                />
                <span className="text-sm font-medium">{card.name}</span>
              </CardContent>
            </CardPrimitive>
          </button>
        ))}
      </div>

      <CardForm open={isFormOpen} onOpenChange={setIsFormOpen} card={editingCard} />
    </div>
  )
}
