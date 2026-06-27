import { Pencil, Plus } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { CardContent, Card as CardPrimitive } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { CardForm } from './CardForm'
import { getCardBrandIcon } from './card-brand-icons'
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

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
        {isLoading &&
          Array.from({ length: 4 }).map((_, index) => (
            // biome-ignore lint/suspicious/noArrayIndexKey: placeholder estável, sem identidade própria
            <Skeleton key={index} className="h-[88px] w-full" />
          ))}

        {cards?.map((card) => {
          const brandIcon = getCardBrandIcon(card.name)
          return (
            <div key={card.id} className="group relative">
              <button
                type="button"
                className="w-full"
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
                    {brandIcon ? (
                      <img
                        src={brandIcon}
                        alt={card.name}
                        className="size-8 rounded-full object-cover"
                      />
                    ) : (
                      <div
                        className="size-8 rounded-full"
                        style={{ backgroundColor: card.color }}
                        aria-hidden
                      />
                    )}
                    <span className="text-sm font-medium">{card.name}</span>
                  </CardContent>
                </CardPrimitive>
              </button>
              <button
                type="button"
                aria-label={`Editar ${card.name}`}
                className="absolute top-1.5 right-1.5 rounded-md p-1 text-muted-foreground opacity-0 transition-opacity hover:bg-accent hover:text-foreground focus-visible:opacity-100 group-hover:opacity-100"
                onClick={(event) => {
                  event.stopPropagation()
                  setEditingCard(card)
                  setIsFormOpen(true)
                }}
              >
                <Pencil className="size-3.5" />
              </button>
            </div>
          )
        })}
      </div>

      <CardForm open={isFormOpen} onOpenChange={setIsFormOpen} card={editingCard} />
    </div>
  )
}
