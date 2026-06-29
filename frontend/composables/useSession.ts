/** Session persistence — ties the browser to backend POST/GET /sessions. */

import type { MessageRead, SessionRead } from '~/types/chat'

const SESSION_STORAGE_KEY = 'rehabbot_session_id'

export function useSession() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string

  async function fetchSession(id: string): Promise<SessionRead | null> {
    try {
      return await $fetch<SessionRead>(`${apiBase}/sessions/${id}`)
    } catch {
      return null
    }
  }

  async function createSession(): Promise<SessionRead> {
    return await $fetch<SessionRead>(`${apiBase}/sessions`, { method: 'POST' })
  }

  /** Return a valid session id — reuse localStorage or create a new one. */
  async function ensureSession(): Promise<string> {
    if (import.meta.client) {
      const stored = localStorage.getItem(SESSION_STORAGE_KEY)
      if (stored) {
        const existing = await fetchSession(stored)
        if (existing && !existing.is_expired) {
          return existing.id
        }
      }
    }

    const created = await createSession()
    if (import.meta.client) {
      localStorage.setItem(SESSION_STORAGE_KEY, created.id)
    }
    return created.id
  }

  async function loadMessages(sessionId: string): Promise<MessageRead[]> {
    return await $fetch<MessageRead[]>(`${apiBase}/messages`, {
      query: { session_id: sessionId },
    })
  }

  function clearStoredSession(): void {
    if (import.meta.client) {
      localStorage.removeItem(SESSION_STORAGE_KEY)
    }
  }

  async function listSessions(): Promise<SessionRead[]> {
    try {
      return await $fetch<SessionRead[]>(`${apiBase}/sessions`)
    } catch {
      return []
    }
  }

  async function deleteSession(id: string): Promise<void> {
    await $fetch(`${apiBase}/sessions/${id}`, { method: 'DELETE' })
  }

  return {
    ensureSession,
    loadMessages,
    clearStoredSession,
    createSession,
    listSessions,
    deleteSession,
  }
}
