import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { AnalystChat } from '@/features/analyst/AnalystChat'
import { CardGrid } from '@/features/cards/CardGrid'
import { useCards } from '@/features/cards/useCards'
import { ContributionForm } from '@/features/contributions/ContributionForm'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { MerchantRulesPage } from '@/features/merchant-rules/MerchantRulesPage'
import { PositionDetailPage } from '@/features/positions/PositionDetailPage'
import { PositionsTable } from '@/features/positions/PositionsTable'
import type { Position } from '@/features/positions/usePositions'
import { QuickEntryInput } from '@/features/quick-entry/QuickEntryInput'
import { VisionPreviewTable } from '@/features/vision-preview/VisionPreviewTable'
import { VisionUpload } from '@/features/vision-preview/VisionUpload'

type Tab = 'cards' | 'rules' | 'portfolio' | 'dashboard' | 'analyst'

function App() {
  const [tab, setTab] = useState<Tab>('cards')
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null)
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null)
  const { data: cards } = useCards()

  const selectedCard = cards?.find((c) => c.id === selectedCardId) ?? null

  return (
    <main className="mx-auto flex min-h-svh max-w-4xl flex-col gap-6 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Lastro</h1>
        <nav className="flex gap-2">
          <Button variant={tab === 'cards' ? 'default' : 'ghost'} onClick={() => setTab('cards')}>
            Cartões
          </Button>
          <Button variant={tab === 'rules' ? 'default' : 'ghost'} onClick={() => setTab('rules')}>
            Regras
          </Button>
          <Button
            variant={tab === 'portfolio' ? 'default' : 'ghost'}
            onClick={() => setTab('portfolio')}
          >
            Carteira
          </Button>
          <Button
            variant={tab === 'dashboard' ? 'default' : 'ghost'}
            onClick={() => setTab('dashboard')}
          >
            Dashboard
          </Button>
          <Button
            variant={tab === 'analyst' ? 'default' : 'ghost'}
            onClick={() => setTab('analyst')}
          >
            Analista
          </Button>
        </nav>
      </div>

      {tab === 'cards' && (
        <div className="flex flex-col items-center gap-6">
          <CardGrid selectedCardId={selectedCardId} onSelectCard={setSelectedCardId} />
          {selectedCard && (
            <>
              <QuickEntryInput cardId={selectedCard.id} cardName={selectedCard.name} />
              <VisionUpload cardId={selectedCard.id} />
              <VisionPreviewTable cardId={selectedCard.id} />
            </>
          )}
        </div>
      )}

      {tab === 'rules' && (
        <div className="flex flex-col items-center">
          <MerchantRulesPage />
        </div>
      )}

      {tab === 'portfolio' && (
        <div className="flex flex-col items-center gap-6">
          {selectedPosition ? (
            <PositionDetailPage
              position={selectedPosition}
              onBack={() => setSelectedPosition(null)}
            />
          ) : (
            <>
              <ContributionForm />
              <PositionsTable onSelectPosition={setSelectedPosition} />
            </>
          )}
        </div>
      )}

      {tab === 'dashboard' && <DashboardPage />}

      {tab === 'analyst' && (
        <div className="flex flex-col items-center">
          <AnalystChat />
        </div>
      )}
    </main>
  )
}

export default App
