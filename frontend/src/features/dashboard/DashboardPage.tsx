import { AllocationTargetForm } from '@/features/allocation-targets/AllocationTargetForm'
import { AllocationChart } from './AllocationChart'
import { EvolutionChart } from './EvolutionChart'
import { FinancialSummaryCards } from './FinancialSummaryCards'
import { FireSimulator } from './FireSimulator'
import { ProjectionSimulator } from './ProjectionSimulator'

export function DashboardPage() {
  return (
    <div className="flex w-full flex-col gap-6">
      <FinancialSummaryCards />

      <EvolutionChart />

      <div className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Metas de alocação</h3>
        <AllocationTargetForm />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <AllocationChart />
        <div className="flex flex-col gap-6">
          <ProjectionSimulator />
          <FireSimulator />
        </div>
      </div>
    </div>
  )
}
