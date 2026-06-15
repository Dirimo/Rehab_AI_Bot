<script setup lang="ts">
definePageMeta({
  layout: 'default',
})
</script>

<template>
  <article class="about">
    <h1>À propos de RehabBot</h1>

    <p>
      RehabBot est un prototype open source développé dans le cadre du MSc MSI
      à EPITECH. Il illustre une architecture multi-agents : frontend Nuxt,
      orchestrateur FastAPI, serveur MCP de scraping, et LLM local via Ollama.
    </p>

    <h2>Architecture</h2>
    <ol>
      <li><strong>Frontend (Nuxt 3)</strong> — interface chat WebSocket + REST.</li>
      <li><strong>Backend (FastAPI)</strong> — boucle agent, sessions PostgreSQL.</li>
      <li><strong>MCP server (FastMCP)</strong> — outils de recherche sur sources médicales publiques.</li>
      <li><strong>LLM (Ollama + Qwen 3.5)</strong> — génération de réponses en français.</li>
    </ol>

    <h2>Sources consultées (MCP)</h2>
    <ul>
      <li>HAS — Haute Autorité de Santé (lombalgie, genou, épaule…)</li>
      <li>Santé publique France — TMS</li>
      <li>NHS & CSP — ressources patient UK</li>
      <li>MedlinePlus (NIH) — API + fiches patient</li>
      <li>VIDAL — recommandations (ex. Parkinson)</li>
      <li>Bundle local — exercices résumés (NHS / MedlinePlus)</li>
    </ul>

    <aside class="about__warning">
      <strong>Usage éducatif uniquement.</strong>
      Ne pas utiliser pour un diagnostic ou un traitement réel.
      En cas de douleur aiguë, consultez un médecin ou un kinésithérapeute.
    </aside>
  </article>
</template>

<style scoped>
.about h1 {
  margin: 0 0 1rem;
  color: var(--color-primary);
}

.about h2 {
  margin: 1.75rem 0 0.75rem;
  font-size: 1.15rem;
  color: var(--color-primary-dark);
}

.about p,
.about li {
  color: var(--color-text);
  line-height: 1.6;
}

.about ol,
.about ul {
  padding-left: 1.25rem;
}

.about__warning {
  margin-top: 2rem;
  padding: 1rem 1.25rem;
  background: var(--color-warning-bg);
  border: 1px solid var(--color-warning-border);
  border-radius: var(--radius);
}
</style>
