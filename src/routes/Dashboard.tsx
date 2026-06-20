import { Link } from 'react-router-dom';
import { useMemo, useState } from 'react';
import {
  averageScore,
  examBreakdown,
  practiceStreak,
  useProgressStore,
  weakTopics,
} from '../store/progress';
import { ProgressRing } from '../components/ProgressRing';
import { ConfirmDialog } from '../components/ConfirmDialog';
import {
  formatDate,
  formatDuration,
  gradeColor,
  scoreColor,
} from '../lib/grade';

export function Dashboard() {
  const attempts = useProgressStore((s) => s.attempts);
  const clear = useProgressStore((s) => s.clear);
  const [confirmClear, setConfirmClear] = useState(false);
  const [showAllAttempts, setShowAllAttempts] = useState(false);

  // Memoize derived aggregates so re-renders don't redo the full pass.
  const avg = useMemo(() => averageScore(attempts), [attempts]);
  const streak = useMemo(() => practiceStreak(attempts), [attempts]);
  const last = attempts[0];
  const weak = useMemo(() => weakTopics(attempts), [attempts]);
  const breakdown = useMemo(() => examBreakdown(attempts), [attempts]);

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold">Your progress</h1>
          <p className="text-neutral-600 dark:text-neutral-400 mt-1">
            {attempts.length === 0
              ? 'Take your first test to start tracking progress.'
              : `Across ${attempts.length} attempt${attempts.length === 1 ? '' : 's'}.`}
          </p>
        </div>
        {attempts.length > 0 ? (
          <button
            type="button"
            onClick={() => setConfirmClear(true)}
            className="btn-ghost text-sm"
          >
            Clear history
          </button>
        ) : null}
      </header>

      <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Attempts" value={attempts.length.toString()} />
        <StatCard label="Average" value={`${avg}%`} />
        <StatCard
          label="Streak"
          value={`${streak} day${streak === 1 ? '' : 's'}`}
        />
        <StatCard
          label="Last grade"
          value={last ? `Grade ${last.gradeBand}` : '—'}
          sub={last ? `${last.percentage}%` : 'Take a test'}
        />
      </section>

      {last ? (
        <section
          className="card p-5 flex items-center gap-5"
          aria-label="Last attempt"
        >
          <ProgressRing value={last.percentage / 100} size={84} stroke={9} />
          <div className="min-w-0">
            <div className="text-sm text-neutral-500 dark:text-neutral-400">
              Last attempt
            </div>
            <div className="font-semibold truncate">
              {last.exam} · {last.subject} · {last.year}
            </div>
            <div className="text-sm text-neutral-600 dark:text-neutral-400">
              {last.correctCount}/{last.totalQuestions} correct ·{' '}
              {formatDate(last.submittedAt)} · {formatDuration(last.durationSeconds)}
            </div>
            <Link
              to={`/results/${last.id}`}
              className="text-sm font-medium text-nigeria-green dark:text-nigeria-green-light hover:underline mt-2 inline-block"
            >
              View detailed results →
            </Link>
          </div>
        </section>
      ) : null}

      {weak.length > 0 ? (
        <section aria-labelledby="weak-topics">
          <h2 id="weak-topics" className="text-lg font-bold mb-3">
            Weak topics
          </h2>
          <div className="card divide-y divide-neutral-200 dark:divide-neutral-800">
            {weak.map((w) => (
              <div key={w.topic} className="p-4">
                <div className="flex items-baseline justify-between mb-1.5">
                  <div className="font-medium">{w.topic}</div>
                  <div className="text-sm tabular-nums text-neutral-600 dark:text-neutral-400">
                    {w.correct}/{w.total} · {w.percentage}%
                  </div>
                </div>
                <div
                  className="h-2 rounded-full bg-neutral-200 dark:bg-neutral-800 overflow-hidden"
                  role="progressbar"
                  aria-valuenow={w.percentage}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <div
                    className={`h-full ${scoreColor(w.percentage)}`}
                    style={{ width: `${w.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {breakdown.length > 0 ? (
        <section aria-labelledby="exam-breakdown">
          <h2 id="exam-breakdown" className="text-lg font-bold mb-3">
            By exam
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {breakdown.map((e) => (
              <div key={e.exam} className="card p-4">
                <div className="flex items-center justify-between">
                  <div className="font-semibold">{e.exam}</div>
                  <span className="pill bg-nigeria-green/10 text-nigeria-green dark:text-nigeria-green-light">
                    {e.attempts} {e.attempts === 1 ? 'attempt' : 'attempts'}
                  </span>
                </div>
                <div className="mt-3 text-3xl font-bold tabular-nums">
                  {e.avg}%
                </div>
                <div className="text-xs text-neutral-500 dark:text-neutral-400">
                  avg · {e.correct}/{e.total} questions correct
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section aria-labelledby="recent-attempts">
        <h2 id="recent-attempts" className="text-lg font-bold mb-3">
          Recent attempts
        </h2>
        {attempts.length === 0 ? (
          <div className="card p-6 text-center">
            <p className="text-neutral-600 dark:text-neutral-400">
              No attempts yet. Pick an exam from the home page to begin.
            </p>
            <Link to="/" className="btn-primary mt-4 inline-flex">
              Choose an exam
            </Link>
          </div>
        ) : (
          <>
            <div className="card divide-y divide-neutral-200 dark:divide-neutral-800">
              {(showAllAttempts ? attempts : attempts.slice(0, 20)).map((a) => (
                <Link
                  key={a.id}
                  to={`/results/${a.id}`}
                  className="flex items-center justify-between gap-3 p-4 hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition"
                >
                  <div className="min-w-0">
                    <div className="font-medium truncate">
                      {a.exam} · {a.subject} · {a.year}
                    </div>
                    <div className="text-xs text-neutral-500 dark:text-neutral-400">
                      {formatDate(a.submittedAt)}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`pill text-white ${gradeColor(a.gradeBand)}`}>
                      {a.gradeBand}
                    </span>
                    <span className="font-semibold tabular-nums">
                      {a.percentage}%
                    </span>
                  </div>
                </Link>
              ))}
            </div>
            {attempts.length > 20 ? (
              <button
                type="button"
                onClick={() => setShowAllAttempts((v) => !v)}
                className="mt-3 text-sm font-medium text-nigeria-green dark:text-nigeria-green-light hover:underline w-full text-center"
              >
                {showAllAttempts
                  ? 'Show less'
                  : `Show all ${attempts.length} attempts`}
              </button>
            ) : null}
          </>
        )}
      </section>

      {confirmClear ? (
        <ConfirmDialog
          title="Clear all attempts?"
          description="This will permanently delete your attempt history on this device. This cannot be undone."
          confirmLabel="Clear"
          cancelLabel="Cancel"
          destructive
          onCancel={() => setConfirmClear(false)}
          onConfirm={() => {
            clear();
            setConfirmClear(false);
          }}
        />
      ) : null}
    </div>
  );
}

function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="card p-4">
      <div className="text-xs uppercase tracking-wide text-neutral-500 dark:text-neutral-400">
        {label}
      </div>
      <div className="mt-1 text-2xl font-bold tabular-nums">{value}</div>
      {sub ? (
        <div className="text-xs text-neutral-500 dark:text-neutral-400">
          {sub}
        </div>
      ) : null}
    </div>
  );
}
