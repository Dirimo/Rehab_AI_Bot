<template>
  <header class="app-header">
    <NuxtLink to="/" class="app-header__brand">
      <span class="app-header__wordmark">RehabBot</span>
    </NuxtLink>

    <nav class="app-header__center" aria-label="Navigation principale">
      <NuxtLink to="/chat" class="app-header__link">Chat IA</NuxtLink>
    </nav>
  </header>
</template>

<style scoped>
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--header-height);
  padding: 0 1.25rem;
  background: transparent;
}

.app-header__brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--color-text);
}

.app-header__brand:hover {
  text-decoration: none;
  opacity: 0.85;
}

.app-header__glyph {
  display: flex;
  line-height: 0;
}

.app-header__wordmark {
  font-family: var(--font-brand);
  font-size: 1.35rem;
  font-weight: 400;
  color: var(--color-text);
}

.app-header__center {
  display: flex;
  gap: 1.75rem;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.app-header__link {
  font-family: var(--font-heading);
  font-size: 0.95rem;
  font-weight: 400;
  color: var(--color-text);
  text-decoration: none;
}

.app-header__link.router-link-active {
  font-weight: 400;
}

.app-header__link:hover {
  text-decoration: none;
  opacity: 0.75;
}

@media (max-width: 767px) {
  .app-header__center {
    display: none;
  }
}
</style>
