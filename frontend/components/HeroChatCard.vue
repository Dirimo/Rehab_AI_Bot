<script setup lang="ts">
const emit = defineEmits<{
  submit: [text: string]
}>()

const PLACEHOLDERS = [
  '🧩 Aidez-moi avec ma lombalgie…',
  '📝 Quels exercices pour l\'épaule ?',
  '🦵 Conseils rééducation du genou…',
  '📚 Sources HAS sur le mal de dos…',
]

const draft = ref('')
const placeholderIndex = ref(0)

const currentPlaceholder = computed(() => PLACEHOLDERS[placeholderIndex.value])

const canSend = computed(() => draft.value.trim().length > 0)

let rotateTimer: ReturnType<typeof setInterval> | null = null

function submit() {
  const text = draft.value.trim()
  if (!text) return
  emit('submit', text)
  draft.value = ''
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    submit()
  }
}

onMounted(() => {
  rotateTimer = setInterval(() => {
    if (!draft.value) {
      placeholderIndex.value = (placeholderIndex.value + 1) % PLACEHOLDERS.length
    }
  }, 4000)
})

onBeforeUnmount(() => {
  if (rotateTimer) clearInterval(rotateTimer)
})
</script>

<template>
  <div class="hero-card">
    <div class="hero-card__top">
      <textarea
        v-model="draft"
        class="hero-card__input"
        rows="2"
        :placeholder="currentPlaceholder"
        aria-label="Votre question de rééducation"
        @keydown="onKeydown"
      />
    </div>
    <div class="hero-card__bottom">
      <button
        type="button"
        class="hero-card__send"
        :class="{ 'hero-card__send--active': canSend }"
        :disabled="!canSend"
        aria-label="Envoyer"
        @click="submit"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 19V5M6 11l6-6 6 6" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.hero-card {
  width: 100%;
  max-width: var(--content-max);
  padding: 1.25rem 1.25rem 1rem;
  background: var(--color-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border-subtle);
}

.hero-card__top {
  margin-bottom: 0.75rem;
}

.hero-card__input {
  width: 100%;
  min-height: 3.5rem;
  padding: 0;
  font-family: var(--font-body);
  font-size: 1.05rem;
  line-height: 1.55;
  color: var(--color-text);
  background: transparent;
  border: none;
  resize: none;
}

.hero-card__input::placeholder {
  color: var(--color-text-placeholder);
}

.hero-card__input:focus {
  outline: none;
  box-shadow: none;
}

.hero-card__bottom {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.hero-card__attach {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  color: var(--color-text-muted);
  background: transparent;
  border: none;
  border-radius: var(--radius-round);
  opacity: 0.45;
  cursor: not-allowed;
}

.hero-card__send {
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

.hero-card__send--active {
  background: var(--color-send-active);
}

.hero-card__send--active:hover {
  transform: scale(1.05);
}

.hero-card__send:disabled {
  cursor: not-allowed;
}
</style>
