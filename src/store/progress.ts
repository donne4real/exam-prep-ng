// Persistent progress tracking via Zustand + localStorage.
// Stores past attempts, computes weak topics, streaks, and average score.

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { Attempt, AttemptAnswer } from '../types/exam';
import { gradeFor } from '../lib/grade';
import { STORAGE_KEYS } from './storageKeys';

export interface RecordAttemptInput {
  exam: Attempt['exam'];
  subject: string;
  year: number;
  startedAt: number;
  submittedAt: number;
  durationSeconds: number;
  answers: AttemptAnswer[];
  totalQuestions: number;
  correctCount: number;
}

interface ProgressState {
  attempts: Attempt[];

  recordAttempt: (input: RecordAttemptInput) => Attempt;
  clear: () => void;
}

function makeId(): string {
  return crypto.randomUUID();
}

export const useProgressStore = create<ProgressState>()(
  persist(
    (set) => ({
      attempts: [],

      recordAttempt: (input) => {
        const percentage =
          input.totalQuestions === 0
            ? 0
            : Math.round((input.correctCount / input.totalQuestions) * 100);
        const attempt: Attempt = {
          id: makeId(),
          exam: input.exam,
          subject: input.subject,
          year: input.year,
          startedAt: input.startedAt,
          submittedAt: input.submittedAt,
          durationSeconds: input.durationSeconds,
          answers: input.answers,
          totalQuestions: input.totalQuestions,
          correctCount: input.correctCount,
          percentage,
          gradeBand: gradeFor(percentage),
        };
        set((state) => ({ attempts: [attempt, ...state.attempts] }));
        return attempt;
      },

      clear: () => set({ attempts: [] }),
    }),
    {
      name: STORAGE_KEYS.progress,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ attempts: state.attempts }),
    },
  ),
);

// ----- selectors (pure, no React) -----------------------------------------

export function averageScore(attempts: Attempt[]): number {
  if (attempts.length === 0) return 0;
  const sum = attempts.reduce((acc, a) => acc + a.percentage, 0);
  return Math.round(sum / attempts.length);
}

/**
 * Consecutive-day streak (inclusive of today if practiced today).
 * Compares calendar dates in local time.
 */
export function practiceStreak(attempts: Attempt[]): number {
  if (attempts.length === 0) return 0;
  const days = new Set<string>();
  for (const a of attempts) {
    days.add(toDateKey(new Date(a.submittedAt)));
  }
  let streak = 0;
  const cursor = new Date();
  // If user hasn't practiced today, anchor streak to yesterday.
  if (!days.has(toDateKey(cursor))) {
    cursor.setDate(cursor.getDate() - 1);
  }
  while (days.has(toDateKey(cursor))) {
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  return streak;
}

export interface TopicStat {
  topic: string;
  total: number;
  correct: number;
  percentage: number;
}

export function weakTopics(attempts: Attempt[], limit = 5): TopicStat[] {
  const map = new Map<string, TopicStat>();
  for (const a of attempts) {
    for (const ans of a.answers) {
      const topic = ans.topic ?? 'General';
      const stat = map.get(topic) ?? {
        topic,
        total: 0,
        correct: 0,
        percentage: 0,
      };
      stat.total += 1;
      if (ans.correct) stat.correct += 1;
      map.set(topic, stat);
    }
  }
  return Array.from(map.values())
    .filter((s) => s.total > 0)
    .map((s) => ({ ...s, percentage: Math.round((s.correct / s.total) * 100) }))
    .sort((a, b) => a.percentage - b.percentage || b.total - a.total)
    .slice(0, limit);
}

export interface ExamBreakdown {
  exam: Attempt['exam'];
  attempts: number;
  avg: number;
  correct: number;
  total: number;
}

export function examBreakdown(attempts: Attempt[]): ExamBreakdown[] {
  const map = new Map<
    Attempt['exam'],
    { count: number; sum: number; correct: number; total: number }
  >();
  for (const a of attempts) {
    const stat = map.get(a.exam) ?? { count: 0, sum: 0, correct: 0, total: 0 };
    stat.count += 1;
    stat.sum += a.percentage;
    stat.correct += a.correctCount;
    stat.total += a.totalQuestions;
    map.set(a.exam, stat);
  }
  return Array.from(map.entries()).map(([exam, v]) => ({
    exam,
    attempts: v.count,
    avg: v.count === 0 ? 0 : Math.round(v.sum / v.count),
    correct: v.correct,
    total: v.total,
  }));
}

function toDateKey(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}
