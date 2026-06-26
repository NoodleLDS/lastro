import { useMutation } from '@tanstack/react-query'
import { apiDownload, apiGet } from '@/lib/api'

export const REPORT_MODULES = [
  { value: 'transactions', label: 'Transações' },
  { value: 'contributions', label: 'Aportes' },
  { value: 'dividends', label: 'Dividendos' },
  { value: 'sales', label: 'Vendas' },
  { value: 'incomes', label: 'Receitas' },
  { value: 'fixed_expenses', label: 'Gastos fixos' },
  { value: 'variable_expenses', label: 'Gastos variáveis' },
  { value: 'positions', label: 'Posições' },
] as const

export type ReportModuleValue = (typeof REPORT_MODULES)[number]['value']

export interface ReportFilters {
  modules: ReportModuleValue[]
  dateFrom?: string
  dateTo?: string
  categoryId?: number
}

function buildQueryString(filters: ReportFilters, format: 'json' | 'xlsx'): string {
  const params = new URLSearchParams()
  for (const module of filters.modules) {
    params.append('modules', module)
  }
  if (filters.dateFrom) {
    params.set('date_from', filters.dateFrom)
  }
  if (filters.dateTo) {
    params.set('date_to', filters.dateTo)
  }
  if (filters.categoryId !== undefined) {
    params.set('category_id', String(filters.categoryId))
  }
  params.set('format', format)
  return `?${params.toString()}`
}

export function useExportReportJson() {
  return useMutation({
    mutationFn: async (filters: ReportFilters) =>
      apiGet(`/reports${buildQueryString(filters, 'json')}`),
  })
}

export function useExportReportXlsx() {
  return useMutation({
    mutationFn: async (filters: ReportFilters) =>
      apiDownload(`/reports${buildQueryString(filters, 'xlsx')}`, 'relatorio-lastro.xlsx'),
  })
}
