/** Public API shapes shared by composables and components. */

export interface SessionRead {
  id: string
  created_at: string
  expires_at: string
  is_expired: boolean
}

export interface MessageRead {
  id: number
  session_id: string
  role: string
  content: string
  created_at: string
}

export type DisplayRole = 'user' | 'assistant'

export interface ChatMessage {
  id?: number
  role: DisplayRole
  content: string
  created_at?: string
}

export type AgentStatus =
  | 'idle'
  | 'connecting'
  | 'thinking'
  | 'searching'
  | 'answer'
  | 'completed'
  | 'error'

export interface WsStatusEvent {
  type: 'status'
  status: 'thinking' | 'searching' | 'answer'
}

export interface WsMessageEvent {
  type: 'message'
  reply: string
  status: 'completed'
}

export interface WsErrorEvent {
  type: 'error'
  detail: string
}

export type WsServerEvent = WsStatusEvent | WsMessageEvent | WsErrorEvent
