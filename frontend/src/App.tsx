import { useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AnalystChat } from '@/features/analyst/AnalystChat'
import { CardGrid } from '@/features/cards/CardGrid'
import { CardMonthSpending } from '@/features/cards/CardMonthSpending'
import { useCards } from '@/features/cards/useCards'
import { ContributionForm } from '@/features/contributions/ContributionForm'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { MerchantRulesPage } from '@/features/merchant-rules/MerchantRulesPage'
import { MonthlySummaryPage } from '@/features/monthly-summary/MonthlySummaryPage'
import { PositionDetailPage } from '@/features/positions/PositionDetailPage'
import { PositionsTable } from '@/features/positions/PositionsTable'
import type { Position } from '@/features/positions/usePositions'
import { QuickEntryInput } from '@/features/quick-entry/QuickEntryInput'
import { ReportsPage } from '@/features/reports/ReportsPage'
import { TransactionsPage } from '@/features/transactions/TransactionsPage'
import { VisionPreviewTable } from '@/features/vision-preview/VisionPreviewTable'
import { VisionUpload } from '@/features/vision-preview/VisionUpload'
import { useTheme } from '@/lib/theme-context'
import { THEME_LABELS, type ThemeName } from '@/lib/themes'

type Tab =
  | 'cards'
  | 'rules'
  | 'portfolio'
  | 'dashboard'
  | 'analyst'
  | 'transactions'
  | 'monthly-summary'
  | 'reports'

function App() {
  const [tab, setTab] = useState<Tab>('cards')
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null)
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null)
  const { data: cards } = useCards()
  const { theme, setTheme } = useTheme()

  const selectedCard = cards?.find((c) => c.id === selectedCardId) ?? null

  return (
    <main className="mx-auto flex min-h-svh max-w-7xl flex-col gap-8 p-8">
      <header className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <img src="/branding/lastro-symbol.png" alt="Lastro" className="size-9" />
          <div>
            <h1 className="text-xl font-semibold leading-tight">Lastro</h1>
            <p className="text-xs text-muted-foreground">gestão financeira e patrimônio</p>
          </div>
        </div>

        <Select value={theme} onValueChange={(value) => setTheme(value as ThemeName)}>
          <SelectTrigger className="w-40" aria-label="Modelos">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(THEME_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </header>

      <Tabs value={tab} onValueChange={(value) => setTab(value as Tab)}>
        <TabsList>
          <TabsTrigger value="cards">Cartões</TabsTrigger>
          <TabsTrigger value="transactions">Transações</TabsTrigger>
          <TabsTrigger value="monthly-summary">Resumo mensal</TabsTrigger>
          <TabsTrigger value="reports">Relatórios</TabsTrigger>
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
              <CardMonthSpending cardId={selectedCard.id} />
            </>
          )}
        </TabsContent>

        <TabsContent value="transactions">
          <TransactionsPage />
        </TabsContent>

        <TabsContent value="monthly-summary">
          <MonthlySummaryPage />
        </TabsContent>

        <TabsContent value="reports">
          <ReportsPage />
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

        <TabsContent value="analyst" className="flex justify-center">
          <AnalystChat />
        </TabsContent>
      </Tabs>
    </main>
  )
}

export default App
