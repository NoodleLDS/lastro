import { animate, motion, useMotionValue, useTransform } from 'framer-motion'
import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import { useEffect } from 'react'
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
    <span
      className={cn('inline-flex items-center gap-0.5 tabular-nums', colorBySign[sign], className)}
    >
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

export function PercentValue({
  value,
  showArrow = false,
  digits = 1,
  className,
}: PercentValueProps) {
  const sign = signOf(value)
  const Arrow = ArrowBySign[sign]

  return (
    <span
      className={cn('inline-flex items-center gap-0.5 tabular-nums', colorBySign[sign], className)}
    >
      {showArrow && Arrow && <Arrow className="size-3.5" />}
      {formatPercent(value, digits)}
    </span>
  )
}

interface CountUpMoneyValueProps {
  cents: number
  showArrow?: boolean
  className?: string
}

export function CountUpMoneyValue({ cents, showArrow = false, className }: CountUpMoneyValueProps) {
  const sign = signOf(cents)
  const Arrow = ArrowBySign[sign]
  const value = useMotionValue(0)
  const rounded = useTransform(value, (v) => formatCents(Math.round(v)))

  useEffect(() => {
    const controls = animate(value, cents, { duration: 0.8 })
    return controls.stop
  }, [cents, value])

  return (
    <span
      className={cn('inline-flex items-center gap-1 tabular-nums', colorBySign[sign], className)}
    >
      {showArrow && Arrow && <Arrow className="size-5" />}
      <motion.span>{rounded}</motion.span>
    </span>
  )
}
