<script setup lang="ts">
import type {
  AgentStatus,
  ChatMessage,
  WsServerEvent,
} from '~/types/chat'

const props = defineProps<{
  sessionId: string
}>()

const config = useRuntimeConfig()
const { loadMessages } = useSession()

const wsUrl = `${config.public.wsBase}/ws/chat`

const messages = ref<ChatMessage[]>([])
const draft = ref('')
const status = ref<AgentStatus>('idle')
const errorDetail = ref<string | null>(null)

let socket: WebSocket | null = null

const statusLabel = computed(() => {
  switch (status.value) {
    case 'connecting':
      return 'Connexion…'
    case 'thinking':
      return 'Réflexion…'
    case 'searching':
      return 'Recherche de sources fiables…'
    case 'answer':
      return 'Rédaction de la réponse…'
    case 'error':
      return 'Erreur'
    default:
      return ''
  }
})

const isBusy = computed(
  () =>
    status.value === 'connecting' ||
    status.value === 'thinking' ||
    status.value === 'searching' ||
    status.value === 'answer',
)

function toDisplayMessages(rows: Awaited<ReturnType<typeof loadMessages>>): ChatMessage[] {
  return rows
    .filter((row) => row.role === 'user' || row.role === 'assistant')
    .map((row) => ({
      id: row.id,
      role: row.role as ChatMessage['role'],
      content: row.content,
      created_at: row.created_at,
    }))
}

async function refreshHistory() {
  const rows = await loadMessages(props.sessionId)
  messages.value = toDisplayMessages(rows)
}

function connectSocket() {
  if (!import.meta.client) return

  status.value = 'connecting'
  socket = new WebSocket(wsUrl)

  socket.onopen = () => {
    status.value = 'idle'
    errorDetail.value = null
  }

  socket.onmessage = (event) => {
    const payload = JSON.parse(event.data) as WsServerEvent

    if (payload.type === 'status') {
      status.value = payload.status
      return
    }

    if (payload.type === 'error') {
      status.value = 'error'
      errorDetail.value = payload.detail
      return
    }

    if (payload.type === 'message') {
      messages.value.push({
        role: 'assistant',
        content: payload.reply,
      })
      status.value = 'completed'
      nextTick(scrollToBottom)
    }
  }

  socket.onerror = () => {
    status.value = 'error'
    errorDetail.value = 'Connexion WebSocket interrompue.'
  }

  socket.onclose = () => {
    if (status.value !== 'error') {
      status.value = 'idle'
    }
  }
}

function scrollToBottom() {
  const el = document.getElementById('chat-scroll')
  if (el) {
    el.scrollTop = el.scrollHeight
  }
}

async function sendMessage() {
  const text = draft.value.trim()
  if (!text || isBusy.value) return

  if (!socket || socket.readyState !== WebSocket.OPEN) {
    connectSocket()
    await new Promise<void>((resolve) => {
      const check = () => {
        if (socket?.readyState === WebSocket.OPEN) resolve()
        else setTimeout(check, 50)
      }
      check()
    })
  }

  messages.value.push({ role: 'user', content: text })
  draft.value = ''
  status.value = 'thinking'
  errorDetail.value = null
  nextTick(scrollToBottom)

  socket?.send(
    JSON.stringify({
      session_id: props.sessionId,
      content: text,
    }),
  )
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

onMounted(async () => {
  await refreshHistory()
  connectSocket()
  nextTick(scrollToBottom)
})

onBeforeUnmount(() => {
  socket?.close()
})
</script>

<template>
  <div class="chatbot">
    <div id="chat-scroll" class="chatbot__messages" aria-live="polite">
      <p v-if="messages.length === 0" class="chatbot__empty">
        Posez une question sur la rééducation (ex. lombalgie, genou, épaule).
        RehabBot consulte des sources publiques fiables via le serveur MCP.
      </p>

      <article
        v-for="(msg, index) in messages"
        :key="msg.id ?? `local-${index}`"
        class="chatbot__bubble"
        :class="`chatbot__bubble--${msg.role}`"
      >
        <span class="chatbot__role">
          {{ msg.role === 'user' ? 'Vous' : 'RehabBot' }}
        </span>
        <p class="chatbot__text">{{ msg.content }}</p>
      </article>

      <p v-if="isBusy && statusLabel" class="chatbot__status">
        <span class="chatbot__spinner" aria-hidden="true" />
        {{ statusLabel }}
      </p>

      <p v-if="errorDetail" class="chatbot__error" role="alert">
        {{ errorDetail }}
      </p>
    </div>

    <form class="chatbot__form" @submit.prevent="sendMessage">
      <textarea
        v-model="draft"
        class="chatbot__input"
        rows="2"
        placeholder="Décrivez votre question ou votre zone douloureuse…"
        :disabled="isBusy"
        aria-label="Votre message"
        @keydown="onKeydown"
      />
      <button class="chatbot__send" type="submit" :disabled="isBusy || !draft.trim()">
        Envoyer
      </button>
    </form>
  </div>
</template>

<style scoped>
.chatbot {
  display: flex;
  flex-direction: column;
  height: min(70vh, 640px);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
}

.chatbot__messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chatbot__empty {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.95rem;
}

.chatbot__bubble {
  max-width: 85%;
  padding: 0.75rem 1rem;
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
}

.chatbot__bubble--user {
  align-self: flex-end;
  background: var(--color-user-bubble);
}

.chatbot__bubble--assistant {
  align-self: flex-start;
  background: var(--color-bot-bubble);
}

.chatbot__role {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-muted);
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.chatbot__text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.chatbot__status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
  color: var(--color-primary);
  font-size: 0.9rem;
}

.chatbot__spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.chatbot__error {
  margin: 0;
  padding: 0.75rem;
  background: #fdecea;
  border: 1px solid #f5c2c0;
  border-radius: var(--radius);
  color: #8a1f17;
  font-size: 0.9rem;
}

.chatbot__form {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  border-top: 1px solid var(--color-border);
  background: #fafcfc;
}

.chatbot__input {
  flex: 1;
  resize: vertical;
  min-height: 2.75rem;
  padding: 0.65rem 0.85rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 1rem;
}

.chatbot__input:focus {
  outline: 2px solid var(--color-accent);
  outline-offset: 1px;
}

.chatbot__send {
  align-self: flex-end;
  padding: 0.65rem 1.25rem;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-weight: 600;
  cursor: pointer;
}

.chatbot__send:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.chatbot__send:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>
