<script setup lang="ts">
definePageMeta({
  layout: 'default',
})
</script>

<template>
  <section class="home">
    <div class="home__hero">
      <h1>RehabBot</h1>
      <p class="home__lead">
        Assistant de rééducation alimenté par un LLM local et des outils MCP
        qui consultent des sources publiques fiables (HAS, NHS, MedlinePlus…).
      </p>
      <NuxtLink to="/chat" class="home__cta">Démarrer une conversation</NuxtLink>
    </div>

    <aside class="home__disclaimer" role="note">
      <strong>Avertissement</strong> — Ce projet est un prototype éducatif
      (EPITECH MSc MSI). Il ne fournit pas de diagnostic ni de prescription.
      Consultez toujours un professionnel de santé.
    </aside>

    <div class="home__features">
      <article>
        <h2>Sources multiples</h2>
        <p>
          Le serveur MCP agrège un catalogue HAS, NHS, MedlinePlus, CSP, VIDAL
          et un bundle d'exercices locaux.
        </p>
      </article>
      <article>
        <h2>LLM local</h2>
        <p>
          Ollama exécute Qwen 3.5 9B sur votre machine — pas d'envoi de données
          vers un cloud propriétaire.
        </p>
      </article>
      <article>
        <h2>Sessions persistantes</h2>
        <p>
          Votre conversation est sauvegardée 21 jours dans PostgreSQL et
          reprise via le navigateur.
        </p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.home__hero {
  text-align: center;
  margin-bottom: 2rem;
}

.home h1 {
  margin: 0 0 0.75rem;
  font-size: 2.25rem;
  color: var(--color-primary);
}

.home__lead {
  margin: 0 auto 1.5rem;
  max-width: 36rem;
  color: var(--color-muted);
  font-size: 1.1rem;
}

.home__cta {
  display: inline-block;
  padding: 0.85rem 1.75rem;
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
  border-radius: var(--radius);
  text-decoration: none;
}

.home__cta:hover {
  background: var(--color-primary-dark);
  text-decoration: none;
}

.home__disclaimer {
  margin-bottom: 2rem;
  padding: 1rem 1.25rem;
  background: var(--color-warning-bg);
  border: 1px solid var(--color-warning-border);
  border-radius: var(--radius);
  font-size: 0.95rem;
}

.home__features {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.home__features article {
  padding: 1.25rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.home__features h2 {
  margin: 0 0 0.5rem;
  font-size: 1.1rem;
  color: var(--color-primary);
}

.home__features p {
  margin: 0;
  font-size: 0.95rem;
  color: var(--color-muted);
}
</style>
