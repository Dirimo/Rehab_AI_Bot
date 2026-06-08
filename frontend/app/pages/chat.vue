<template>
  <div class="chat-page">
    <!-- Navbar -->
    <nav class="navbar">
      <div class="logo">🏥 RehabBot</div>
      <div class="nav-links">
        <NuxtLink to="/">Accueil</NuxtLink>
        <NuxtLink to="/about">À propos</NuxtLink>
      </div>
    </nav>

    <div class="chat-layout">
      <!-- Sidebar -->
      <aside class="sidebar">
        <button class="btn-new" @click="nouvelleConversation">+ Nouvelle conversation</button>
        <p class="no-conv">Aucune conversation pour l'instant.</p>
      </aside>

      <!-- Zone de chat -->
      <main class="chat-main">
        <div class="messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="empty-state">
            <h2>Comment puis-je vous aider aujourd'hui ?</h2>
            <p>Décrivez votre situation, votre douleur ou votre objectif.</p>
          </div>

          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message', msg.role]"
          >
            <div class="bubble">{{ msg.content }}</div>
          </div>

          <!-- Indicateur de chargement -->
          <div v-if="loading" class="message assistant">
            <div class="bubble loading">⏳ RehabBot réfléchit...</div>
          </div>
        </div>

        <!-- Zone de saisie -->
        <div class="input-area">
          <input
            v-model="inputMessage"
            @keydown.enter="envoyerMessage"
            placeholder="Décrivez votre situation..."
            :disabled="loading"
          />
          <button @click="envoyerMessage" :disabled="loading || !inputMessage.trim()">
            Envoyer →
          </button>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()

const messages = ref<{role: string, content: string}[]>([])
const inputMessage = ref('')
const loading = ref(false)
const sessionId = ref<string | null>(null)
const messagesContainer = ref<HTMLElement | null>(null)

// Au chargement, récupère ou crée une session
onMounted(async () => {
  const savedSession = localStorage.getItem('rehabbot_session_id')
  if (savedSession) {
    sessionId.value = savedSession
    await chargerHistorique()
  } else {
    await creerSession()
  }
})

// Crée une nouvelle session
async function creerSession() {
  try {
    const res = await fetch(`${config.public.apiBase}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
    const data = await res.json()
    sessionId.value = data.id
    localStorage.setItem('rehabbot_session_id', data.id)
  } catch (e) {
    console.error('Erreur création session', e)
  }
}

// Charge l'historique de la session
async function chargerHistorique() {
  try {
    const res = await fetch(`${config.public.apiBase}/messages/${sessionId.value}`)
    const data = await res.json()
    messages.value = data
  } catch (e) {
    console.error('Erreur chargement historique', e)
  }
}

// Nouvelle conversation
async function nouvelleConversation() {
  localStorage.removeItem('rehabbot_session_id')
  messages.value = []
  await creerSession()
}

// Envoie un message via WebSocket
function envoyerMessage() {
  if (!inputMessage.value.trim() || loading.value) return

  const texte = inputMessage.value.trim()
  inputMessage.value = ''
  loading.value = true

  // Ajoute le message utilisateur
  messages.value.push({ role: 'user', content: texte })

  // Connexion WebSocket
  const ws = new WebSocket(`${config.public.wsBase}/ws/${sessionId.value}`)

  ws.onopen = () => {
    ws.send(JSON.stringify({ message: texte }))
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.status) {
      // Statuts intermédiaires
      console.log('Statut :', data.status)
    } else if (data.response) {
      // Réponse finale
      messages.value.push({ role: 'assistant', content: data.response })
      loading.value = false
      ws.close()
      scrollEnBas()
    }
  }

  ws.onerror = () => {
    messages.value.push({ role: 'assistant', content: '❌ Erreur de connexion au serveur.' })
    loading.value = false
  }
}

function scrollEnBas() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}
</script>

<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }

.chat-page {
  font-family: sans-serif;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f9fafb;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 40px;
  background: white;
  border-bottom: 1px solid #eee;
}

.logo { font-weight: bold; }

.nav-links { display: flex; gap: 24px; }
.nav-links a { text-decoration: none; color: #333; font-size: 0.9rem; }

.chat-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 260px;
  background: white;
  border-right: 1px solid #eee;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.btn-new {
  background: #0d7377;
  color: white;
  border: none;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
  width: 100%;
}

.no-conv {
  color: #aaa;
  font-size: 0.85rem;
  text-align: center;
}

/* Chat principal */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 40px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  text-align: center;
  margin: auto;
  color: #888;
}

.empty-state h2 {
  font-size: 1.5rem;
  color: #333;
  margin-bottom: 8px;
}

.message { display: flex; }
.message.user { justify-content: flex-end; }
.message.assistant { justify-content: flex-start; }

.bubble {
  max-width: 65%;
  padding: 12px 18px;
  border-radius: 12px;
  font-size: 0.95rem;
  line-height: 1.6;
}

.message.user .bubble {
  background: #0d7377;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .bubble {
  background: white;
  border: 1px solid #e5e7eb;
  border-bottom-left-radius: 4px;
}

.loading { color: #999; font-style: italic; }

/* Input */
.input-area {
  display: flex;
  gap: 12px;
  padding: 20px 40px;
  background: white;
  border-top: 1px solid #eee;
}

.input-area input {
  flex: 1;
  padding: 14px 18px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.95rem;
  outline: none;
}

.input-area input:focus {
  border-color: #0d7377;
}

.input-area button {
  background: #0d7377;
  color: white;
  border: none;
  padding: 14px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
}

.input-area button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>