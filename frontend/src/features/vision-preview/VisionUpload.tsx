import { useRef } from 'react'
import { Button } from '@/components/ui/button'
import { useUploadVisionPreview } from './useVisionPreview'

interface VisionUploadProps {
  cardId: number
}

export function VisionUpload({ cardId }: VisionUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const upload = useUploadVisionPreview()

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    upload.mutate({ cardId, file })
    event.target.value = ''
  }

  return (
    <div className="flex flex-col gap-2">
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />
      <Button
        type="button"
        variant="outline"
        onClick={() => inputRef.current?.click()}
        disabled={upload.isPending}
      >
        {upload.isPending ? 'Lendo fatura...' : 'Lançar por print'}
      </Button>
      {upload.isError && <p className="text-sm text-destructive">{upload.error.message}</p>}
    </div>
  )
}
