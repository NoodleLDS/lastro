import { useEffect, useState } from 'react'
import { QuickEntryInput } from '@/features/quick-entry/QuickEntryInput'
import { VisionPreviewTable } from '@/features/vision-preview/VisionPreviewTable'
import { VisionUpload } from '@/features/vision-preview/VisionUpload'
import { CardMonthSpending } from './CardMonthSpending'

export function CardWorkspace({ cardId, cardName }: { cardId: number; cardName: string }) {
  const [{ year, month }, setReference] = useState(() => {
    const now = new Date()
    return { year: now.getFullYear(), month: now.getMonth() + 1 }
  })

  // biome-ignore lint/correctness/useExhaustiveDependencies: cardId dispara o reset de mês ao trocar de cartão, mesmo sem ser lido no corpo
  useEffect(() => {
    const now = new Date()
    setReference({ year: now.getFullYear(), month: now.getMonth() + 1 })
  }, [cardId])

  return (
    <>
      <QuickEntryInput
        cardId={cardId}
        cardName={cardName}
        referenceYear={year}
        referenceMonth={month}
      />
      <VisionUpload cardId={cardId} />
      <VisionPreviewTable cardId={cardId} />
      <CardMonthSpending
        cardId={cardId}
        year={year}
        month={month}
        onReferenceChange={setReference}
      />
    </>
  )
}
