import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AnalystChat } from '@/features/analyst/AnalystChat'
import { CardGrid } from '@/features/cards/CardGrid'
import { useCards } from '@/features/cards/useCards'
import { ContributionForm } from '@/features/contributions/ContributionForm'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { MerchantRulesPage } from '@/features/merchant-rules/MerchantRulesPage'
import { MonthlySummaryPage } from '@/features/monthly-summary/MonthlySummaryPage'
import { PositionDetailPage } from '@/features/positions/PositionDetailPage'
import { PositionsTable } from '@/features/positions/PositionsTable'
import type { Position } from '@/features/positions/usePositions'
import { QuickEntryInput } from '@/features/quick-entry/QuickEntryInput'
import { TransactionsPage } from '@/features/transactions/TransactionsPage'
import { VisionPreviewTable } from '@/features/vision-preview/VisionPreviewTable'
import { VisionUpload } from '@/features/vision-preview/VisionUpload'

type Tab =
  | 'cards'
  | 'rules'
  | 'portfolio'
  | 'dashboard'
  | 'analyst'
  | 'transactions'
  | 'monthly-summary'

function App() {
  const [tab, setTab] = useState<Tab>('cards')
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null)
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null)
  const { data: cards } = useCards()

  const selectedCard = cards?.find((c) => c.id === selectedCardId) ?? null

  return (
    <main className="mx-auto flex min-h-svh max-w-7xl flex-col gap-6 p-8">
      <h1 className="text-2xl font-semibold">Lastro</h1>

      <Tabs value={tab} onValueChange={(value) => setTab(value as Tab)}>
        <TabsList>
          <TabsTrigger value="cards">Cartões</TabsTrigger>
          <TabsTrigger value="transactions">Transações</TabsTrigger>
          <TabsTrigger value="monthly-summary">Resumo mensal</TabsTrigger>
          <TabsTrigger value="rules">Regras</TabsTrigger>
          <TabsTrigger value="portfolio">Carteira</TabsTrigger>
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="analyst">Analista</TabsTrigger>
        </TabsList>

        <TabsContent value="cards" className="flex flex-col gap-6">
          <CardGrid selectedCardId={selectedCardId} onSelectCard={setSelectedCardId} />
          {selectedCard && (
            <>
              <QuickEntryInput cardId={selectedCard.id} cardName={selectedCard.name} />
              <VisionUpload cardId={selectedCard.id} />
              <VisionPreviewTable cardId={selectedCard.id} />
            </>
          )}
        </TabsContent>

        <TabsContent value="transactions">
          <TransactionsPage />
        </TabsContent>

        <TabsContent value="monthly-summary">
          <MonthlySummaryPage />
        </TabsContent>

        <TabsContent value="rules">
          <MerchantRulesPage />
        </TabsContent>

        <TabsContent value="portfolio" className="flex flex-col gap-6">
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
        </TabsContent>

        <TabsContent value="dashboard">
          <DashboardPage />
        </TabsContent>

        <TabsContent value="analyst">
          <AnalystChat />
        </TabsContent>
      </Tabs>
    </main>
  )
}

export default App
