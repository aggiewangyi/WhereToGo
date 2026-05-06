import { agentHeaders, getToken } from './api'
import api from './api'

export type ChatHistoryTurn = { role: 'user' | 'assistant'; content: string }

export type AgentChatOptions = {
  session_id?: string | null
  history?: ChatHistoryTurn[]
  stream?: boolean
  interaction_mode?: 'verbose' | 'quiet' | null
}

export type AgentSessionRow = {
  id: string
  title: string | null
  updated_at: string
}

export type AgentHistoryMessage = {
  role: string
  content: string
  created_at: string
}

function streamHeaders(): Record<string, string> {
  const h: Record<string, string> = {
    'Content-Type': 'application/json',
    ...agentHeaders(),
  }
  const t = getToken()
  if (t) h.Authorization = `Bearer ${t}`
  return h
}

export async function listAgentSessions(): Promise<AgentSessionRow[]> {
  const { data } = await api.get<AgentSessionRow[]>('/agent/sessions')
  return data
}

export async function getAgentSessionMessages(sessionId: string): Promise<{
  session_id: string
  messages: AgentHistoryMessage[]
}> {
  const { data } = await api.get(`/agent/sessions/${encodeURIComponent(sessionId)}/messages`)
  return data
}

/** 阻塞式整段回复 */
export async function agentChatBlocking(message: string, options?: AgentChatOptions) {
  const res = await fetch('/api/v1/agent/chat', {
    method: 'POST',
    headers: streamHeaders(),
    body: JSON.stringify({
      message,
      stream: false,
      session_id: options?.session_id || undefined,
      history: options?.history,
      interaction_mode: options?.interaction_mode,
    }),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json() as Promise<{ type: string; content: string; session_id: string }>
}

/** SSE */
export function agentChatStream(message: string, options?: AgentChatOptions) {
  const { session_id, history, interaction_mode } = options || {}
  return fetch('/api/v1/agent/chat', {
    method: 'POST',
    headers: streamHeaders(),
    body: JSON.stringify({
      message,
      stream: true,
      ...(session_id ? { session_id } : {}),
      history,
      interaction_mode,
    }),
  })
}
