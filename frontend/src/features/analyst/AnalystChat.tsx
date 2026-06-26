import { Copy, RotateCcw, Sparkle, ThumbsDown, ThumbsUp } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { useAskAnalystStream } from './useAskAnalystStream'

interface Message {
  id: number
  question: string
  answer: string
  model: string | null
  tokensPerSecond: number | null
}

let nextMessageId = 0

export function AnalystChat() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const stream = useAskAnalystStream()

  async function sendQuestion(asked: string, messageId: number) {
    const result = await stream.ask(asked)
    setMessages((prev) =>
      prev.map((message) =>
        message.id === messageId
          ? {
              ...message,
              answer: result.answer,
              model: result.model,
              tokensPerSecond: result.tokensPerSecond,
            }
          : message,
      ),
    )
    stream.reset()
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const asked = question
    setQuestion('')
    const messageId = nextMessageId++
    setMessages((prev) => [
      ...prev,
      { id: messageId, question: asked, answer: '', model: null, tokensPerSecond: null },
    ])
    await sendQuestion(asked, messageId)
  }

  async function handleRegenerate(messageId: number, asked: string) {
    setMessages((prev) =>
      prev.map((message) =>
        message.id === messageId
          ? { ...message, answer: '', model: null, tokensPerSecond: null }
          : message,
      ),
    )
    await sendQuestion(asked, messageId)
  }

  const liveMessageId = messages.length > 0 ? messages[messages.length - 1].id : null
  const isLiveStreaming = stream.isStreaming && liveMessageId !== null

  return (
    <div className="flex h-[calc(100vh-12rem)] w-full max-w-2xl flex-col">
      <div className="flex flex-1 flex-col gap-8 overflow-y-auto pb-4">
        {messages.map((message) => {
          const isLive = isLiveStreaming && message.id === liveMessageId
          const answer = isLive ? stream.answer : message.answer
          const model = isLive ? stream.model : message.model
          const tokensPerSecond = isLive ? stream.tokensPerSecond : message.tokensPerSecond
          const isThinking = isLive && answer.length === 0

          return (
            <div key={message.id} className="flex flex-col gap-3">
              <p className="text-sm text-muted-foreground">{message.question}</p>

              {isThinking ? (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Sparkle className="size-4 animate-spin text-primary" />
                  <span className="text-sm italic">Processando, aguarde um momento...</span>
                </div>
              ) : (
                <p className="whitespace-pre-wrap leading-relaxed">
                  {answer}
                  {isLive && (
                    <span className="ml-0.5 inline-block w-2 animate-pulse text-primary">▋</span>
                  )}
                </p>
              )}

              {!isThinking && answer.length > 0 && (
                <div className="flex items-center gap-3 text-muted-foreground">
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText(answer)}
                    className="hover:text-foreground"
                    aria-label="Copiar resposta"
                  >
                    <Copy className="size-4" />
                  </button>
                  <button type="button" className="hover:text-foreground" aria-label="Gostei">
                    <ThumbsUp className="size-4" />
                  </button>
                  <button type="button" className="hover:text-foreground" aria-label="Não gostei">
                    <ThumbsDown className="size-4" />
                  </button>
                  {message.id === liveMessageId && (
                    <button
                      type="button"
                      onClick={() => handleRegenerate(message.id, message.question)}
                      disabled={stream.isStreaming}
                      className="hover:text-foreground disabled:opacity-50"
                      aria-label="Tentar de novo"
                    >
                      <RotateCcw className="size-4" />
                    </button>
                  )}
                  {(model || tokensPerSecond) && (
                    <span className="ml-2 text-xs text-muted-foreground/60">
                      {model}
                      {model && tokensPerSecond ? ' · ' : ''}
                      {tokensPerSecond ? `${tokensPerSecond.toFixed(1)} tokens/s` : ''}
                    </span>
                  )}
                </div>
              )}
            </div>
          )
        })}

        {messages.length === 0 && (
          <div className="flex flex-1 items-center justify-center text-muted-foreground">
            <p className="text-sm">Pergunte sobre sua carteira, um ativo, ou peça uma simulação.</p>
          </div>
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-2 rounded-2xl border border-border bg-card p-3"
      >
        <Textarea
          placeholder="Escreva uma mensagem..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={1}
          className="resize-none border-none bg-transparent px-1 shadow-none focus-visible:ring-0"
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              handleSubmit(event)
            }
          }}
        />
        <div className="flex items-center justify-end gap-2">
          {stream.isStreaming && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Sparkle className="size-3 animate-spin text-primary" />
              pensando...
            </span>
          )}
          <Button
            type="submit"
            size="sm"
            className={cn('rounded-full', !question.trim() && 'opacity-50')}
            disabled={stream.isStreaming || !question.trim()}
          >
            Perguntar
          </Button>
        </div>
      </form>

      {stream.error && <p className="mt-2 text-sm text-destructive">{stream.error}</p>}
    </div>
  )
}
