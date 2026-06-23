<script setup lang="ts">
definePageMeta({
  layout: 'chat',
})

const pending = usePendingPrompt()
const { ensureSession } = useSession()

const sessionId = ref<string | null>(null)
const initialMessage = ref<string | undefined>()
const loadError = ref<string | null>(null)

onMounted(async () => {
  try {
    sessionId.value = await ensureSession()
    if (pending.value) {
      initialMessage.value = pending.value
      pending.value = null
    }
  } catch {
    loadError.value =
      'Impossible de créer une session. Vérifiez que le backend tourne sur le port 8000.'
  }
})
</script>

<template>
  <section class="chat-page">
    <p v-if="loadError" class="chat-page__error" role="alert">
      {{ loadError }}
    </p>

    <ClientOnly>
      <ChatBot
        v-if="sessionId"
        :session-id="sessionId"
        :initial-message="initialMessage"
      />
      <div v-else-if="!loadError" class="chat-page__loading">
        <div class="chat-page__dots" aria-hidden="true"><span /><span /><span /></div>
        <p>Chargement…</p>
      </div>
    </ClientOnly>
  </section>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  width: 100%;
  padding: 0 1rem;
}

.chat-page__loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: var(--color-text-muted);
}

.chat-page__dots {
  display: flex;
  gap: 6px;
}

.chat-page__dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-sky-accent);
  animation: dot-pulse 1.2s infinite ease-in-out;
}

.chat-page__dots span:nth-child(2) {
  animation-delay: 0.15s;
}

.chat-page__dots span:nth-child(3) {
  animation-delay: 0.3s;
}

.chat-page__loading p {
  margin: 0;
  font-size: 0.9rem;
}

.chat-page__error {
  margin: 1rem 0;
  padding: 1rem;
  border-radius: var(--radius-card);
  background: var(--color-error-bg);
  border: 1px solid rgba(220, 38, 38, 0.25);
  color: var(--color-error);
  font-size: 0.9rem;
}
</style>
