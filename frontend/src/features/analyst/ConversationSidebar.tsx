import { Pencil, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { useConversations, useDeleteConversation, useRenameConversation } from './useConversations'

interface ConversationSidebarProps {
  selectedId: number | null
  onSelect: (id: number | null) => void
}

export function ConversationSidebar({ selectedId, onSelect }: ConversationSidebarProps) {
  const { data: conversations } = useConversations()
  const deleteConversation = useDeleteConversation()
  const renameConversation = useRenameConversation()
  const [editingId, setEditingId] = useState<number | null>(null)
  const [titleDraft, setTitleDraft] = useState('')

  function handleDelete(event: React.MouseEvent, id: number) {
    event.stopPropagation()
    deleteConversation.mutate(id, {
      onSuccess: () => {
        if (selectedId === id) onSelect(null)
      },
    })
  }

  function startEditing(event: React.MouseEvent, id: number, currentTitle: string) {
    event.stopPropagation()
    setEditingId(id)
    setTitleDraft(currentTitle)
  }

  function commitRename(id: number) {
    const title = titleDraft.trim()
    setEditingId(null)
    if (title.length === 0) return
    renameConversation.mutate({ id, title })
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
        {conversations?.map((conversation) =>
          editingId === conversation.id ? (
            <Input
              key={conversation.id}
              autoFocus
              value={titleDraft}
              onChange={(e) => setTitleDraft(e.target.value)}
              onBlur={() => commitRename(conversation.id)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') commitRename(conversation.id)
                if (event.key === 'Escape') setEditingId(null)
              }}
              className="h-9 text-sm"
            />
          ) : (
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
              <span className="ml-2 flex shrink-0 items-center gap-1 text-muted-foreground opacity-0 group-hover:opacity-100">
                <button
                  type="button"
                  onClick={(event) => startEditing(event, conversation.id, conversation.title)}
                  className="hover:text-foreground"
                  aria-label="Renomear conversa"
                >
                  <Pencil className="size-3.5" />
                </button>
                <button
                  type="button"
                  onClick={(event) => handleDelete(event, conversation.id)}
                  className="hover:text-destructive"
                  aria-label="Excluir conversa"
                >
                  <Trash2 className="size-3.5" />
                </button>
              </span>
            </button>
          ),
        )}
      </div>
    </div>
  )
}
