import { Link, NavLink, useLocation } from 'react-router-dom';
import { useSettingsStore, type ThemeMode } from '../store/settings';

const navLinks: { to: string; label: string }[] = [
  { to: '/', label: 'Home' },
  { to: '/dashboard', label: 'Progress' },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const theme = useSettingsStore((s) => s.theme);
  const setTheme = useSettingsStore((s) => s.setTheme);

  const cycleTheme = () => {
    const order: ThemeMode[] = ['auto', 'light', 'dark'];
    const next = order[(order.indexOf(theme) + 1) % order.length];
    setTheme(next);
  };

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
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M4 19V5" />
                <path d="M4 5h12l-3 4 3 4H4" />
                <path d="M20 19V5" />
              </svg>
            </span>
            <span className="hidden sm:inline">ExamPrep NG</span>
          </Link>
          <nav className="ml-auto flex items-center gap-1">
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
              onClick={cycleTheme}
              className="ml-1 inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium min-h-tap text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              aria-label={`Theme: ${themeLabel}. Click to change.`}
              title={`Theme: ${themeLabel}`}
            >
              {theme === 'dark' ? <MoonIcon /> : theme === 'light' ? <SunIcon /> : <AutoIcon />}
              <span className="hidden sm:inline">{themeLabel}</span>
            </button>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <div className={`mx-auto w-full max-w-5xl px-4 ${minimal ? 'py-0' : 'py-5 sm:py-8'}`}>
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

function SunIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}
function MoonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}
function AutoIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="4" width="18" height="14" rx="2" />
      <path d="M8 20h8M12 18v2" />
    </svg>
  );
}
