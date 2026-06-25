import { animate, motion, useMotionValue, useTransform } from 'framer-motion'
import { useEffect } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useEvolution } from './useEvolution'

function formatCents(cents: number): string {
  return (cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function CountUpValue({ cents }: { cents: number }) {
  const value = useMotionValue(0)
  const rounded = useTransform(value, (v) => formatCents(Math.round(v)))

  useEffect(() => {
    const controls = animate(value, cents, { duration: 0.8 })
    return controls.stop
  }, [cents, value])

  return <motion.span>{rounded}</motion.span>
}

export function EvolutionChart() {
  const { data, isLoading } = useEvolution()

  if (isLoading) return <p className="text-muted-foreground">carregando...</p>
  if (!data || data.points.length === 0) {
    return <p className="text-muted-foreground">nenhum snapshot registrado ainda</p>
  }

  const lastPoint = data.points[data.points.length - 1]
  const chartData = data.points.map((p) => ({
    month: p.month,
    valor: p.portfolio_value_cents / 100,
  }))

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Evolução do patrimônio</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="text-2xl font-semibold">
          <CountUpValue cents={lastPoint.portfolio_value_cents} />
        </p>

        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="month" stroke="var(--muted-foreground)" />
            <YAxis stroke="var(--muted-foreground)" />
            <Tooltip formatter={(value) => formatCents(Number(value) * 100)} />
            <Line type="monotone" dataKey="valor" stroke="var(--primary)" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>

        {data.comparison && (
          <div className="flex gap-4 text-sm text-muted-foreground">
            <span>Carteira: {data.comparison.portfolio_return_pct.toFixed(2)}%</span>
            <span>CDI: {data.comparison.cdi_return_pct.toFixed(2)}%</span>
            {data.comparison.ivvb11_return_pct !== null && (
              <span>IVVB11: {data.comparison.ivvb11_return_pct.toFixed(2)}%</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
