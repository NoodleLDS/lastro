import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatCents, formatPercent, signOf } from '@/lib/format'

const colorBySign = {
  positive: 'text-success',
  negative: 'text-destructive',
  neutral: 'text-foreground',
} as const

const ArrowBySign = {
  positive: ArrowUpRight,
  negative: ArrowDownRight,
  neutral: null,
} as const

interface MoneyValueProps {
  cents: number
  showArrow?: boolean
  className?: string
}

export function MoneyValue({ cents, showArrow = false, className }: MoneyValueProps) {
  const sign = signOf(cents)
  const Arrow = ArrowBySign[sign]

  return (
    <span className={cn('inline-flex items-center gap-0.5', colorBySign[sign], className)}>
      {showArrow && Arrow && <Arrow className="size-3.5" />}
      {formatCents(cents)}
    </span>
  )
}

interface PercentValueProps {
  value: number
  showArrow?: boolean
  digits?: number
  className?: string
}

export function PercentValue({ value, showArrow = false, digits = 1, className }: PercentValueProps) {
  const sign = signOf(value)
  const Arrow = ArrowBySign[sign]

  return (
    <span className={cn('inline-flex items-center gap-0.5', colorBySign[sign], className)}>
      {showArrow && Arrow && <Arrow className="size-3.5" />}
      {formatPercent(value, digits)}
    </span>
  )
}
