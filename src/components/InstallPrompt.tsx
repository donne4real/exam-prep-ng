import { useEffect, useState } from 'react';
import { useSettingsStore } from '../store/settings';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export function InstallPrompt() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(
    null,
  );
  const [dismissed, setDismissed] = useState(false);
  const settingsDismissed = useSettingsStore((s) => s.installPromptDismissed);
  const dismissPermanently = useSettingsStore((s) => s.dismissInstallPrompt);
  const [installed, setInstalled] = useState(false);

  useEffect(() => {
    const onBefore = (e: Event) => {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
    };
    const onInstalled = () => {
      setInstalled(true);
      setDeferred(null);
    };
    window.addEventListener('beforeinstallprompt', onBefore);
    window.addEventListener('appinstalled', onInstalled);
    return () => {
      window.removeEventListener('beforeinstallprompt', onBefore);
      window.removeEventListener('appinstalled', onInstalled);
    };
  }, []);

  if (installed) return null;
  if (settingsDismissed || dismissed) return null;
  if (!deferred) return null;

  const handleInstall = async () => {
    try {
      await deferred.prompt();
      await deferred.userChoice;
    } catch {
      // ignore
    } finally {
      setDeferred(null);
    }
  };

  return (
    <div
      className="fixed inset-x-3 bottom-3 sm:bottom-4 z-40 card border-nigeria-green border-2 p-4 flex items-center gap-3 shadow-lg animate-slide-up"
      role="region"
      aria-label="Install app"
    >
      <div className="h-10 w-10 rounded-xl bg-nigeria-green text-white flex items-center justify-center shrink-0">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M12 3v12" />
          <path d="M7 10l5 5 5-5" />
          <path d="M5 21h14" />
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-semibold leading-tight">Install ExamPrep NG</div>
        <div className="text-xs text-neutral-600 dark:text-neutral-400 truncate">
          Add to your home screen for offline practice.
        </div>
      </div>
      <button
        type="button"
        onClick={handleInstall}
        className="btn-primary text-sm px-3"
      >
        Install
      </button>
      <button
        type="button"
        onClick={() => {
          setDismissed(true);
          dismissPermanently();
        }}
        aria-label="Dismiss install prompt"
        className="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 min-h-tap min-w-tap px-1"
      >
        ✕
      </button>
    </div>
  );
}
