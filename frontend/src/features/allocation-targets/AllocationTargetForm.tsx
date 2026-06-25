import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useCreateAllocationTarget } from './useAllocationTargets'

const ASSET_TYPES = [
  { value: 'stock', label: 'Ação' },
  { value: 'fii', label: 'FII' },
  { value: 'etf', label: 'ETF' },
  { value: 'fixed_income', label: 'Renda fixa' },
  { value: 'crypto', label: 'Cripto' },
]

export function AllocationTargetForm() {
  const [assetType, setAssetType] = useState('')
  const [targetPercentage, setTargetPercentage] = useState('')
  const createTarget = useCreateAllocationTarget()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!assetType || !targetPercentage) return
    createTarget.mutate(
      { asset_type: assetType, target_percentage: Number(targetPercentage) },
      {
        onSuccess: () => {
          setAssetType('')
          setTargetPercentage('')
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2">
      <div className="flex flex-col gap-1">
        <Label htmlFor="target-asset-type">Classe</Label>
        <Select value={assetType} onValueChange={setAssetType}>
          <SelectTrigger id="target-asset-type">
            <SelectValue placeholder="selecione" />
          </SelectTrigger>
          <SelectContent>
            {ASSET_TYPES.map((type) => (
              <SelectItem key={type.value} value={type.value}>
                {type.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="target-percentage">Meta (%)</Label>
        <Input
          id="target-percentage"
          type="number"
          step="0.1"
          value={targetPercentage}
          onChange={(e) => setTargetPercentage(e.target.value)}
          required
        />
      </div>
      <Button type="submit" disabled={createTarget.isPending}>
        Definir meta
      </Button>
    </form>
  )
}
