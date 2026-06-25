export function formatCents(cents: number): string {
  return (cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function formatPercent(value: number, digits = 1): string {
  return `${value.toFixed(digits)}%`
}

export type ValueSign = 'positive' | 'negative' | 'neutral'

export function signOf(value: number): ValueSign {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}
