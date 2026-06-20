// App settings: theme preference, last-used exam/subject for quick resume.

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { ExamType } from '../types/exam';
import { STORAGE_KEYS } from './storageKeys';

export type ThemeMode = 'auto' | 'light' | 'dark';

interface SettingsState {
  theme: ThemeMode;
  installPromptDismissed: boolean;
  lastExam: ExamType | null;
  lastSubject: string | null;

  setTheme: (mode: ThemeMode) => void;
  dismissInstallPrompt: () => void;
  setLast: (exam: ExamType, subject: string) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'auto',
      installPromptDismissed: false,
      lastExam: null,
      lastSubject: null,

      setTheme: (mode) => set({ theme: mode }),
      dismissInstallPrompt: () => set({ installPromptDismissed: true }),
      setLast: (exam, subject) =>
        set({ lastExam: exam, lastSubject: subject }),
    }),
    {
      name: STORAGE_KEYS.settings,
      storage: createJSONStorage(() => localStorage),
    },
  ),
);

// ----- theme helpers -------------------------------------------------------

export function applyTheme(mode: ThemeMode): void {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  const resolved =
    mode === 'auto'
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      : mode;
  root.classList.toggle('dark', resolved === 'dark');
  root.style.colorScheme = resolved;
}
