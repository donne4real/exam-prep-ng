import { Link } from 'react-router-dom';
import React, { useEffect, useState } from 'react';
import { listExams, getState, subscribe } from '../data/loader';
import type { ExamMeta } from '../types/exam';
import { useProgressStore, averageScore, practiceStreak } from '../store/progress';

export function Home() {
  const [status, setStatus] = useState(() => getState().status);
  const [tick, setTick] = useState(0);
  useEffect(() => subscribe(() => {
    setStatus(getState().status);
    setTick((t) => t + 1);
  }), []);
  // Recompute when loader notifies
  const exams = React.useMemo(() => listExams(), [tick]);
  const attempts = useProgressStore((s) => s.attempts);
  const avg = averageScore(attempts);
  const streak = practiceStreak(attempts);

  return (
    <div className="space-y-8">
      <section className="rounded-3xl bg-gradient-to-br from-nigeria-green to-nigeria-green-dark text-white p-6 sm:p-10 shadow-lg">
        <div className="flex flex-col gap-3 max-w-2xl">
          <span className="pill bg-white/15 text-white w-fit">Nigerian exam prep</span>
          <h1 className="text-3xl sm:text-4xl font-bold leading-tight">
            Practice real past questions for BECE and JAMB.
          </h1>
          <p className="text-white/85 text-base sm:text-lg">
            Free, offline-first, built for low-end Android phones. WAEC and NECO banks are on the way — pick an exam below to begin.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <a
              href="#pick-an-exam"
              className="btn bg-white text-nigeria-green-dark hover:bg-nigeria-gold hover:text-neutral-900 font-bold"
            >
              Start Practicing
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M5 12h14M13 5l7 7-7 7" />
              </svg>
            </a>
            <Link
              to="/dashboard"
              className="btn bg-white/10 text-white hover:bg-white/20 border border-white/30"
            >
              View Progress
            </Link>
          </div>
        </div>
      </section>

      {status === 'empty' || status === 'error' ? (
        <EmptyContentState status={status} />
      ) : null}

      <section aria-labelledby="pick-an-exam">
        <div className="flex items-baseline justify-between mb-3">
          <h2 id="pick-an-exam" className="text-xl font-bold">
            Pick an exam
          </h2>
          <span className="text-sm text-neutral-500 dark:text-neutral-400">
            {attempts.length} {attempts.length === 1 ? 'attempt' : 'attempts'} · avg {avg}% · {streak}-day streak
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {exams.map((exam) => (
            <ExamCard key={exam.id} exam={exam} />
          ))}
        </div>
      </section>
    </div>
  );
}

function ExamCard({ exam }: { exam: ExamMeta }) {
  return (
    <Link
      to={`/exam/${exam.id}`}
      className="card p-5 hover:border-nigeria-green hover:shadow-md transition group"
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="pill bg-nigeria-green/10 text-nigeria-green dark:text-nigeria-green-light">
            {exam.id}
          </div>
          <h3 className="mt-3 text-lg font-bold">{exam.fullName}</h3>
          <p className="mt-1 text-sm text-neutral-600 dark:text-neutral-400 leading-relaxed">
            {exam.description}
          </p>
        </div>
        <span className="rounded-full bg-nigeria-gold/20 text-nigeria-gold-dark dark:text-nigeria-gold p-2 group-hover:bg-nigeria-gold group-hover:text-neutral-900 transition">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M5 12h14M13 5l7 7-7 7" />
          </svg>
        </span>
      </div>
      <div className="mt-4 text-xs text-neutral-500 dark:text-neutral-400">
        Typical duration: {exam.durationMinutes} minutes
      </div>
    </Link>
  );
}

function EmptyContentState({ status }: { status: string }) {
  return (
    <div className="card p-6 border-l-4 border-l-nigeria-gold bg-nigeria-gold/5">
      <div className="flex items-start gap-3">
        <div className="h-9 w-9 rounded-full bg-nigeria-gold/20 text-nigeria-gold-dark dark:text-nigeria-gold flex items-center justify-center shrink-0">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4M12 16h.01" />
          </svg>
        </div>
        <div>
          <h2 className="font-semibold">
            {status === 'error' ? 'Content not available yet' : 'Loading content'}
          </h2>
          <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1 leading-relaxed">
            {status === 'error'
              ? "We couldn't load the question bank. Check your connection and refresh, or install the app for offline access."
              : 'The exam question bank is being prepared. You can still explore the app — your progress will be saved locally once questions arrive.'}
          </p>
        </div>
      </div>
    </div>
  );
}
