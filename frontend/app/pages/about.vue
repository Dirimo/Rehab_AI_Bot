<template>
  <div class="about">
    <!-- Navbar -->
    <nav class="navbar">
      <div class="logo">🏥 RehabBot</div>
      <div class="nav-links">
        <NuxtLink to="/">Accueil</NuxtLink>
        <NuxtLink to="/about">À propos</NuxtLink>
        <NuxtLink to="/chat" class="btn-nav">Ouvrir le chat</NuxtLink>
      </div>
    </nav>

    <div class="content">
      <span class="tag">À PROPOS</span>
      <h1>Un compagnon pédagogique<br>pour la rééducation.</h1>
      <p class="intro">RehabBot est un agent conversationnel dédié à la rééducation physique. Il s'adresse aux patients en rééducation, aux sportifs amateurs et aux étudiants en santé qui souhaitent comprendre, explorer et trouver des ressources fiables sur les mouvements, les pathologies et la récupération.</p>

      <div class="section">
        <h2>Ce que fait RehabBot</h2>
        <ul>
          <li><strong>Dialogue naturel</strong> — Posez vos questions comme vous le diriez à un proche soignant.</li>
          <li><strong>Suggestions d'exercices</strong> — À partir de sources publiques (institutions, fédérations, ressources kiné).</li>
          <li><strong>Recherche web en temps réel</strong> — Récupération d'informations à jour via scraping de sources fiables.</li>
          <li><strong>Orientation</strong> — Conseille systématiquement de consulter un professionnel si la situation l'exige.</li>
        </ul>
      </div>

      <div class="section">
        <h2>Ce qu'il ne fait pas</h2>
        <ul class="no-list">
          <li>✗ Aucun diagnostic médical.</li>
          <li>✗ Aucune prescription d'exercices personnalisée se substituant à un kinésithérapeute.</li>
          <li>✗ Aucun suivi clinique.</li>
        </ul>
      </div>

      <div class="warning">
        ⚠️ <strong>Avertissement médical.</strong> RehabBot est un outil pédagogique d'information et d'orientation. Il ne remplace pas un avis médical ni un suivi par un professionnel de santé. En cas de douleur aiguë, blessure récente ou symptôme inquiétant, consultez un professionnel qualifié.
      </div>

      <div class="section">
        <h2>Confidentialité</h2>
        <p>Vos conversations sont rattachées à votre session et stockées de manière sécurisée. Elles ne sont jamais partagées avec des tiers à des fins commerciales.</p>
      </div>

      <NuxtLink to="/chat" class="btn-primary">Discuter avec RehabBot</NuxtLink>
    </div>

    <footer>© 2026 RehabBot — Information pédagogique uniquement</footer>
  </div>
</template>

<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }

.about {
  font-family: 'Georgia', serif;
  color: #1a1a1a;
  background: #fff;
  min-height: 100vh;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 60px;
  border-bottom: 1px solid #eee;
}

.logo { font-weight: bold; font-size: 1.1rem; }

.nav-links {
  display: flex;
  align-items: center;
  gap: 30px;
}

.nav-links a {
  text-decoration: none;
  color: #333;
  font-size: 0.95rem;
}

.btn-nav {
  background: #0d7377;
  color: white !important;
  padding: 10px 20px;
  border-radius: 6px;
}

.content {
  max-width: 700px;
  margin: 60px auto;
  padding: 0 20px;
}

.tag {
  font-family: sans-serif;
  font-size: 0.8rem;
  color: #0d7377;
  letter-spacing: 0.1em;
  display: block;
  margin-bottom: 16px;
}

h1 {
  font-size: 2.4rem;
  line-height: 1.2;
  margin-bottom: 24px;
}

.intro {
  font-family: sans-serif;
  color: #555;
  line-height: 1.7;
  margin-bottom: 40px;
}

.section {
  margin-bottom: 40px;
}

.section h2 {
  font-size: 1.3rem;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.section ul {
  list-style: none;
  padding: 0;
}

.section ul li {
  font-family: sans-serif;
  font-size: 0.95rem;
  color: #444;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
  line-height: 1.6;
}

.no-list li {
  color: #888;
}

.section p {
  font-family: sans-serif;
  color: #555;
  line-height: 1.7;
}

.warning {
  background: #fffbeb;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  padding: 16px 20px;
  font-family: sans-serif;
  font-size: 0.9rem;
  color: #78350f;
  margin-bottom: 40px;
}

.btn-primary {
  display: inline-block;
  background: #0d7377;
  color: white;
  padding: 14px 28px;
  border-radius: 6px;
  text-decoration: none;
  font-family: sans-serif;
  font-size: 0.95rem;
  margin-bottom: 60px;
}

footer {
  text-align: center;
  padding: 30px;
  font-family: sans-serif;
  font-size: 0.85rem;
  color: #999;
  border-top: 1px solid #eee;
}
</style>