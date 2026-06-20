import { Link, NavLink, useLocation } from 'react-router-dom';
import { useSettingsStore, type ThemeMode } from '../store/settings';
import { AutoIcon, BrandMark, MoonIcon, SunIcon } from './icons';

const navLinks: { to: string; label: string }[] = [
  { to: '/', label: 'Home' },
  { to: '/dashboard', label: 'Progress' },
];

const THEME_ORDER: ThemeMode[] = ['auto', 'light', 'dark'];

function nextTheme(mode: ThemeMode): ThemeMode {
  return THEME_ORDER[(THEME_ORDER.indexOf(mode) + 1) % THEME_ORDER.length];
}

export function Shell({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const theme = useSettingsStore((s) => s.theme);
  const setTheme = useSettingsStore((s) => s.setTheme);

  const themeLabel =
    theme === 'auto' ? 'System' : theme === 'dark' ? 'Dark' : 'Light';

  // Hide chrome on the test runner for a distraction-free exam screen.
  const minimal = /^\/practice\/[^/]+\/[^/]+$/.test(location.pathname);

  return (
    <div className="min-h-full flex flex-col">
      <header
        className={`sticky top-0 z-30 bg-white/90 dark:bg-neutral-950/90 backdrop-blur border-b border-neutral-200 dark:border-neutral-800 ${
          minimal ? 'hidden' : ''
        }`}
      >
        <div className="mx-auto max-w-5xl px-4 h-14 flex items-center gap-2">
          <Link to="/" className="flex items-center gap-2 font-bold text-lg">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-nigeria-green text-white">
              <BrandMark size={18} />
            </span>
            <span className="hidden sm:inline">ExamPrep NG</span>
          </Link>
          <nav className="ml-auto flex items-center gap-1" aria-label="Primary">
            {navLinks.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === '/'}
                className={({ isActive }) =>
                  `px-3 py-2 rounded-lg text-sm font-medium min-h-tap inline-flex items-center ${
                    isActive
                      ? 'bg-nigeria-green/10 text-nigeria-green dark:text-nigeria-green-light'
                      : 'text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800'
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
            <button
              type="button"
              onClick={() => setTheme(nextTheme(theme))}
              className="ml-1 inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium min-h-tap text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              aria-label={`Theme: ${themeLabel}. Click to change.`}
              title={`Theme: ${themeLabel}`}
            >
              {theme === 'dark' ? (
                <MoonIcon size={16} />
              ) : theme === 'light' ? (
                <SunIcon size={16} />
              ) : (
                <AutoIcon size={16} />
              )}
              <span className="hidden sm:inline">{themeLabel}</span>
            </button>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <div
          className={`mx-auto w-full max-w-5xl px-4 ${
            minimal ? 'py-0' : 'py-5 sm:py-8'
          }`}
        >
          {children}
        </div>
      </main>

      {!minimal ? (
        <footer className="border-t border-neutral-200 dark:border-neutral-800 py-6 text-center text-xs text-neutral-500 dark:text-neutral-400">
          <div>ExamPrep NG · Practice for BECE, NECO, JAMB</div>
          <div className="mt-1">Works offline once installed.</div>
        </footer>
      ) : null}
    </div>
  );
}
