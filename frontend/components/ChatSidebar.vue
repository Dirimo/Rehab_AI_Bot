<script setup lang="ts">
const props = defineProps<{
  activeSessionId: string | null
}>()

const router = useRouter()
const { listSessions, deleteSession, createSession } = useSession()

const sessions = ref<any[]>([])
const isSidebarOpen = ref(false)
const loadError = ref<string | null>(null)

async function loadSessionsList() {
  const all = await listSessions()
  // Only show sessions that already have a title (i.e. at least one message sent)
  sessions.value = all.filter((s: any) => s.title)
}

function selectSession(id: string) {
  isSidebarOpen.value = false // Close sidebar on mobile
  router.push(`/${id}`)
}

async function removeSession(id: string) {
  try {
    await deleteSession(id)
    await loadSessionsList()
    if (props.activeSessionId === id) {
      if (sessions.value.length > 0) {
        selectSession(sessions.value[0].id)
      } else {
        router.push('/')
      }
    }
  } catch {
    loadError.value = 'Impossible de supprimer la discussion.'
  }
}

onMounted(async () => {
  await loadSessionsList()
})

defineExpose({
  loadSessionsList,
})
</script>

<template>
  <aside class="chat-sidebar" :class="{ 'chat-sidebar--open': isSidebarOpen }">
    <!-- Toggle Button to close sidebar on mobile inside the sidebar header -->
    <button
      type="button"
      class="chat-page__toggle-sidebar"
      aria-label="Fermer le menu"
      @click="isSidebarOpen = false"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    </button>

    <div class="chat-sidebar__header">
      <NuxtLink to="/" class="chat-sidebar__brand">
        <span class="chat-sidebar__wordmark">RehabBot</span>
      </NuxtLink>
      
      <NuxtLink
        to="/"
        class="chat-sidebar__new-btn"
        @click="isSidebarOpen = false"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        Nouvelle discussion
      </NuxtLink>
    </div>

    <div class="chat-sidebar__list" role="navigation" aria-label="Historique des discussions">
      <div
        v-for="sess in sessions"
        :key="sess.id"
        class="chat-sidebar__item"
        :class="{ 'chat-sidebar__item--active': activeSessionId === sess.id }"
      >
        <button
          type="button"
          class="chat-sidebar__item-btn"
          @click="selectSession(sess.id)"
        >
          <svg class="chat-sidebar__item-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <span class="chat-sidebar__item-title">
            {{ sess.title || 'Discussion sans titre' }}
          </span>
        </button>
        
        <button
          type="button"
          class="chat-sidebar__delete-btn"
          title="Supprimer la discussion"
          aria-label="Supprimer la discussion"
          @click.stop="removeSession(sess.id)"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </div>
    </div>
  </aside>

  <!-- Toggle button for mobile trigger (renders outside sidebar) -->
  <button
    type="button"
    class="chat-page__toggle-sidebar-trigger"
    aria-label="Ouvrir le menu"
    @click="isSidebarOpen = true"
  >
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="3" y1="12" x2="21" y2="12"></line>
      <line x1="3" y1="6" x2="21" y2="6"></line>
      <line x1="3" y1="18" x2="21" y2="18"></line>
    </svg>
  </button>

  <div
    v-if="isSidebarOpen"
    class="chat-page__overlay"
    @click="isSidebarOpen = false"
  />
</template>

<style scoped>
/* Sidebar styling with glassmorphism */
.chat-sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--color-border-subtle);
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(12px);
  padding: 1rem 0.75rem;
  transition: transform var(--transition-fast), left var(--transition-fast);
}

.chat-sidebar__header {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.chat-sidebar__brand {
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  color: var(--color-text);
  padding: 0.5rem 0;
}

.chat-sidebar__wordmark {
  font-family: var(--font-brand);
  font-size: 1.75rem;
  font-weight: 400;
  color: var(--color-text);
}

.chat-sidebar__new-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.75rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-soft);
  transition: transform var(--transition-fast), background var(--transition-fast);
}

.chat-sidebar__new-btn:hover {
  transform: translateY(-1px);
  background: var(--color-bg);
}

.chat-sidebar__list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding-right: 2px;
}

.chat-sidebar__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-radius: 10px;
  transition: background var(--transition-fast);
  padding: 0.15rem;
}

.chat-sidebar__item:hover {
  background: rgba(10, 10, 10, 0.04);
}

.chat-sidebar__item--active {
  background: rgba(10, 10, 10, 0.06);
}

.chat-sidebar__item-btn {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.5rem 0.4rem;
  background: transparent;
  border: none;
  color: var(--color-text);
  text-align: left;
  min-width: 0;
}

.chat-sidebar__item-icon {
  flex-shrink: 0;
  color: var(--color-text-muted);
}

.chat-sidebar__item-title {
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-sidebar__delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  border-radius: 6px;
  opacity: 0;
  transition: opacity var(--transition-fast), background var(--transition-fast), color var(--transition-fast);
}

.chat-sidebar__item:hover .chat-sidebar__delete-btn,
.chat-sidebar__delete-btn:focus-visible {
  opacity: 1;
}

.chat-sidebar__delete-btn:hover {
  background: var(--color-error-bg);
  color: var(--color-error);
}

/* Mobile responsive styles */
.chat-page__toggle-sidebar-trigger {
  display: none;
  position: fixed;
  left: 1rem;
  top: 12px;
  z-index: 110;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  color: var(--color-text);
  box-shadow: var(--shadow-soft);
}

.chat-page__toggle-sidebar {
  display: none;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  color: var(--color-text);
  box-shadow: var(--shadow-soft);
  margin-bottom: 1rem;
}

.chat-page__overlay {
  display: none;
  position: fixed;
  inset: 0;
  z-index: 105;
  background: rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(4px);
}

@media (max-width: 767px) {
  .chat-page__toggle-sidebar-trigger {
    display: flex;
  }

  .chat-page__toggle-sidebar {
    display: flex;
  }
  
  .chat-sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 108;
    transform: translateX(-100%);
    box-shadow: 4px 0 15px rgba(0, 0, 0, 0.1);
  }
  
  .chat-sidebar--open {
    transform: translateX(0);
  }
  
  .chat-page__overlay {
    display: block;
  }
}
</style>
