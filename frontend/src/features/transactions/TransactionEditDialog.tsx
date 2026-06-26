import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
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
import type { Transaction } from './useTransactions'
import { useDeleteTransaction, useUpdateTransaction } from './useTransactions'

interface TransactionEditDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  transaction: Transaction | null
}

export function TransactionEditDialog({
  open,
  onOpenChange,
  transaction,
}: TransactionEditDialogProps) {
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [categoryId, setCategoryId] = useState<string>('')
  const { data: categories } = useCategories()
  const updateTransaction = useUpdateTransaction()
  const deleteTransaction = useDeleteTransaction()

  useEffect(() => {
    setDescription(transaction?.description ?? '')
    setAmount(transaction ? String(transaction.amount_cents / 100) : '')
    setCategoryId(transaction?.category_id ? String(transaction.category_id) : '')
  }, [transaction])

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!transaction) return
    updateTransaction.mutate(
      {
        id: transaction.id,
        description,
        amount_cents: Math.round(Number(amount) * 100),
        category_id: categoryId ? Number(categoryId) : undefined,
      },
      { onSuccess: () => onOpenChange(false) },
    )
  }

  function handleDelete() {
    if (!transaction) return
    if (!window.confirm('Remover esta transação? Essa ação não pode ser desfeita.')) return
    deleteTransaction.mutate(transaction.id, { onSuccess: () => onOpenChange(false) })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Editar transação</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="transaction-edit-description">Descrição</Label>
            <Input
              id="transaction-edit-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="transaction-edit-amount">Valor</Label>
            <Input
              id="transaction-edit-amount"
              type="number"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="transaction-edit-category">Categoria</Label>
            <Select value={categoryId} onValueChange={setCategoryId}>
              <SelectTrigger id="transaction-edit-category">
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

          {(updateTransaction.isError || deleteTransaction.isError) && (
            <p className="text-sm text-destructive">
              {updateTransaction.error?.message ?? deleteTransaction.error?.message}
            </p>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteTransaction.isPending}
            >
              {deleteTransaction.isPending ? 'Removendo...' : 'Remover'}
            </Button>
            <Button type="submit" disabled={updateTransaction.isPending}>
              {updateTransaction.isPending ? 'Salvando...' : 'Salvar'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
