<template>
  <div class="layout">
    <header class="layout__header">
      <NuxtLink to="/" class="layout__brand">
        <span class="layout__logo" aria-hidden="true">🩺</span>
        RehabBot
      </NuxtLink>
      <nav class="layout__nav" aria-label="Navigation principale">
        <NuxtLink to="/">Accueil</NuxtLink>
        <NuxtLink to="/chat">Chat</NuxtLink>
        <NuxtLink to="/about">À propos</NuxtLink>
      </nav>
    </header>

    <main class="layout__main">
      <slot />
    </main>

    <footer class="layout__footer">
      <p>
        Prototype éducatif — ne remplace pas un avis médical.
        Sources : HAS, NHS, MedlinePlus, Santé publique France…
      </p>
    </footer>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.layout__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow);
}

.layout__brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-primary);
  text-decoration: none;
}

.layout__logo {
  font-size: 1.4rem;
}

.layout__nav {
  display: flex;
  gap: 1.25rem;
}

.layout__nav a {
  font-weight: 500;
  color: var(--color-text);
  text-decoration: none;
  padding-bottom: 2px;
  border-bottom: 2px solid transparent;
}

.layout__nav a:hover,
.layout__nav a.router-link-active {
  color: var(--color-primary);
  border-bottom-color: var(--color-accent);
}

.layout__main {
  flex: 1;
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

.layout__footer {
  padding: 1rem 1.5rem;
  text-align: center;
  font-size: 0.85rem;
  color: var(--color-muted);
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
}

.layout__footer p {
  margin: 0;
}
</style>
