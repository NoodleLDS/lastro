import { Pencil, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { useAnalystInstructions, useUpdateAnalystInstructions } from './useAnalystInstructions'
import { useAnalystMemory } from './useAnalystMemory'

interface AnalystContextPanelProps {
  open: boolean
  onClose: () => void
}

export function AnalystContextPanel({ open, onClose }: AnalystContextPanelProps) {
  const [memoryExpanded, setMemoryExpanded] = useState(false)
  const [editingInstructions, setEditingInstructions] = useState(false)
  const [instructionsDraft, setInstructionsDraft] = useState('')

  const { data: memory } = useAnalystMemory(open)
  const { data: instructions } = useAnalystInstructions()
  const updateInstructions = useUpdateAnalystInstructions()

  useEffect(() => {
    if (editingInstructions && instructions) setInstructionsDraft(instructions.content)
  }, [editingInstructions, instructions])

  if (!open) return null

  const fullMemoryText = memory
    ? `${memory.master_prompt}\n\n# Dados vivos do banco\n\n${memory.portfolio_context}`
    : ''

  function handleSaveInstructions() {
    updateInstructions.mutate(instructionsDraft, { onSuccess: () => setEditingInstructions(false) })
  }

  return (
    <div className="flex w-80 flex-col gap-4 border-l border-border pl-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Contexto do analista</span>
        <button
          type="button"
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground"
        >
          <X className="size-4" />
        </button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Memória</CardTitle>
            <span className="text-xs text-muted-foreground">Apenas leitura</span>
          </div>
        </CardHeader>
        <CardContent>
          {memoryExpanded ? (
            <div className="flex flex-col gap-2">
              <pre className="max-h-80 overflow-y-auto whitespace-pre-wrap text-xs text-muted-foreground">
                {fullMemoryText}
              </pre>
              <button
                type="button"
                onClick={() => setMemoryExpanded(false)}
                className="self-start text-xs text-primary hover:underline"
              >
                Mostrar menos
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <p className="line-clamp-3 text-sm text-muted-foreground">{fullMemoryText}</p>
              <button
                type="button"
                onClick={() => setMemoryExpanded(true)}
                className="self-start text-xs text-primary hover:underline"
              >
                Ver tudo
              </button>
            </div>
          )}
          <p className="mt-2 text-xs text-muted-foreground/60">
            Perfil financeiro, regras de aporte e os dados atuais da carteira que o analista usa em
            toda resposta.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Instruções</CardTitle>
            <button
              type="button"
              onClick={() => setEditingInstructions(true)}
              className="text-muted-foreground hover:text-foreground"
              aria-label="Editar instruções"
            >
              <Pencil className="size-4" />
            </button>
          </div>
        </CardHeader>
        <CardContent>
          {editingInstructions ? (
            <div className="flex flex-col gap-2">
              <Textarea
                value={instructionsDraft}
                onChange={(e) => setInstructionsDraft(e.target.value)}
                rows={6}
                placeholder='Ex.: "responda de forma mais direta" ou "sempre traga 3 cenários".'
              />
              {updateInstructions.isError && (
                <p className="text-xs text-destructive">{updateInstructions.error.message}</p>
              )}
              <div className="flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={() => setEditingInstructions(false)}>
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveInstructions}
                  disabled={updateInstructions.isPending}
                >
                  Salvar
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              {instructions?.content.trim()
                ? instructions.content
                : 'Nenhuma instrução adicional. Complementam a memória acima, sem substituí-la.'}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
