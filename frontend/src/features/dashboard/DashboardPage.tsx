import { AllocationTargetForm } from '@/features/allocation-targets/AllocationTargetForm'
import { AllocationChart } from './AllocationChart'
import { EvolutionChart } from './EvolutionChart'
import { FireSimulator } from './FireSimulator'
import { ProjectionSimulator } from './ProjectionSimulator'

export function DashboardPage() {
  return (
    <div className="flex w-full flex-col items-center gap-8">
      <EvolutionChart />

      <div className="flex w-full max-w-2xl flex-col gap-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Metas de alocação</h3>
        <AllocationTargetForm />
      </div>
      <AllocationChart />

      <ProjectionSimulator />
      <FireSimulator />
    </div>
  )
}
