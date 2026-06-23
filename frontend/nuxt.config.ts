// RehabBot frontend config (Member 1).
// Public env vars are read from the repo root .env or frontend/.env:
//   NUXT_PUBLIC_API_BASE=http://localhost:8000
//   NUXT_PUBLIC_WS_BASE=ws://localhost:8000

export default defineNuxtConfig({
  compatibilityDate: '2025-06-15',
  devtools: { enabled: true },

  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000',
      wsBase: 'ws://localhost:8000',
    },
  },

  app: {
    head: {
      title: 'RehabBot',
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Oregano:ital@0;1&display=swap',
        },
      ],
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'theme-color', content: '#F8F7F7' },
        {
          name: 'description',
          content:
            'Assistant éducatif de rééducation — prototype open source, ne remplace pas un professionnel de santé.',
        },
      ],
    },
  },

  css: ['~/assets/css/main.css'],
})
