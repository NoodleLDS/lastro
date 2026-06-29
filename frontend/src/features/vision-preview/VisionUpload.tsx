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
        {upload.isPending ? 'Analisando fatura...' : 'Lançar por print'}
      </Button>
      {upload.isPending && (
        <p className="text-sm text-muted-foreground">
          Modelo local pode levar 1-2 minutos para analisar a imagem. Não recarregue a página.
        </p>
      )}
      {upload.isError && (
        <p className="text-sm text-destructive">
          {upload.error.message === 'Failed to fetch'
            ? 'Não foi possível conectar à API. Verifique se o app (Docker) está rodando e tente novamente.'
            : upload.error.message}
        </p>
      )}
    </div>
  )
}
