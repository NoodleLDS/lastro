import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { useAskAnalyst } from './useAskAnalyst'

interface Message {
  id: number
  question: string
  answer: string
}

let nextMessageId = 0

export function AnalystChat() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const askAnalyst = useAskAnalyst()

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const asked = question
    askAnalyst.mutate(asked, {
      onSuccess: (data) => {
        setMessages((prev) => [
          ...prev,
          { id: nextMessageId++, question: asked, answer: data.answer },
        ])
        setQuestion('')
      },
    })
  }

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Analista</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-4">
          {messages.map((message) => (
            <div key={message.id} className="flex flex-col gap-1">
              <p className="font-medium">{message.question}</p>
              <p className="whitespace-pre-wrap text-sm text-muted-foreground">{message.answer}</p>
            </div>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-2">
          <Textarea
            placeholder="Pergunte sobre sua carteira, um ativo, ou peça uma simulação..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
          />
          <Button type="submit" disabled={askAnalyst.isPending || !question.trim()}>
            {askAnalyst.isPending ? 'Pensando...' : 'Perguntar'}
          </Button>
        </form>

        {askAnalyst.isError && (
          <p className="text-sm text-destructive">{askAnalyst.error.message}</p>
        )}
      </CardContent>
    </Card>
  )
}
