import { Settings } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { useRestartContainers, useShutdownContainers } from './useAdmin'

export function AdminMenu() {
  const [open, setOpen] = useState(false)
  const restart = useRestartContainers()
  const shutdown = useShutdownContainers()

  const isBusy = restart.isPending || shutdown.isPending

  function handleRestart() {
    restart.mutate(undefined, { onSuccess: () => setOpen(false) })
  }

  function handleShutdown() {
    shutdown.mutate(undefined, { onSuccess: () => setOpen(false) })
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon" aria-label="Configurações">
          <Settings className="size-4" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Configurações</DialogTitle>
          <DialogDescription>Controle dos containers Docker do Lastro.</DialogDescription>
        </DialogHeader>

        {restart.isError && <p className="text-sm text-destructive">{restart.error.message}</p>}
        {shutdown.isError && <p className="text-sm text-destructive">{shutdown.error.message}</p>}
        {restart.isSuccess && (
          <p className="text-sm text-muted-foreground">
            Reiniciando os containers... a página vai recarregar em alguns segundos.
          </p>
        )}
        {shutdown.isSuccess && (
          <p className="text-sm text-muted-foreground">Containers sendo encerrados.</p>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={handleRestart} disabled={isBusy}>
            Reiniciar containers
          </Button>
          <Button variant="destructive" onClick={handleShutdown} disabled={isBusy}>
            Sair (desliga os containers)
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
