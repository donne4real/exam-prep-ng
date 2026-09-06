import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  // Set base path for GitHub Pages deployment at /exam-prep-ng/
  base: "/exam-prep-ng/",
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'robots.txt', 'apple-touch-icon.png'],
      manifest: {
        name: 'Nigerian Exam Prep',
        short_name: 'ExamPrep NG',
        description: 'Practice questions for BECE, NECO and JAMB exams. Works offline.',
        theme_color: '#008751',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        // Must match `base` — the app is served from /exam-prep-ng/ on
        // GitHub Pages. A scope wider than the SW's own path breaks installs.
        scope: '/exam-prep-ng/',
        start_url: '/exam-prep-ng/',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        // JSON is excluded from the precache glob because the bundled
        // data/questions.json is too large for precache; the runtime
        // NetworkFirst route below handles it instead.
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        maximumFileSizeToCacheInBytes: 8 * 1024 * 1024,
        runtimeCaching: [
          {
            urlPattern: ({ request }) => request.destination === 'document',
            handler: 'NetworkFirst',
            options: {
              cacheName: 'html-cache',
            },
          },
          {
            // Serve the cached bank instantly and refresh in the background:
            // revisits (especially offline) must not wait on the network.
            urlPattern: ({ url }) => url.pathname.endsWith('/data/questions.json'),
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'questions-cache',
              expiration: {
                maxEntries: 4,
                maxAgeSeconds: 60 * 60 * 24 * 30,
              },
            },
          },
        ],
      },
      devOptions: {
        enabled: true,
        type: 'module',
      },
    }),
  ],
  build: {
    target: 'es2019',
    cssCodeSplit: true,
    sourcemap: false,
  },
});
