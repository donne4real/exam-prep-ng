import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, useNavigate } from 'react-router-dom';
import { App } from './App';
import './styles/index.css';
import { applyTheme, useSettingsStore } from './store/settings';

// Apply theme on first paint and re-apply when it changes.
applyTheme(useSettingsStore.getState().theme);
useSettingsStore.subscribe((state, prev) => {
  if (state.theme !== prev.theme) applyTheme(state.theme);
});

// Follow system theme changes when in auto mode.
if (typeof window !== 'undefined' && window.matchMedia) {
  const mql = window.matchMedia('(prefers-color-scheme: dark)');
  mql.addEventListener('change', () => {
    if (useSettingsStore.getState().theme === 'auto') applyTheme('auto');
  });
}

// Handle SPA routing after GitHub Pages 404 fallback redirect
function RedirectHandler() {
  const navigate = useNavigate();
  const redirectPath = sessionStorage.getItem('spa_redirect');
  if (redirectPath) {
    sessionStorage.removeItem('spa_redirect');
    // Strip the base path prefix if present
    const path = redirectPath.replace(/^\/exam-prep-ng/, '') || '/';
    navigate(path, { replace: true });
  }
  return null;
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <RedirectHandler />
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
