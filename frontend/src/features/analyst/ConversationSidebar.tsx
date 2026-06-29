import { Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { useConversations, useDeleteConversation } from './useConversations'

interface ConversationSidebarProps {
  selectedId: number | null
  onSelect: (id: number | null) => void
}

export function ConversationSidebar({ selectedId, onSelect }: ConversationSidebarProps) {
  const { data: conversations } = useConversations()
  const deleteConversation = useDeleteConversation()

  function handleDelete(event: React.MouseEvent, id: number) {
    event.stopPropagation()
    deleteConversation.mutate(id, {
      onSuccess: () => {
        if (selectedId === id) onSelect(null)
      },
    })
  }

  return (
    <div className="flex w-56 flex-col gap-2 border-r border-border pr-3">
      <Button
        variant="outline"
        size="sm"
        className="justify-start gap-2"
        onClick={() => onSelect(null)}
      >
        <Plus className="size-4" />
        Nova conversa
      </Button>

      <div className="flex flex-col gap-1 overflow-y-auto">
        {conversations?.map((conversation) => (
          <button
            type="button"
            key={conversation.id}
            onClick={() => onSelect(conversation.id)}
            className={cn(
              'group flex items-center justify-between rounded-md px-2 py-2 text-left text-sm hover:bg-accent',
              selectedId === conversation.id && 'bg-accent',
            )}
          >
            <span className="truncate">{conversation.title}</span>
            <button
              type="button"
              onClick={(event) => handleDelete(event, conversation.id)}
              className="ml-2 shrink-0 text-muted-foreground opacity-0 hover:text-destructive group-hover:opacity-100"
              aria-label="Excluir conversa"
            >
              <Trash2 className="size-3.5" />
            </button>
          </button>
        ))}
      </div>
    </div>
  )
}
