<script setup lang="ts">
definePageMeta({
  layout: 'default',
})

const { ensureSession } = useSession()
const sessionId = ref<string | null>(null)
const loadError = ref<string | null>(null)

onMounted(async () => {
  try {
    sessionId.value = await ensureSession()
  } catch {
    loadError.value =
      'Impossible de créer une session. Vérifiez que le backend tourne sur le port 8000.'
  }
})
</script>

<template>
  <section class="chat-page">
    <header class="chat-page__header">
      <h1>Conversation</h1>
      <p>
        Posez vos questions de rééducation. RehabBot peut rechercher des
        exercices et des sources via le serveur MCP.
      </p>
    </header>

    <p v-if="loadError" class="chat-page__error" role="alert">
      {{ loadError }}
    </p>

    <ClientOnly>
      <ChatBot v-if="sessionId" :session-id="sessionId" />
      <p v-else-if="!loadError" class="chat-page__loading">Chargement de la session…</p>
    </ClientOnly>
  </section>
</template>

<style scoped>
.chat-page__header h1 {
  margin: 0 0 0.5rem;
  color: var(--color-primary);
}

.chat-page__header p {
  margin: 0 0 1.5rem;
  color: var(--color-muted);
}

.chat-page__loading,
.chat-page__error {
  padding: 1rem;
  border-radius: var(--radius);
}

.chat-page__loading {
  color: var(--color-muted);
}

.chat-page__error {
  background: #fdecea;
  border: 1px solid #f5c2c0;
  color: #8a1f17;
}
</style>
