import { useEffect, useRef, useState } from 'react';
import { ClockIcon } from './icons';

interface Props {
  /** Total duration in seconds. */
  durationSeconds: number;
  /** Called exactly once when the countdown reaches zero. */
  onExpire: () => void;
  paused?: boolean;
}

function fmt(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const mm = String(Math.floor(s / 60)).padStart(2, '0');
  const ss = String(s % 60).padStart(2, '0');
  return `${mm}:${ss}`;
}

/**
 * Countdown timer with `onExpire` as the *single* source of "time's up"
 * notifications. Internally we anchor to `Date.now()` (not interval tick
 * counts) so the displayed time stays accurate even if the tab is throttled
 * or backgrounded.
 */
export function Timer({ durationSeconds, onExpire, paused }: Props) {
  const [remaining, setRemaining] = useState(durationSeconds);
  const expiredRef = useRef(false);
  const onExpireRef = useRef(onExpire);
  onExpireRef.current = onExpire;

  // Reset when duration changes (e.g. parent re-renders with a new exam).
  useEffect(() => {
    setRemaining(durationSeconds);
    expiredRef.current = false;
  }, [durationSeconds]);

  useEffect(() => {
    if (paused) return;
    const deadline = Date.now() + durationSeconds * 1000;
    const id = window.setInterval(() => {
      const next = Math.max(0, Math.round((deadline - Date.now()) / 1000));
      setRemaining(next);
      if (next === 0) {
        if (expiredRef.current) return;
        expiredRef.current = true;
        window.clearInterval(id);
        onExpireRef.current();
      }
    }, 250);
    return () => window.clearInterval(id);
  }, [durationSeconds, paused]);

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
      aria-atomic="true"
      aria-label={`Time remaining: ${fmt(remaining)}`}
      role="timer"
    >
      <ClockIcon size={16} />
      {fmt(remaining)}
    </div>
  );
}
