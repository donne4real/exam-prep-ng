import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  // Treat `data/` as a plain static asset folder, not source. The content
  // agent drops raw research HTML and per-year JSON extracts in there
  // which Vite would otherwise try to parse as modules.
  publicDir: 'public',
  server: {
    fs: {
      // Refuse to serve files outside the project root.
      strict: true,
    },
    watch: {
      // Don't trigger HMR / dep re-scans when research files change.
      ignored: ['**/data/raw/**', '**/data/extracted/**'],
    },
  },
  optimizeDeps: {
    exclude: ['data'],
  },
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
        scope: '/',
        start_url: '/',
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
            urlPattern: ({ url }) => url.pathname.endsWith('/data/questions.json'),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'questions-cache',
              networkTimeoutSeconds: 5,
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
    // Generate source maps but don't link them from JS. Lets us debug
    // production issues without exposing them to casual visitors.
    sourcemap: 'hidden',
  },
});
