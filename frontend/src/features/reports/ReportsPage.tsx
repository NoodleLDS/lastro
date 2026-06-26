import { useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useCategories } from '@/features/categories/useCategories'
import type { PeriodPreset } from '@/features/transactions/periodPresets'
import { rangeForPreset } from '@/features/transactions/periodPresets'
import type { ReportModuleValue } from './useReports'
import { REPORT_MODULES, useExportReportJson, useExportReportXlsx } from './useReports'

const ALL_CATEGORIES = 'all'

export function ReportsPage() {
  const [selectedModules, setSelectedModules] = useState<Set<ReportModuleValue>>(
    new Set(REPORT_MODULES.map((m) => m.value)),
  )
  const [categoryId, setCategoryId] = useState<string>(ALL_CATEGORIES)
  const [preset, setPreset] = useState<PeriodPreset>('this_month')
  const [customFrom, setCustomFrom] = useState('')
  const [customTo, setCustomTo] = useState('')
  const [jsonResult, setJsonResult] = useState<string | null>(null)

  const { data: categories } = useCategories()
  const exportJson = useExportReportJson()
  const exportXlsx = useExportReportXlsx()

  const { dateFrom, dateTo } = useMemo(() => {
    if (preset === 'custom') {
      return { dateFrom: customFrom || undefined, dateTo: customTo || undefined }
    }
    return rangeForPreset(preset)
  }, [preset, customFrom, customTo])

  function toggleModule(value: ReportModuleValue) {
    setSelectedModules((prev) => {
      const next = new Set(prev)
      if (next.has(value)) {
        next.delete(value)
      } else {
        next.add(value)
      }
      return next
    })
  }

  function buildFilters() {
    return {
      modules: Array.from(selectedModules),
      dateFrom,
      dateTo,
      categoryId: categoryId === ALL_CATEGORIES ? undefined : Number(categoryId),
    }
  }

  async function handleExportJson() {
    setJsonResult(null)
    const result = await exportJson.mutateAsync(buildFilters())
    setJsonResult(JSON.stringify(result, null, 2))
  }

  async function handleExportXlsx() {
    await exportXlsx.mutateAsync(buildFilters())
  }

  return (
    <div className="flex w-full flex-col gap-4">
      <h2 className="text-lg font-semibold">Relatórios</h2>

      <div className="flex flex-col gap-2">
        <span className="text-sm text-muted-foreground">Módulos</span>
        <div className="flex flex-wrap gap-3">
          {REPORT_MODULES.map((module) => (
            <label
              key={module.value}
              className="flex items-center gap-1.5 text-sm"
              htmlFor={`module-${module.value}`}
            >
              <input
                id={`module-${module.value}`}
                type="checkbox"
                checked={selectedModules.has(module.value)}
                onChange={() => toggleModule(module.value)}
                className="size-4 rounded border-border accent-primary"
              />
              {module.label}
            </label>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-2">
        <div className="flex flex-col gap-1">
          <span className="text-sm text-muted-foreground">Categoria</span>
          <Select value={categoryId} onValueChange={setCategoryId}>
            <SelectTrigger>
              <SelectValue placeholder="todas" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_CATEGORIES}>Todas</SelectItem>
              {categories?.map((category) => (
                <SelectItem key={category.id} value={String(category.id)}>
                  {category.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-sm text-muted-foreground">Período</span>
          <Select value={preset} onValueChange={(value) => setPreset(value as PeriodPreset)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="this_month">Este mês</SelectItem>
              <SelectItem value="last_month">Mês passado</SelectItem>
              <SelectItem value="custom">Personalizado</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {preset === 'custom' && (
          <>
            <div className="flex flex-col gap-1">
              <label htmlFor="reports-date-from" className="text-sm text-muted-foreground">
                De
              </label>
              <Input
                id="reports-date-from"
                type="date"
                value={customFrom}
                onChange={(e) => setCustomFrom(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label htmlFor="reports-date-to" className="text-sm text-muted-foreground">
                Até
              </label>
              <Input
                id="reports-date-to"
                type="date"
                value={customTo}
                onChange={(e) => setCustomTo(e.target.value)}
              />
            </div>
          </>
        )}
      </div>

      <div className="flex gap-2">
        <Button
          onClick={handleExportJson}
          disabled={exportJson.isPending || selectedModules.size === 0}
        >
          {exportJson.isPending ? 'Gerando...' : 'Exportar JSON'}
        </Button>
        <Button
          variant="secondary"
          onClick={handleExportXlsx}
          disabled={exportXlsx.isPending || selectedModules.size === 0}
        >
          {exportXlsx.isPending ? 'Gerando...' : 'Exportar planilha'}
        </Button>
      </div>

      {jsonResult && (
        <pre className="max-h-96 overflow-auto rounded-lg border border-border bg-card p-3 text-xs">
          {jsonResult}
        </pre>
      )}
    </div>
  )
}
