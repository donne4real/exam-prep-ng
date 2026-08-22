import { useEffect, useRef, useState } from 'react';

interface Props {
  durationSeconds: number;
  onExpire: () => void;
  paused?: boolean;
  onTick?: (remaining: number) => void;
}

function fmt(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const mm = String(Math.floor(s / 60)).padStart(2, '0');
  const ss = String(s % 60).padStart(2, '0');
  return `${mm}:${ss}`;
}

export function Timer({ durationSeconds, onExpire, paused, onTick }: Props) {
  const [remaining, setRemaining] = useState(durationSeconds);
  const expiredRef = useRef(false);
  const onExpireRef = useRef(onExpire);
  const onTickRef = useRef(onTick);
  onExpireRef.current = onExpire;
  onTickRef.current = onTick;

  // Reset when duration changes.
  useEffect(() => {
    setRemaining(durationSeconds);
    expiredRef.current = false;
  }, [durationSeconds]);

  useEffect(() => {
    if (paused) return;
    const start = Date.now();
    const startedAt = remaining;
    const id = window.setInterval(() => {
      const elapsed = Math.floor((Date.now() - start) / 1000);
      const next = Math.max(0, startedAt - elapsed);
      setRemaining(next);
      onTickRef.current?.(next);
      if (next === 0 && !expiredRef.current) {
        expiredRef.current = true;
        window.clearInterval(id);
        onExpireRef.current();
      }
    }, 250);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paused]);

  const warn = remaining <= 60;
  const danger = remaining <= 10;

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold tabular-nums ${
        danger
          ? 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300'
          : warn
          ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
          : 'bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-200'
      }`}
      aria-live="polite"
      aria-label={`Time remaining: ${fmt(remaining)}`}
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <circle cx="12" cy="13" r="8" />
        <path d="M12 9v4l2 2" />
        <path d="M9 2h6" />
      </svg>
      {fmt(remaining)}
    </div>
  );
}
