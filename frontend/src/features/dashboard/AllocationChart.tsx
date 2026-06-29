import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { assetTypeLabel } from '@/lib/asset-type-labels'
import { formatCents } from '@/lib/format'
import { useAllocation } from './useAllocation'

const COLORS = [
  'var(--primary)',
  'var(--success)',
  'var(--warning)',
  '#60a5fa',
  'var(--destructive)',
]

export function AllocationChart() {
  const { data: allocation, isLoading } = useAllocation()

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Alocação por classe</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Skeleton className="h-[220px] w-full" />
          {Array.from({ length: 3 }).map((_, index) => (
            // biome-ignore lint/suspicious/noArrayIndexKey: placeholder estável, sem identidade própria
            <Skeleton key={index} className="h-8 w-full" />
          ))}
        </CardContent>
      </Card>
    )
  }
  if (!allocation || allocation.length === 0) {
    return <p className="text-muted-foreground">nenhuma posição com cotação ainda</p>
  }

  const chartData = allocation.map((item) => ({
    name: assetTypeLabel(item.asset_type),
    value: item.current_value_cents,
    percentage: item.current_percentage,
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
              nameKey="name"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={2}
              stroke="none"
            >
              {chartData.map((entry, index) => (
                <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value, _name, item) => [
                `${formatCents(Number(value))} (${item.payload.percentage.toFixed(1)}%)`,
                item.payload.name,
              ]}
              contentStyle={{
                background: 'var(--popover)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius)',
                color: 'var(--popover-foreground)',
              }}
            />
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
                  {assetTypeLabel(item.asset_type)}
                </span>
                <span className="flex items-center gap-2 text-muted-foreground">
                  <span className="text-foreground">{item.current_percentage.toFixed(1)}%</span>
                  {item.target_percentage !== null && `meta: ${item.target_percentage}%`}
                  {item.is_deviation_alert && <Badge variant="destructive">desvio</Badge>}
                </span>
              </div>
              <Progress
                value={item.current_percentage}
                indicatorColor={COLORS[index % COLORS.length]}
              />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
