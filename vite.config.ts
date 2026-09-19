import { createRequire } from 'node:module';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Load the plugin's CJS build on purpose: its ESM build cannot require() the
// CJS-only workbox-build ("Dynamic require of 'workbox-build' is not
// supported"), which broke `vite build` on Node >= 22.
const { VitePWA } = createRequire(import.meta.url)('vite-plugin-pwa') as typeof import('vite-plugin-pwa');

// The app is hosted at four different base paths, so pick one per target:
//   GitHub Pages  -> /exam-prep-ng/   (default, `npm run build`)
//   Netlify       -> /                (Netlify sets NETLIFY=true in CI)
//   Cloudflare    -> /                (Cloudflare Pages sets CF_PAGES=true)
//   Android APK   -> /                (`vite build --mode android`, Capacitor)
// The PWA scope/start_url and the router basename follow this value.
const baseFor = (mode: string) =>
  process.env.NETLIFY || process.env.CF_PAGES || mode === 'android' ? '/' : '/exam-prep-ng/';

export default defineConfig(({ mode }) => {
  const base = baseFor(mode);
  return {
  // Set base path for GitHub Pages deployment at /exam-prep-ng/
  base,
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
        // GitHub Pages and from / on Netlify. A scope wider than the SW's
        // own path breaks installs.
        scope: base,
        start_url: base,
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
            // Serve cached data files instantly and refresh in the background:
            // revisits (especially offline) must not wait on the network.
            // Covers data/index.json and the per-subject data/banks/*.json.
            urlPattern: ({ url }) =>
              url.pathname.includes('/data/') && url.pathname.endsWith('.json'),
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'questions-cache',
              expiration: {
                maxEntries: 16,
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
  };
});
