<script setup lang="ts">
definePageMeta({
  layout: 'chat',
})

const router = useRouter()
const pending = usePendingPrompt()
const { createSession } = useSession()
const sidebarRef = ref()

async function handleNewChatSubmit(text: string) {
  try {
    const newSess = await createSession()
    if (import.meta.client) {
      localStorage.setItem('rehabbot_session_id', newSess.id)
    }
    pending.value = text
    router.push(`/${newSess.id}`)
  } catch (err) {
    console.error('Failed to start chat:', err)
  }
}
</script>

<template>
  <section class="chat-page">
    <!-- Reusable Sidebar -->
    <ChatSidebar ref="sidebarRef" :active-session-id="null" />

    <!-- Centered Starting View -->
    <div class="chat-container">
      <div class="home-landing">
        <BrandGlyph class="home-landing__glyph" :size="96" />
        <h1 class="home-landing__title">Rééducation IA en ligne</h1>
        <HeroChatCard class="home-landing__card" @submit="handleNewChatSubmit" />
      </div>
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

.home-landing {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem 1rem;
}

.home-landing__glyph {
  margin-bottom: 1.25rem;
}

.home-landing__title {
  margin: 0 0 1.75rem;
  font-size: 2.75rem;
  font-weight: 400;
  color: var(--color-text);
}

.home-landing__card {
  width: 100%;
}

@media (max-width: 767px) {
  .home-landing__title {
    font-size: 1.75rem;
  }
}
</style>
