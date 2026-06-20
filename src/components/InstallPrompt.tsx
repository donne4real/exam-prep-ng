import { useEffect, useState } from 'react';
import { useSettingsStore } from '../store/settings';
import { DownloadIcon, ShareIcon, XIcon } from './icons';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

function isIosSafari(): boolean {
  if (typeof navigator === 'undefined') return false;
  const ua = navigator.userAgent;
  const isIOS = /iPad|iPhone|iPod/.test(ua);
  // WebKit only (no Chrome/Firefox on iOS)
  const isWebKit = /WebKit/.test(ua);
  const isStandalone =
    typeof window !== 'undefined' &&
    ('standalone' in navigator ? (navigator as Navigator & { standalone?: boolean }).standalone === true : false);
  return isIOS && isWebKit && !isStandalone;
}

export function InstallPrompt() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const settingsDismissed = useSettingsStore((s) => s.installPromptDismissed);
  const dismissPermanently = useSettingsStore((s) => s.dismissInstallPrompt);
  const [installed, setInstalled] = useState(false);
  // iOS doesn't fire beforeinstallprompt, so we keep a separate visible flag.
  const [iosDismissed, setIosDismissed] = useState(false);

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

  // Chromium / Edge path: beforeinstallprompt has fired.
  if (deferred) {
    if (settingsDismissed) return null;
    return <ChromePrompt deferred={deferred} onDismiss={dismissPermanently} />;
  }

  // iOS Safari path: show manual install instructions.
  if (isIosSafari() && !iosDismissed && !settingsDismissed) {
    return <IosPrompt onDismiss={() => setIosDismissed(true)} />;
  }

  return null;
}

function ChromePrompt({
  deferred,
  onDismiss,
}: {
  deferred: BeforeInstallPromptEvent;
  onDismiss: () => void;
}) {
  const handleInstall = async () => {
    try {
      await deferred.prompt();
      await deferred.userChoice;
    } catch {
      // ignore
    } finally {
      // Either outcome: hide the prompt. If accepted, appinstalled will
      // also fire; if dismissed, the user already saw it.
    }
  };

  return (
    <div
      className="fixed inset-x-3 bottom-3 sm:bottom-4 z-40 card border-nigeria-green border-2 p-4 flex items-center gap-3 shadow-lg animate-slide-up"
      role="region"
      aria-label="Install app"
    >
      <div className="h-10 w-10 rounded-xl bg-nigeria-green text-white flex items-center justify-center shrink-0">
        <DownloadIcon size={20} />
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
        onClick={onDismiss}
        aria-label="Dismiss install prompt"
        className="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 min-h-tap min-w-tap px-1 inline-flex items-center justify-center"
      >
        <XIcon size={16} />
      </button>
    </div>
  );
}

function IosPrompt({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div
      className="fixed inset-x-3 bottom-3 sm:bottom-4 z-40 card border-nigeria-green border-2 p-4 shadow-lg animate-slide-up"
      role="region"
      aria-label="Install app on iOS"
    >
      <div className="flex items-start gap-3">
        <div className="h-10 w-10 rounded-xl bg-nigeria-green text-white flex items-center justify-center shrink-0">
          <ShareIcon size={20} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold leading-tight">Install ExamPrep NG</div>
          <div className="text-xs text-neutral-600 dark:text-neutral-400 leading-relaxed">
            Tap the <ShareIcon size={12} className="inline -mt-0.5" /> Share
            button, then choose <strong>Add to Home Screen</strong>.
          </div>
        </div>
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss install prompt"
          className="text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300 min-h-tap min-w-tap px-1 inline-flex items-center justify-center"
        >
          <XIcon size={16} />
        </button>
      </div>
    </div>
  );
}
