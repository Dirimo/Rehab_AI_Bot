<script setup lang="ts">
definePageMeta({
  layout: 'default',
})
</script>

<template>
  <div class="showcase">
    <!-- Ambient beautiful background -->
    <HeroBackground />

    <!-- Header / Brand logo -->
    <header class="showcase__header">
      <div class="showcase__brand">
        <span class="showcase__wordmark">Rehab</span>
      </div>
    </header>

    <!-- Main Hero area -->
    <main class="showcase__main">
      <section class="hero-section">
        <div class="hero-section__content">
          <h1 class="hero-section__title">
            Centre de Rééducation Rehab
          </h1>
          <p class="hero-section__subtitle">
            Des soins de physiothérapie sur-mesure au sein de notre établissement, accompagnés de notre assistant virtuel RehabBot pour vous guider à la maison.
          </p>
          
          <div class="hero-section__actions">
            <NuxtLink to="/chat" class="showcase__cta">
              Parler à l'assistant RehabBot
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
              </svg>
            </NuxtLink>
          </div>
        </div>

        <div class="hero-section__visual">
          <div class="hero-section__image-container">
            <img src="/rehab-showcase.png" alt="Rééducation physique au Centre Rehab" class="hero-section__image" />
            <div class="hero-section__logo-glow" />
          </div>
        </div>
      </section>

      <!-- Features grid section -->
      <section class="features-section">
        <h2 class="features-section__title">Notre approche globale de soin</h2>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-card__icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path>
              </svg>
            </div>
            <h3 class="feature-card__title">Soins Physiques & Kinésithérapie</h3>
            <p class="feature-card__desc">
              Des séances personnalisées et adaptées dispensées par nos praticiens directement dans notre centre de rééducation.
            </p>
          </div>

          <div class="feature-card">
            <div class="feature-card__icon-wrapper">
              <ClientOnly>
                <BrandLogo3d :size="36" :rotate="true" />
              </ClientOnly>
            </div>
            <h3 class="feature-card__title">Assistant Virtuel RehabBot</h3>
            <p class="feature-card__desc">
              Notre robot intelligent, disponible en ligne 24h/24, pour vous aider et vous guider dans vos exercices à la maison.
            </p>
          </div>

          <div class="feature-card">
            <div class="feature-card__icon-wrapper">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
            </div>
            <h3 class="feature-card__title">Accompagnement 24h/24</h3>
            <p class="feature-card__desc">
              Une assistance disponible à tout moment pour répondre à vos questions et vous guider dans vos mouvements à la maison.
            </p>
          </div>
        </div>
      </section>


    </main>
  </div>
</template>

<style scoped>
.showcase {
  min-height: 100vh;
  position: relative;
  display: flex;
  flex-direction: column;
  color: var(--color-text);
  overflow-x: hidden;
  padding: 0 1.5rem;
}

.showcase__header {
  position: relative;
  z-index: 10;
  max-width: 1100px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.showcase__brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.showcase__wordmark {
  font-family: var(--font-brand);
  font-size: 2rem;
  font-weight: 400;
}

.showcase__main {
  position: relative;
  z-index: 10;
  max-width: 1100px;
  width: 100%;
  margin: 0 auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5rem;
  padding-bottom: 4rem;
}

/* Hero Section */
.hero-section {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  align-items: center;
  gap: 3rem;
  padding: 3rem 0 1rem;
}

.hero-section__content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
}

.hero-section__title {
  font-size: 4rem;
  line-height: 1.1;
  margin: 0 0 1.5rem;
  color: var(--color-text);
}

.hero-section__subtitle {
  font-size: 1.35rem;
  line-height: 1.6;
  color: var(--color-text-muted);
  margin: 0 0 2.5rem;
  max-width: 36rem;
}

.hero-section__actions {
  display: flex;
  gap: 1rem;
}

.showcase__cta {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  background: var(--color-user-bubble);
  color: #ffffff;
  padding: 1rem 2rem;
  border-radius: 0;
  font-size: 1.1rem;
  font-weight: 500;
  box-shadow: var(--shadow-card);
  transition: transform 200ms ease, background 200ms ease;
}

.showcase__cta:hover {
  transform: translateY(-2px);
  background: #262626;
}

.showcase__cta svg {
  transition: transform 200ms ease;
}

.showcase__cta:hover svg {
  transform: translateX(4px);
}

.hero-section__visual {
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.hero-section__image-container {
  position: relative;
  z-index: 2;
  transition: transform 400ms cubic-bezier(0.16, 1, 0.3, 1);
  border: 1px solid var(--color-border-subtle);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  background: #ffffff;
}

.hero-section__image-container:hover {
  transform: scale(1.02);
}

.hero-section__image {
  display: block;
  width: 100%;
  max-width: 440px;
  height: auto;
}

.hero-section__logo-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 320px;
  height: 320px;
  background: radial-gradient(circle, rgba(187, 217, 245, 0.45) 0%, transparent 70%);
  z-index: 1;
  filter: blur(20px);
  pointer-events: none;
}

/* Features Section */
.features-section {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
}

.features-section__title {
  font-size: 2.5rem;
  text-align: center;
  margin: 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
}

.feature-card {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--color-border-subtle);
  border-radius: 0;
  padding: 2.25rem 2rem;
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow-soft);
  transition: transform 200ms ease, background 200ms ease;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.feature-card:hover {
  transform: translateY(-4px);
  background: rgba(255, 255, 255, 0.95);
  box-shadow: var(--shadow-card);
}

.feature-card__icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 0;
  background: var(--color-bg-sky);
  color: var(--color-text);
  display: flex;
  align-items: center;
  justify-content: center;
}

.feature-card__title {
  font-size: 1.5rem;
  margin: 0;
}

.feature-card__desc {
  font-size: 1.05rem;
  line-height: 1.6;
  color: var(--color-text-muted);
  margin: 0;
}

/* Disclaimer Section */
.disclaimer-section {
  width: 100%;
}

.disclaimer-card {
  display: flex;
  align-items: flex-start;
  gap: 1.5rem;
  background: var(--color-error-bg);
  border: 1px solid rgba(220, 38, 38, 0.15);
  border-radius: 0;
  padding: 1.75rem 2rem;
  box-shadow: var(--shadow-soft);
}

.disclaimer-card__icon {
  color: var(--color-error);
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.disclaimer-card__text {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: left;
}

.disclaimer-card__title {
  font-size: 1.25rem;
  color: var(--color-error);
  margin: 0;
  font-weight: 500;
}

.disclaimer-card__desc {
  font-size: 1rem;
  line-height: 1.6;
  color: #7f1d1d;
  margin: 0;
}

/* Responsive design */
@media (max-width: 960px) {
  .hero-section {
    grid-template-columns: 1fr;
    text-align: center;
    gap: 2rem;
  }

  .hero-section__content {
    align-items: center;
    text-align: center;
  }

  .hero-section__title {
    font-size: 3rem;
  }

  .hero-section__subtitle {
    font-size: 1.15rem;
  }

  .features-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .disclaimer-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .disclaimer-card__text {
    text-align: center;
  }
}
</style>
