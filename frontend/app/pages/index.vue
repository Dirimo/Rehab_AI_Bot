<template>
  <div class="home">
    <!-- Navbar -->
    <nav class="navbar">
      <div class="logo">🏥 RehabBot</div>
      <div class="nav-links">
        <NuxtLink to="/">Accueil</NuxtLink>
        <NuxtLink to="/about">À propos</NuxtLink>
        <NuxtLink to="/chat" class="btn-nav">Ouvrir le chat</NuxtLink>
      </div>
    </nav>

    <!-- Hero -->
    <section class="hero">
      <div class="hero-text">
        <span class="tag">Assistant pédagogique de rééducation</span>
        <h1>Reprenez le<br>mouvement,</h1>
        <p>RehabBot est votre compagnon conversationnel : il répond à vos questions sur la rééducation, propose des exercices et recherche pour vous des informations fiables — patient, sportif amateur ou étudiant.</p>
        <div class="hero-buttons">
          <NuxtLink to="/chat" class="btn-primary">Démarrer une conversation</NuxtLink>
          <NuxtLink to="/about" class="btn-secondary">En savoir plus</NuxtLink>
        </div>
      </div>
      <div class="hero-image">
        <img src="https://images.unsplash.com/photo-1518611012118-696072aa579a?w=500" alt="Rééducation" />
      </div>
    </section>

    <!-- Avertissement -->
    <div class="warning">
      ⚠️ <strong>Avertissement médical.</strong> RehabBot est un outil pédagogique d'information et d'orientation. Il ne remplace pas un avis médical, un diagnostic ni un suivi par un professionnel de santé qualifié. En cas de douleur intense, de blessure récente ou de doute, consultez votre médecin ou kinésithérapeute.
    </div>

    <!-- Features -->
    <section class="features">
      <h2>Une approche douce, claire et utile.</h2>
      <p class="features-sub">Quatre piliers conçus pour vous accompagner sans jamais se substituer à votre soignant.</p>
      <div class="cards">
        <div class="card">
          <h3>Conversation naturelle</h3>
          <p>Décrivez votre situation en langage courant — RehabBot vous répond avec clarté.</p>
        </div>
        <div class="card">
          <h3>Exercices ciblés</h3>
          <p>Suggestions d'exercices issues de sources publiques de rééducation et de kinésithérapie.</p>
        </div>
        <div class="card">
          <h3>Recherche web en temps réel</h3>
          <p>Récupération d'informations fiables et à jour par scraping de sources reconnues.</p>
        </div>
        <div class="card">
          <h3>Pédagogique & orientant</h3>
          <p>RehabBot vulgarise, explique, et vous oriente vers un professionnel quand c'est nécessaire.</p>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer>© 2026 RehabBot — Information pédagogique uniquement</footer>
  </div>
</template>

<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }

.home {
  font-family: 'Georgia', serif;
  color: #1a1a1a;
  background: #fff;
}

/* Navbar */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 60px;
  border-bottom: 1px solid #eee;
}

.logo {
  font-weight: bold;
  font-size: 1.1rem;
}

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

/* Hero */
.hero {
  display: flex;
  align-items: center;
  gap: 60px;
  padding: 60px 60px;
  max-width: 1100px;
  margin: 0 auto;
}

.hero-text {
  flex: 1;
}

.tag {
  background: #f0faf0;
  color: #0d7377;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-family: sans-serif;
  display: inline-block;
  margin-bottom: 20px;
}

h1 {
  font-size: 3rem;
  line-height: 1.15;
  margin-bottom: 20px;
}

.hero-text p {
  color: #555;
  line-height: 1.7;
  font-family: sans-serif;
  font-size: 0.95rem;
  margin-bottom: 30px;
}

.hero-buttons {
  display: flex;
  gap: 14px;
}

.btn-primary {
  background: #0d7377;
  color: white;
  padding: 12px 24px;
  border-radius: 6px;
  text-decoration: none;
  font-family: sans-serif;
  font-size: 0.95rem;
}

.btn-secondary {
  background: transparent;
  color: #333;
  padding: 12px 24px;
  border-radius: 6px;
  text-decoration: none;
  border: 1px solid #ccc;
  font-family: sans-serif;
  font-size: 0.95rem;
}

.hero-image img {
  width: 420px;
  height: 280px;
  object-fit: cover;
  border-radius: 12px;
}

/* Warning */
.warning {
  background: #fffbeb;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  padding: 16px 24px;
  margin: 0 60px 60px;
  font-family: sans-serif;
  font-size: 0.9rem;
  color: #78350f;
}

/* Features */
.features {
  padding: 0 60px 60px;
  max-width: 1100px;
  margin: 0 auto;
}

.features h2 {
  font-size: 2rem;
  margin-bottom: 10px;
}

.features-sub {
  color: #666;
  font-family: sans-serif;
  font-size: 0.95rem;
  margin-bottom: 40px;
}

.cards {
  display: flex;
  gap: 20px;
}

.card {
  flex: 1;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 24px;
}

.card h3 {
  font-size: 1rem;
  margin-bottom: 10px;
}

.card p {
  font-family: sans-serif;
  font-size: 0.88rem;
  color: #666;
  line-height: 1.6;
}

/* Footer */
footer {
  text-align: center;
  padding: 30px;
  font-family: sans-serif;
  font-size: 0.85rem;
  color: #999;
  border-top: 1px solid #eee;
}
</style>