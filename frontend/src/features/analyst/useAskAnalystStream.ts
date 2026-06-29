import { useCallback, useRef, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface StreamChunk {
  content: string
  done: boolean
  model: string | null
  tokens_per_second: number | null
}

interface StreamState {
  answer: string
  model: string | null
  tokensPerSecond: number | null
  isStreaming: boolean
  error: string | null
}

const initialState: StreamState = {
  answer: '',
  model: null,
  tokensPerSecond: null,
  isStreaming: false,
  error: null,
}

export function useAskAnalystStream() {
  const [state, setState] = useState<StreamState>(initialState)
  const abortRef = useRef<AbortController | null>(null)

  const ask = useCallback(async (question: string, conversationId: number | null) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setState({ ...initialState, isStreaming: true })
    let answer = ''
    let model: string | null = null
    let tokensPerSecond: number | null = null
    let resolvedConversationId: number | null = conversationId

    try {
      const response = await fetch(`${API_BASE_URL}/analyst/ask/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, conversation_id: conversationId }),
        signal: controller.signal,
      })
      if (!response.ok || !response.body) {
        const body = await response.json().catch(() => null)
        throw new Error(body?.detail ?? `API error: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const events = buffer.split('\n\n')
        buffer = events.pop() ?? ''
        for (const event of events) {
          const line = event.trim()
          if (!line.startsWith('data: ')) continue
          const parsed = JSON.parse(line.slice('data: '.length))
          if (typeof parsed.conversation_id === 'number') {
            resolvedConversationId = parsed.conversation_id
            continue
          }
          const chunk = parsed as StreamChunk
          answer += chunk.content
          model = chunk.model ?? model
          tokensPerSecond = chunk.tokens_per_second ?? tokensPerSecond
          setState((prev) => ({ ...prev, answer, model, tokensPerSecond }))
        }
      }

      setState((prev) => ({ ...prev, isStreaming: false }))
      return { answer, model, tokensPerSecond, conversationId: resolvedConversationId }
    } catch (error) {
      if (controller.signal.aborted) {
        return { answer, model, tokensPerSecond, conversationId: resolvedConversationId }
      }
      setState((prev) => ({
        ...prev,
        isStreaming: false,
        error: error instanceof Error ? error.message : 'Erro desconhecido',
      }))
      return { answer, model, tokensPerSecond, conversationId: resolvedConversationId }
    }
  }, [])

  const reset = useCallback(() => setState(initialState), [])

  return { ...state, ask, reset }
}
