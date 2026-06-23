<template>
  <div class="chat-layout">
    <HeroBackground />
    <AppHeader />
    <main class="chat-layout__main">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.chat-layout {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100dvh;
  overflow: hidden;
  background: var(--color-bg);
}

.chat-layout__main {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
  padding-top: var(--header-height);
}
</style>
