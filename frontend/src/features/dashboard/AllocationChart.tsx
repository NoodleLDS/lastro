import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { formatCents } from '@/lib/format'
import { useAllocation } from './useAllocation'

const COLORS = ['var(--primary)', 'var(--success)', 'var(--warning)', '#60a5fa', 'var(--destructive)']

export function AllocationChart() {
  const { data: allocation, isLoading } = useAllocation()

  if (isLoading) return <p className="text-muted-foreground">carregando...</p>
  if (!allocation || allocation.length === 0) {
    return <p className="text-muted-foreground">nenhuma posição com cotação ainda</p>
  }

  const chartData = allocation.map((item) => ({
    name: item.asset_type,
    value: item.current_value_cents,
    label: `${item.asset_type} ${item.current_percentage.toFixed(1)}%`,
  }))

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Alocação por classe</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="label"
              outerRadius={80}
              label={({ name }) => name}
            >
              {chartData.map((entry, index) => (
                <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => formatCents(Number(value))} />
          </PieChart>
        </ResponsiveContainer>

        <div className="flex flex-col gap-3">
          {allocation.map((item, index) => (
            <div key={item.asset_type} className="flex flex-col gap-1">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 font-medium">
                  <span
                    className="size-2 rounded-full"
                    style={{ background: COLORS[index % COLORS.length] }}
                  />
                  {item.asset_type}
                </span>
                <span>
                  {item.current_percentage.toFixed(1)}%
                  {item.target_percentage !== null && ` (meta: ${item.target_percentage}%)`}
                  {item.is_deviation_alert && (
                    <Badge variant="destructive" className="ml-2">
                      desvio
                    </Badge>
                  )}
                </span>
              </div>
              <Progress value={item.current_percentage} />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
