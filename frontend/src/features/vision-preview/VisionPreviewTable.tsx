import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useConfirmBatch, usePendingReview, useUpdatePreviewTransaction } from './useVisionPreview'

interface VisionPreviewTableProps {
  cardId: number
}

export function VisionPreviewTable({ cardId }: VisionPreviewTableProps) {
  const { data: pending } = usePendingReview(cardId)
  const updateTransaction = useUpdatePreviewTransaction()
  const confirmBatch = useConfirmBatch()

  if (!pending || pending.length === 0) {
    return null
  }

  const pendingIds = pending.map((t) => t.id)

  return (
    <div className="flex w-full max-w-2xl flex-col gap-3">
      <h3 className="text-sm font-semibold">Revisar fatura</h3>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Descrição</TableHead>
            <TableHead>Valor</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {pending.map((transaction) => (
            <TableRow key={transaction.id}>
              <TableCell>
                <Input
                  defaultValue={transaction.description}
                  onBlur={(e) =>
                    updateTransaction.mutate({
                      id: transaction.id,
                      description: e.target.value,
                    })
                  }
                />
              </TableCell>
              <TableCell>
                <Input
                  type="number"
                  step="0.01"
                  defaultValue={(transaction.amount_cents / 100).toFixed(2)}
                  onBlur={(e) =>
                    updateTransaction.mutate({
                      id: transaction.id,
                      amount_cents: Math.round(Number(e.target.value) * 100),
                    })
                  }
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <Button onClick={() => confirmBatch.mutate(pendingIds)} disabled={confirmBatch.isPending}>
        Confirmar fatura
      </Button>
    </div>
  )
}
