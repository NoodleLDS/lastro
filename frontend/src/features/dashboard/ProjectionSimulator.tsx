import { useState } from 'react'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useProjection } from './useProjection'

function formatCents(cents: number): string {
  return (cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function ProjectionSimulator() {
  const [monthlyContribution, setMonthlyContribution] = useState('3200')
  const [monthlyReturn, setMonthlyReturn] = useState('0.8')
  const [months, setMonths] = useState('24')
  const projection = useProjection()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    projection.mutate({
      monthly_contribution_cents: Math.round(Number(monthlyContribution) * 100),
      monthly_return_rate: Number(monthlyReturn) / 100,
      months: Number(months),
    })
  }

  const chartData = projection.data?.values_cents.map((cents, index) => ({
    month: index,
    valor: cents / 100,
  }))

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Simulador de projeção</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
          <div className="flex flex-col gap-1">
            <Label htmlFor="projection-contribution">Aporte mensal (R$)</Label>
            <Input
              id="projection-contribution"
              type="number"
              value={monthlyContribution}
              onChange={(e) => setMonthlyContribution(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="projection-rate">Retorno esperado (% a.m.)</Label>
            <Input
              id="projection-rate"
              type="number"
              step="0.1"
              value={monthlyReturn}
              onChange={(e) => setMonthlyReturn(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="projection-months">Meses</Label>
            <Input
              id="projection-months"
              type="number"
              value={months}
              onChange={(e) => setMonths(e.target.value)}
            />
          </div>
          <Button type="submit" disabled={projection.isPending}>
            Simular
          </Button>
        </form>

        {chartData && (
          <>
            <p className="text-lg font-semibold">
              {formatCents(projection.data?.values_cents.at(-1) ?? 0)}
            </p>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <XAxis dataKey="month" stroke="var(--muted-foreground)" />
                <YAxis stroke="var(--muted-foreground)" />
                <Tooltip formatter={(value) => formatCents(Number(value) * 100)} />
                <Line type="monotone" dataKey="valor" stroke="var(--primary)" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </>
        )}
      </CardContent>
    </Card>
  )
}
