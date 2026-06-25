import { motion } from 'framer-motion'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useFireSimulator } from './useFireSimulator'

function formatCents(cents: number): string {
  return (cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function FireSimulator() {
  const [targetExpense, setTargetExpense] = useState('3000')
  const fireSimulator = useFireSimulator()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    fireSimulator.mutate({ target_monthly_expense_cents: Math.round(Number(targetExpense) * 100) })
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Simulador de independência financeira</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          <div className="flex flex-col gap-1">
            <Label htmlFor="fire-expense">Gasto mensal alvo (R$)</Label>
            <Input
              id="fire-expense"
              type="number"
              value={targetExpense}
              onChange={(e) => setTargetExpense(e.target.value)}
            />
          </div>
          <Button type="submit" disabled={fireSimulator.isPending}>
            Simular
          </Button>
        </form>

        {fireSimulator.data && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col gap-2 text-sm"
          >
            <p>
              Taxa de retirada segura:{' '}
              <span className="font-semibold">
                {fireSimulator.data.safe_withdrawal_rate_pct.toFixed(2)}%
              </span>
            </p>
            <p>
              Renda mensal sustentável hoje:{' '}
              <span className="font-semibold">
                {formatCents(fireSimulator.data.sustainable_monthly_income_cents)}
              </span>
            </p>
            {fireSimulator.data.has_reached_target ? (
              <p className="text-primary">Você já atingiu o gasto-alvo com esse patrimônio.</p>
            ) : (
              fireSimulator.data.missing_portfolio_cents !== null && (
                <p className="text-muted-foreground">
                  Falta {formatCents(fireSimulator.data.missing_portfolio_cents)} de patrimônio para
                  sustentar esse gasto.
                </p>
              )
            )}
          </motion.div>
        )}
      </CardContent>
    </Card>
  )
}
