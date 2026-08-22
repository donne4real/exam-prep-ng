# Nigerian Exam Prep (PWA)

An offline-first Progressive Web App for practising past questions for
**BECE**, **NECO**, and **JAMB** exams. Built with Vite + React + TypeScript,
Tailwind CSS, Zustand, React Router, and `vite-plugin-pwa`.

The app is designed to run fast on cheap Android phones (Tecno, Infinix) and
to work offline once the user installs it.

---

## Features

- **6 routes**: Home, Subjects, Years, Test Runner, Results, Dashboard
- **PWA install** with custom install banner (`InstallPrompt`)
- **Offline support** via Workbox service worker (cache-first for assets,
  stale-while-revalidate for `data/questions.json`)
- **Dark mode** — auto / light / dark, persisted in `localStorage`
- **Progress tracking** — attempts, average score, weak topics, day streak
- **Timed tests** with auto-submit on expiry
- **Friendly empty state** when `data/questions.json` is not yet available
- **Mobile-first** — 44px minimum tap targets, large readable typography

## Tech stack

| Concern        | Choice                                    |
| -------------- | ----------------------------------------- |
| Bundler        | Vite 5                                    |
| UI framework   | React 18 + TypeScript 5                   |
| Styling        | Tailwind CSS 3                            |
| State          | Zustand 4 (persisted to `localStorage`)   |
| Routing        | React Router 6                            |
| PWA / SW       | `vite-plugin-pwa` (Workbox under the hood)|
| Fonts          | Inter (Google Fonts) with system fallback |

## Project structure

```
exam-prep-ng/
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json
├── vite.config.ts
├── public/
│   ├── favicon.svg
│   ├── manifest.json
│   └── robots.txt
└── src/
    ├── App.tsx
    ├── main.tsx
    ├── components/
    │   ├── InstallPrompt.tsx
    │   ├── OptionButton.tsx
    │   ├── ProgressRing.tsx
    │   ├── QuestionCard.tsx
    │   ├── Shell.tsx
    │   └── Timer.tsx
    ├── data/
    │   └── loader.ts
    ├── routes/
    │   ├── Dashboard.tsx
    │   ├── Home.tsx
    │   ├── Results.tsx
    │   ├── Subjects.tsx
    │   ├── TestRunner.tsx
    │   └── Years.tsx
    ├── store/
    │   ├── progress.ts
    │   └── settings.ts
    ├── styles/
    │   └── index.css
    └── types/
        └── exam.ts
```

## Setup

Requirements: **Node.js 18+** (tested on Node 22).

```bash
cd exam-prep-ng
npm install
```

## Develop

```bash
npm run dev
```

Opens Vite dev server at <http://localhost:5173>. The service worker is
registered in dev too (via `devOptions.enabled`), so you can test offline
behavior.

## Build

```bash
npm run build
```

Outputs to `dist/`. The output is a fully static SPA — deploy to any static
host (Netlify, Vercel, Cloudflare Pages, GitHub Pages, etc.).

## Preview production build

```bash
npm run preview
```

## Question data

The app expects `public/data/questions.json` with this shape:

```ts
type QuestionsFile = {
  version: number;
  generatedAt?: string;
  exams: ExamMeta[];
  subjects: SubjectMeta[];
  questions: Question[];
};
```

See `src/types/exam.ts` for the full schema. If the file is missing or empty,
the UI renders gracefully — exam/subject scaffolds are shown with badges
indicating that content isn't ready yet.

## PWA install

On Android Chrome / iOS Safari, the app can be added to the home screen.
On Chrome/Edge the `InstallPrompt` component listens for
`beforeinstallprompt` and surfaces a banner. Users can also use the browser's
"Add to Home screen" menu item.

## Offline behavior

- HTML/CSS/JS/fonts/images: cached on first load (precache manifest).
- `data/questions.json`: `StaleWhileRevalidate` (uses cached version when
  offline, fetches a fresh copy when online).
- App shell navigation: `NetworkFirst` so the latest HTML is preferred when
  online, but cached when offline.

## Storage

- Progress (attempts): `localStorage` key `exam-prep-ng-progress`
- Settings (theme, last exam, install prompt dismissal): `exam-prep-ng-settings`

Both keys can be cleared from the browser devtools if you need to reset state.

## Design

- Primary color: **Nigerian green** `#008751`
- Accent: **Nigerian gold** `#FFD700`
- Neutral background with optional dark mode
- Font: Inter
- No emoji-driven cartoon imagery; this is meant to feel like a serious
  study tool.

## License

MIT
