<template>
  <div class="layout" :class="{ 'layout--hero': isHero }">
    <AppHeader />
    <main class="layout__main">
      <slot />
    </main>
    <footer v-if="!isHero" class="layout__footer">
      <p>Ne remplace pas un avis médical.</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const isHero = computed(() => route.path === '/')
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

.layout--hero .layout__main {
  padding: 0;
  max-width: none;
}

.layout__main {
  flex: 1;
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
  padding: calc(var(--header-height) + 2rem) 1.5rem 2rem;
}

.layout__footer {
  padding: 1.25rem 1.5rem;
  text-align: center;
  font-size: 0.8rem;
  color: var(--color-text-muted);
  border-top: 1px solid var(--color-border-subtle);
  background: var(--color-surface);
}

.layout__footer p {
  margin: 0;
}

.layout__footer a {
  color: var(--color-text);
  text-decoration: underline;
  text-underline-offset: 2px;
}

@media (max-width: 767px) {
  .layout__main {
    padding-left: 1rem;
    padding-right: 1rem;
  }
}
</style>
