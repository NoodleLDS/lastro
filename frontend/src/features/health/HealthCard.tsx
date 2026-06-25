import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useHealth } from './useHealth'

export function HealthCard() {
  const { data, isLoading, isError } = useHealth()

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>API status</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && <p className="text-muted-foreground">checando...</p>}
        {isError && <p className="text-destructive">não foi possível conectar à API</p>}
        {data && <p className="text-foreground">{data.status}</p>}
      </CardContent>
    </Card>
  )
}
