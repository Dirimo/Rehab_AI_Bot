<script setup lang="ts">
definePageMeta({
  layout: 'default',
})

const router = useRouter()
const pending = usePendingPrompt()

function goToChat(text: string) {
  pending.value = text
  router.push('/chat')
}

function scrollToSections() {
  document.getElementById('sections')?.scrollIntoView({ behavior: 'smooth' })
}
</script>

<template>
  <div class="home">
    <HeroBackground />

    <section class="home__hero">
      <BrandGlyph class="home__glyph" :size="96" />
      <h1 class="home__title">Rééducation IA en ligne</h1>
      <HeroChatCard class="home__card" @submit="goToChat" />
      <button
        type="button"
        class="home__chevron"
        aria-label="Voir les sections suivantes"
        @click="scrollToSections"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </section>

    <section id="sections" class="home__sections">
      <article class="home__section">
        <h2>Posez vos questions à l'IA</h2>
        <p>
          Lombalgie, genou, épaule… RehabBot consulte des sources publiques fiables
          (HAS, NHS, MedlinePlus) via son serveur MCP et répond en français.
        </p>
      </article>
      <article class="home__section">
        <h2>Exercices et conseils de rééducation</h2>
        <p>
          Recherche d'exercices adaptés, conseils par zone anatomique et liens
          vers des fiches patient validées — toujours à titre éducatif.
        </p>
      </article>
      <article class="home__section">
        <h2>LLM local, données privées</h2>
        <p>
          Ollama exécute Qwen 3.5 9B sur votre machine. Vos conversations sont
          sauvegardées 21 jours dans PostgreSQL.
        </p>
      </article>
    </section>


  </div>
</template>

<style scoped>
.home {
  position: relative;
  min-height: 100vh;
}

.home__hero {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  padding: calc(var(--header-height) + 4vh) 1rem 3rem;
  text-align: center;
}

.home__glyph {
  margin-bottom: 1.25rem;
}

.home__title {
  margin: 0 0 1.75rem;
  font-size: 2.75rem;
  font-weight: 400;
  letter-spacing: normal;
  color: var(--color-text);
}

.home__card {
  width: 100%;
}

.home__chevron {
  margin-top: auto;
  padding-top: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  color: var(--color-text-muted);
  background: transparent;
  border: none;
  animation: chevron-bounce 2s ease-in-out infinite;
}

.home__sections {
  position: relative;
  z-index: 1;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 4rem 1rem 3rem;
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.home__section {
  text-align: center;
}

.home__section h2 {
  margin: 0 0 0.75rem;
  font-size: clamp(1.35rem, 3vw, 1.65rem);
  font-weight: 400;
}

.home__section p {
  margin: 0 auto;
  max-width: 32rem;
  color: var(--color-text-muted);
  line-height: 1.65;
}

.home__footer {
  position: relative;
  z-index: 1;
  padding: 2rem 1rem 2.5rem;
  text-align: center;
  border-top: 1px solid var(--color-border-subtle);
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(8px);
}

.home__disclaimer {
  margin: 0 0 0.75rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.home__legal {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  font-size: 0.85rem;
}

.home__legal a {
  color: var(--color-text);
  text-decoration: underline;
  text-underline-offset: 2px;
}

@media (max-width: 767px) {
  .home__title {
    font-size: 1.75rem;
  }

  .home__hero {
    padding-top: calc(var(--header-height) + 2vh);
  }
}
</style>
