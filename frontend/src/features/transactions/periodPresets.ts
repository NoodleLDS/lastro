export type PeriodPreset = 'this_month' | 'last_month' | 'custom'

function toIsoDate(d: Date): string {
  return d.toISOString().slice(0, 10)
}

export function rangeForPreset(preset: PeriodPreset): { dateFrom?: string; dateTo?: string } {
  const now = new Date()

  if (preset === 'this_month') {
    const from = new Date(now.getFullYear(), now.getMonth(), 1)
    const to = new Date(now.getFullYear(), now.getMonth() + 1, 0)
    return { dateFrom: toIsoDate(from), dateTo: toIsoDate(to) }
  }

  if (preset === 'last_month') {
    const from = new Date(now.getFullYear(), now.getMonth() - 1, 1)
    const to = new Date(now.getFullYear(), now.getMonth(), 0)
    return { dateFrom: toIsoDate(from), dateTo: toIsoDate(to) }
  }

  return {}
}
