<script setup lang="ts">
definePageMeta({
  layout: 'chat',
  validate: (route) => {
    // Only accept 32-character hex UUID strings as valid session IDs
    return typeof route.params.id === 'string' && /^[0-9a-f]{32}$/i.test(route.params.id)
  }
})

const route = useRoute()
const pending = usePendingPrompt()

const sessionId = computed(() => route.params.id as string)
const initialMessage = ref<string | undefined>()
const sidebarRef = ref()

// Resolve pending prompt synchronously before child component ChatBot mounts
if (pending.value) {
  initialMessage.value = pending.value
  pending.value = null
}

function onSessionUpdated() {
  sidebarRef.value?.loadSessionsList()
}
</script>

<template>
  <section class="chat-page">
    <!-- Reusable Sidebar -->
    <ChatSidebar ref="sidebarRef" :active-session-id="sessionId" />

    <!-- Chat Bot Container -->
    <div class="chat-container">
      <ClientOnly>
        <ChatBot
          :session-id="sessionId"
          :initial-message="initialMessage"
          @session-updated="onSessionUpdated"
        />
      </ClientOnly>
    </div>
  </section>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: row;
  flex: 1;
  min-height: 0;
  width: 100%;
  position: relative;
}

.chat-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  width: 100%;
  padding: var(--header-height) 1rem 0;
}
</style>
