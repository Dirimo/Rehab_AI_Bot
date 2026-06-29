<script setup lang="ts">
import type {
  AgentStatus,
  ChatMessage,
  WsServerEvent,
} from '~/types/chat'
import { formatMessageHtml } from '~/utils/formatMessage'

const props = defineProps<{
  sessionId: string
  initialMessage?: string
}>()

const emit = defineEmits<{
  (e: 'sessionUpdated'): void
}>()

const config = useRuntimeConfig()
const { loadMessages } = useSession()

const EXAMPLE_PROMPTS = [
  'Exercices pour lombalgie',
  'Rééducation épaule',
  'Conseils genou arthrose',
  'Sources HAS dos',
]

const wsUrl = `${config.public.wsBase}/ws/chat`

const messages = ref<ChatMessage[]>([])
const draft = ref('')
const status = ref<AgentStatus>('idle')
const toastMessage = ref<string | null>(null)
const isLoadingHistory = ref(true)
const userScrolledUp = ref(false)
const copiedIndex = ref<number | null>(null)

let socket: WebSocket | null = null
let toastTimer: ReturnType<typeof setTimeout> | null = null

const isBusy = computed(
  () =>
    status.value === 'connecting' ||
    status.value === 'thinking' ||
    status.value === 'searching' ||
    status.value === 'answer',
)

function renderMessageHtml(content: string): string {
  return formatMessageHtml(content)
}

function showToast(message: string) {
  toastMessage.value = message
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastMessage.value = null
  }, 4000)
}

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
  isLoadingHistory.value = true
  try {
    const rows = await loadMessages(props.sessionId)
    messages.value = toDisplayMessages(rows)
  } finally {
    isLoadingHistory.value = false
    nextTick(() => scrollToBottom(true))
  }
}

function connectSocket() {
  if (!import.meta.client) return

  status.value = 'connecting'
  socket = new WebSocket(wsUrl)

  socket.onopen = () => {
    status.value = 'idle'
  }

  socket.onmessage = (event) => {
    const payload = JSON.parse(event.data) as WsServerEvent

    if (payload.type === 'status') {
      status.value = payload.status
      return
    }

    if (payload.type === 'error') {
      status.value = 'error'
      showToast(payload.detail)
      return
    }

    if (payload.type === 'message') {
      messages.value.push({
        role: 'assistant',
        content: payload.reply,
      })
      status.value = 'completed'
      nextTick(() => scrollToBottom())
      emit('sessionUpdated')
    }
  }

  socket.onerror = () => {
    status.value = 'error'
    showToast('Connexion WebSocket interrompue.')
  }

  socket.onclose = () => {
    if (status.value !== 'error') {
      status.value = 'idle'
    }
  }
}

function onMessagesScroll(event: Event) {
  const el = event.target as HTMLElement
  const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
  userScrolledUp.value = distanceFromBottom > 80
}

function scrollToBottom(force = false) {
  if (!force && userScrolledUp.value) return
  const el = document.getElementById('chat-scroll')
  if (el) {
    el.scrollTop = el.scrollHeight
  }
}

async function ensureSocketOpen() {
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
}

async function sendContent(text: string, showUserBubble = true, force = false) {
  const trimmed = text.trim()
  if (!trimmed || (!force && isBusy.value)) return

  await ensureSocketOpen()

  if (showUserBubble) {
    messages.value.push({ role: 'user', content: trimmed })
  }
  draft.value = ''
  status.value = 'thinking'
  userScrolledUp.value = false
  nextTick(() => scrollToBottom(true))

  socket?.send(
    JSON.stringify({
      session_id: props.sessionId,
      content: trimmed,
    }),
  )
}

async function sendMessage() {
  await sendContent(draft.value)
}

function usePrompt(prompt: string) {
  draft.value = prompt
  sendMessage()
}

function regenerate(assistantIndex: number) {
  for (let i = assistantIndex - 1; i >= 0; i--) {
    const msg = messages.value[i]
    if (msg?.role === 'user') {
      sendContent(msg.content, false)
      return
    }
  }
}

async function copyMessage(index: number, text: string) {
  try {
    await navigator.clipboard.writeText(text)
    copiedIndex.value = index
    setTimeout(() => {
      if (copiedIndex.value === index) copiedIndex.value = null
    }, 2000)
  } catch {
    showToast('Impossible de copier le texte.')
  }
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
  if (props.initialMessage?.trim()) {
    await sendContent(props.initialMessage.trim(), true, true)
  }
})

onBeforeUnmount(() => {
  socket?.close()
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<template>
  <div class="chatbot">
    <div
      id="chat-scroll"
      class="chatbot__messages"
      aria-live="polite"
      @scroll="onMessagesScroll"
    >
      <!-- Loading skeleton -->
      <template v-if="isLoadingHistory">
        <div v-for="n in 3" :key="`skel-${n}`" class="chatbot__skeleton" :class="{ 'chatbot__skeleton--right': n === 2 }" />
      </template>

      <template v-else>
        <p v-if="messages.length === 0" class="chatbot__empty">
          Posez une question sur la rééducation. RehabBot consulte HAS, NHS,
          MedlinePlus et d'autres sources via le serveur MCP.
        </p>

        <article
          v-for="(msg, index) in messages"
          :key="msg.id ?? `local-${index}`"
          class="chatbot__bubble"
          :class="`chatbot__bubble--${msg.role}`"
          :aria-label="msg.role === 'user' ? 'Message utilisateur' : 'Message assistant'"
        >
          <span class="chatbot__role">
            {{ msg.role === 'user' ? 'Vous' : 'RehabBot' }}
          </span>
          <div class="chatbot__text" v-html="renderMessageHtml(msg.content)" />

          <div v-if="msg.role === 'assistant'" class="chatbot__actions">
            <button
              type="button"
              class="chatbot__action-btn"
              title="Copier"
              :aria-label="copiedIndex === index ? 'Copié' : 'Copier la réponse'"
              @click="copyMessage(index, msg.content)"
            >
              <span v-if="copiedIndex === index" class="chatbot__copied">Copié !</span>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <rect x="9" y="9" width="11" height="11" rx="2" stroke="currentColor" stroke-width="1.75" />
                <path d="M5 15V5a2 2 0 0 1 2-2h10" stroke="currentColor" stroke-width="1.75" />
              </svg>
            </button>
            <button
              type="button"
              class="chatbot__action-btn"
              title="Régénérer"
              aria-label="Régénérer la réponse"
              :disabled="isBusy"
              @click="regenerate(index)"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M4 12a8 8 0 0 1 13.66-5.66M20 12a8 8 0 0 1-13.66 5.66" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" />
                <path d="M20 4v4h-4M4 20v-4h4" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
          </div>
        </article>

        <!-- Typing indicator (3 dots) -->
        <article
          v-if="isBusy"
          class="chatbot__bubble chatbot__bubble--assistant chatbot__bubble--typing"
          aria-label="RehabBot rédige une réponse"
        >
          <span class="chatbot__role">RehabBot</span>
          <div class="chatbot__dots" aria-hidden="true">
            <span /><span /><span />
          </div>
          <span class="sr-only">
            {{ status === 'searching' ? 'Recherche de sources…' : 'Réflexion en cours…' }}
          </span>
        </article>
      </template>
    </div>

    <!-- Fixed input card (ChatTide §6) -->
    <div class="chatbot__input-area">
      <div class="chatbot__chips" role="list" aria-label="Suggestions">
        <button
          v-for="prompt in EXAMPLE_PROMPTS"
          :key="prompt"
          type="button"
          class="chatbot__chip"
          role="listitem"
          :disabled="isBusy"
          @click="usePrompt(prompt)"
        >
          {{ prompt }}
        </button>
      </div>

      <div class="chatbot__card">
        <textarea
          v-model="draft"
          class="chatbot__input"
          rows="2"
          placeholder="🧩 Posez votre question de rééducation…"
          :disabled="isBusy"
          aria-label="Votre message"
          @keydown="onKeydown"
        />
        <div class="chatbot__card-actions">
          <button
            class="chatbot__send"
            type="button"
            :class="{ 'chatbot__send--active': draft.trim() && !isBusy }"
            :disabled="isBusy || !draft.trim()"
            aria-label="Envoyer"
            @click="sendMessage"
          >
            <span v-if="isBusy" class="chatbot__send-spinner" aria-hidden="true" />
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M12 19V5M6 11l6-6 6 6" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toastMessage" class="chatbot__toast" role="alert">
        {{ toastMessage }}
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.chatbot {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  position: relative;
}

.chatbot__messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 0 1rem;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scroll-behavior: smooth;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
}

.chatbot__empty {
  margin: auto;
  max-width: 28rem;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.95rem;
  line-height: 1.6;
}

.chatbot__skeleton {
  height: 72px;
  max-width: 70%;
  border-radius: var(--radius-card);
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.chatbot__skeleton--right {
  align-self: flex-end;
  max-width: 45%;
}

.chatbot__bubble {
  max-width: 85%;
  padding: 0.85rem 1.1rem;
  border-radius: var(--radius-card);
  animation: message-in var(--transition-fast) ease-out;
  transition: transform var(--transition-fast);
}

.chatbot__bubble:hover {
  transform: scale(1.01);
}

.chatbot__bubble--user {
  align-self: flex-end;
  background: var(--color-user-bubble);
  color: #fff;
  box-shadow: var(--shadow-soft);
}

.chatbot__bubble--assistant {
  align-self: flex-start;
  background: var(--color-bot-bubble);
  border: 1px solid var(--color-border-subtle);
  box-shadow: var(--shadow-card);
}

.chatbot__bubble--typing {
  padding-bottom: 1rem;
}

.chatbot__role {
  display: block;
  font-family: var(--font-heading);
  font-size: 0.85rem;
  font-weight: 400;
  margin-bottom: 0.35rem;
}

.chatbot__bubble--user .chatbot__role {
  color: rgba(255, 255, 255, 0.7);
}

.chatbot__bubble--assistant .chatbot__role {
  color: var(--color-text-muted);
}

.chatbot__text {
  margin: 0;
  font-size: 1rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.chatbot__text :deep(strong) {
  font-weight: 700;
}

.chatbot__text :deep(.msg-h3) {
  margin: 0.85rem 0 0.4rem;
  font-family: var(--font-heading);
  font-size: 1.35rem;
  font-weight: 400;
  line-height: 1.35;
  color: var(--color-text);
}

.chatbot__text :deep(.msg-h3:first-child) {
  margin-top: 0;
}

.chatbot__bubble--user .chatbot__text :deep(.msg-h3) {
  color: #fff;
}

.chatbot__bubble--user .chatbot__text :deep(strong) {
  color: #fff;
}

.chatbot__text :deep(.msg-link) {
  color: #0284c7;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.chatbot__text :deep(.msg-link:hover) {
  opacity: 0.8;
}

.chatbot__bubble--user .chatbot__text :deep(.msg-link) {
  color: #93c5fd;
}

.chatbot__actions {
  display: flex;
  gap: 0.25rem;
  margin-top: 0.65rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border-subtle);
}

.chatbot__action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  min-height: 44px;
  padding: 0.4rem;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm, 8px);
  color: var(--color-text-muted);
  transition: background var(--transition-fast), color var(--transition-fast);
}

.chatbot__action-btn:hover:not(:disabled) {
  background: var(--color-bg);
  color: var(--color-text);
}

.chatbot__action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.chatbot__copied {
  font-size: 0.75rem;
  font-weight: 600;
  color: #16a34a;
}

.chatbot__dots {
  display: flex;
  gap: 5px;
  padding: 0.25rem 0;
}

.chatbot__dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-sky-accent);
  animation: dot-pulse 1.2s infinite ease-in-out;
}

.chatbot__dots span:nth-child(2) {
  animation-delay: 0.15s;
}

.chatbot__dots span:nth-child(3) {
  animation-delay: 0.3s;
}

.chatbot__input-area {
  flex-shrink: 0;
  padding: 0.5rem 0 1rem;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
}

.chatbot__chips {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  padding-bottom: 0.65rem;
  scrollbar-width: none;
}

.chatbot__chips::-webkit-scrollbar {
  display: none;
}

.chatbot__chip {
  flex-shrink: 0;
  padding: 0.4rem 0.85rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-text-muted);
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  backdrop-filter: blur(4px);
  transition: background var(--transition-fast), color var(--transition-fast);
}

.chatbot__chip:hover:not(:disabled) {
  background: var(--color-surface);
  color: var(--color-text);
}

.chatbot__chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chatbot__card {
  padding: 1rem 1rem 0.75rem;
  background: var(--color-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border-subtle);
}

.chatbot__input {
  width: 100%;
  min-height: 2.75rem;
  max-height: 140px;
  padding: 0;
  margin-bottom: 0.5rem;
  font-family: var(--font-body);
  font-size: 1rem;
  line-height: 1.5;
  color: var(--color-text);
  background: transparent;
  border: none;
  resize: none;
}

.chatbot__input::placeholder {
  color: var(--color-text-placeholder);
}

.chatbot__input:focus {
  outline: none;
  box-shadow: none;
}

.chatbot__input:disabled {
  opacity: 0.6;
}

.chatbot__card-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.chatbot__attach {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  color: var(--color-text-muted);
  background: transparent;
  border: none;
  border-radius: var(--radius-round);
  opacity: 0.4;
  cursor: not-allowed;
}

.chatbot__send {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  color: #fff;
  background: var(--color-send-idle);
  border: none;
  border-radius: var(--radius-round);
  transition: background var(--transition-fast), transform var(--transition-fast);
}

.chatbot__send--active {
  background: var(--color-send-active);
}

.chatbot__send--active:hover {
  transform: scale(1.05);
}

.chatbot__send:disabled {
  cursor: not-allowed;
}

.chatbot__send-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.chatbot__toast {
  position: fixed;
  right: 1rem;
  bottom: 7rem;
  z-index: 200;
  max-width: 320px;
  padding: 0.85rem 1.1rem;
  font-size: 0.9rem;
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid rgba(220, 38, 38, 0.35);
  border-left: 3px solid var(--color-error);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  animation: toast-in var(--transition-fast) ease-out;
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity var(--transition-fast), transform var(--transition-fast);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 767px) {
  .chatbot__toast {
    left: 1rem;
    right: 1rem;
    max-width: none;
  }
}
</style>
