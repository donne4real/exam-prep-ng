// Persistent progress tracking via Zustand + localStorage.
// Stores past attempts, computes weak topics, streaks, and average score.

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { Attempt, AttemptAnswer, Question } from '../types/exam';

interface ProgressState {
  attempts: Attempt[];
  /** Best-effort map of attemptId -> questionId -> explanation available. */
  hydrated: boolean;

  recordAttempt: (input: {
    exam: Attempt['exam'];
    subject: string;
    year: number;
    startedAt: number;
    submittedAt: number;
    durationSeconds: number;
    answers: AttemptAnswer[];
    totalQuestions: number;
    correctCount: number;
    questions: Question[];
  }) => Attempt;

  clear: () => void;
}

function gradeFor(pct: number): Attempt['gradeBand'] {
  if (pct >= 75) return 'A';
  if (pct >= 60) return 'B';
  if (pct >= 50) return 'C';
  if (pct >= 40) return 'D';
  return 'F';
}

function makeId(): string {
  return `att_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

export const useProgressStore = create<ProgressState>()(
  persist(
    (set) => ({
      attempts: [],
      hydrated: false,

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
      name: 'exam-prep-ng-progress',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ attempts: state.attempts }),
      onRehydrateStorage: () => (state) => {
        if (state) state.hydrated = true;
      },
    },
  ),
);

// ----- selectors -----------------------------------------------------------

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
    const d = new Date(a.submittedAt);
    days.add(toDateKey(d));
  }
  let streak = 0;
  const cursor = new Date();
  // If user hasn't practiced today, the streak is anchored to yesterday.
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

export function weakTopics(
  attempts: Attempt[],
  limit = 5,
): TopicStat[] {
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
  const list = Array.from(map.values())
    .filter((s) => s.total > 0)
    .map((s) => ({ ...s, percentage: Math.round((s.correct / s.total) * 100) }));
  list.sort((a, b) => a.percentage - b.percentage || b.total - a.total);
  return list.slice(0, limit);
}

function toDateKey(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}
