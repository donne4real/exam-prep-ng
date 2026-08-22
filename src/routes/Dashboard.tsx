import { Link } from 'react-router-dom';
import {
  averageScore,
  practiceStreak,
  useProgressStore,
  weakTopics,
} from '../store/progress';
import { ProgressRing } from '../components/ProgressRing';

export function Dashboard() {
  const attempts = useProgressStore((s) => s.attempts);
  const clear = useProgressStore((s) => s.clear);

  const avg = averageScore(attempts);
  const streak = practiceStreak(attempts);
  const last = attempts[0];
  const weak = weakTopics(attempts);

  const examBreakdown = (() => {
    const map = new Map<string, { total: number; correct: number; count: number; sum: number }>();
    for (const a of attempts) {
      const key = a.exam;
      const stat = map.get(key) ?? { total: 0, correct: 0, count: 0, sum: 0 };
      stat.total += a.totalQuestions;
      stat.correct += a.correctCount;
      stat.count += 1;
      stat.sum += a.percentage;
      map.set(key, stat);
    }
    return Array.from(map.entries()).map(([exam, v]) => ({
      exam,
      avg: v.count === 0 ? 0 : Math.round(v.sum / v.count),
      attempts: v.count,
      correct: v.correct,
      total: v.total,
    }));
  })();

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
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
            onClick={() => {
              if (window.confirm('Clear all attempts? This cannot be undone.')) {
                clear();
              }
            }}
            className="btn-ghost text-sm"
          >
            Clear history
          </button>
        ) : null}
      </header>

      <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Attempts" value={attempts.length.toString()} />
        <StatCard label="Average" value={`${avg}%`} />
        <StatCard label="Streak" value={`${streak} day${streak === 1 ? '' : 's'}`} />
        <StatCard
          label="Last grade"
          value={last ? `Grade ${last.gradeBand}` : '—'}
          sub={last ? `${last.percentage}%` : 'Take a test'}
        />
      </section>

      {last ? (
        <section className="card p-5 flex items-center gap-5" aria-label="Last attempt">
          <ProgressRing value={last.percentage / 100} size={84} stroke={9} />
          <div className="min-w-0">
            <div className="text-sm text-neutral-500 dark:text-neutral-400">Last attempt</div>
            <div className="font-semibold truncate">
              {last.exam} · {last.subject} · {last.year}
            </div>
            <div className="text-sm text-neutral-600 dark:text-neutral-400">
              {last.correctCount}/{last.totalQuestions} correct ·{' '}
              {new Date(last.submittedAt).toLocaleString()}
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
                <div className="h-2 rounded-full bg-neutral-200 dark:bg-neutral-800 overflow-hidden">
                  <div
                    className={`h-full ${
                      w.percentage >= 70
                        ? 'bg-emerald-500'
                        : w.percentage >= 50
                        ? 'bg-amber-400'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${w.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {examBreakdown.length > 0 ? (
        <section aria-labelledby="exam-breakdown">
          <h2 id="exam-breakdown" className="text-lg font-bold mb-3">
            By exam
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {examBreakdown.map((e) => (
              <div key={e.exam} className="card p-4">
                <div className="flex items-center justify-between">
                  <div className="font-semibold">{e.exam}</div>
                  <span className="pill bg-nigeria-green/10 text-nigeria-green dark:text-nigeria-green-light">
                    {e.attempts} {e.attempts === 1 ? 'attempt' : 'attempts'}
                  </span>
                </div>
                <div className="mt-3 text-3xl font-bold tabular-nums">{e.avg}%</div>
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
          <div className="card divide-y divide-neutral-200 dark:divide-neutral-800">
            {attempts.slice(0, 20).map((a) => (
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
                    {new Date(a.submittedAt).toLocaleString()}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span
                    className={`pill text-white ${
                      a.gradeBand === 'A'
                        ? 'bg-emerald-500'
                        : a.gradeBand === 'B'
                        ? 'bg-emerald-400'
                        : a.gradeBand === 'C'
                        ? 'bg-amber-400'
                        : a.gradeBand === 'D'
                        ? 'bg-orange-500'
                        : 'bg-red-500'
                    }`}
                  >
                    {a.gradeBand}
                  </span>
                  <span className="font-semibold tabular-nums">{a.percentage}%</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
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
      {sub ? <div className="text-xs text-neutral-500 dark:text-neutral-400">{sub}</div> : null}
    </div>
  );
}
