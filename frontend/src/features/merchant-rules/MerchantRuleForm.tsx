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
import { useCategories } from '@/features/categories/useCategories'
import { useCreateMerchantRule } from './useMerchantRules'

export function MerchantRuleForm() {
  const [pattern, setPattern] = useState('')
  const [categoryId, setCategoryId] = useState<string>('')
  const { data: categories } = useCategories()
  const createRule = useCreateMerchantRule()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!categoryId) return
    createRule.mutate(
      { pattern, category_id: Number(categoryId) },
      {
        onSuccess: () => {
          setPattern('')
          setCategoryId('')
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <div className="flex flex-col gap-1">
        <Label htmlFor="rule-pattern">Padrão (contém)</Label>
        <Input
          id="rule-pattern"
          value={pattern}
          onChange={(e) => setPattern(e.target.value)}
          placeholder="uber"
          required
        />
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="rule-category">Categoria</Label>
        <Select value={categoryId} onValueChange={setCategoryId}>
          <SelectTrigger id="rule-category">
            <SelectValue placeholder="selecione" />
          </SelectTrigger>
          <SelectContent>
            {categories?.map((category) => (
              <SelectItem key={category.id} value={String(category.id)}>
                {category.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <Button type="submit" className="self-end" disabled={!pattern || !categoryId}>
        Adicionar
      </Button>
    </form>
  )
}
