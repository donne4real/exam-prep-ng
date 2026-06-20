// Shared formatters + grading helpers. Kept dependency-free so they can be
// imported from both React components and unit tests without dragging in
// the rest of the app.

import type { Attempt } from '../types/exam';

export type GradeBand = Attempt['gradeBand'];

export const GRADE_BANDS: GradeBand[] = ['A', 'B', 'C', 'D', 'F'];

export function gradeFor(pct: number): GradeBand {
  if (pct >= 75) return 'A';
  if (pct >= 60) return 'B';
  if (pct >= 50) return 'C';
  if (pct >= 40) return 'D';
  return 'F';
}

/**
 * Returns a Tailwind background class for a percentage. Centralised so we
 * don't have the same `pct >= 70 ? 'bg-emerald-500' : ...` ladder in three
 * different files.
 */
export function scoreColor(pct: number): string {
  if (pct >= 70) return 'bg-emerald-500';
  if (pct >= 50) return 'bg-amber-400';
  return 'bg-red-500';
}

export function gradeColor(grade: GradeBand): string {
  switch (grade) {
    case 'A':
      return 'bg-emerald-500';
    case 'B':
      return 'bg-emerald-400';
    case 'C':
      return 'bg-amber-400';
    case 'D':
      return 'bg-orange-500';
    case 'F':
      return 'bg-red-500';
  }
}

export function formatDuration(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${m}m ${String(rem).padStart(2, '0')}s`;
}

// Cached Intl formatters. Constructing these on every render is wasteful.
const dateFormatter = new Intl.DateTimeFormat('en-NG', {
  dateStyle: 'medium',
  timeStyle: 'short',
});

const timeOnlyFormatter = new Intl.DateTimeFormat('en-NG', {
  timeStyle: 'short',
});

export function formatDate(epochMs: number): string {
  return dateFormatter.format(new Date(epochMs));
}

export function formatTime(epochMs: number): string {
  return timeOnlyFormatter.format(new Date(epochMs));
}
