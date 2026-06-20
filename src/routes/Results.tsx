import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMemo, useState } from 'react';
import { useProgressStore } from '../store/progress';
import { ProgressRing } from '../components/ProgressRing';
import { QuestionCard } from '../components/QuestionCard';
import { listQuestionsForSubject } from '../data/loader';
import { gradeColor, scoreColor, formatDate, formatDuration } from '../lib/grade';
import type { Question } from '../types/exam';

export function Results() {
  const { attemptId } = useParams<{ attemptId: string }>();
  const navigate = useNavigate();
  const attempts = useProgressStore((s) => s.attempts);
  const attempt = attempts.find((a) => a.id === attemptId);
  const [showAll, setShowAll] = useState(false);

  // Memoize derived data so re-renders (e.g. toggle showAll) don't recompute.
  const { reconstructedQuestions, topicStats } = useMemo(() => {
    if (!attempt) {
      return {
        reconstructedQuestions: [] as Question[],
        topicStats: [] as { topic: string; total: number; correct: number; pct: number }[],
      };
    }
    // Build a lookup map once: O(N) instead of O(N²) per question.
    const bank = listQuestionsForSubject(attempt.exam, attempt.subject);
    const map = new Map<string, Question>();
    for (const q of bank) map.set(q.id, q);

    const reconstructed: Question[] = attempt.answers.map((a) => {
      const fromBank = map.get(a.questionId);
      return (
        fromBank ?? {
          id: a.questionId,
          exam: attempt.exam,
          subject: attempt.subject,
          year: attempt.year || new Date().getFullYear(),
          prompt: '(Question no longer in local question bank)',
          options: [],
          correctOptionId: '',
        }
      );
    });

    const topicMap = new Map<string, { total: number; correct: number }>();
    for (const a of attempt.answers) {
      const t = a.topic ?? 'General';
      const stat = topicMap.get(t) ?? { total: 0, correct: 0 };
      stat.total += 1;
      if (a.correct) stat.correct += 1;
      topicMap.set(t, stat);
    }
    const topics = Array.from(topicMap.entries())
      .map(([topic, v]) => ({
        topic,
        total: v.total,
        correct: v.correct,
        pct: v.total === 0 ? 0 : Math.round((v.correct / v.total) * 100),
      }))
      .sort((a, b) => a.pct - b.pct);

    return { reconstructedQuestions: reconstructed, topicStats: topics };
  }, [attempt]);

  // Count real vs generated answers in this attempt for the header summary.
  // Uses the source snapshotted on each AttemptAnswer at submit time so
  // it works even if the question bank changes.
  const sourceStats = useMemo(() => {
    if (!attempt) return { real: 0, generated: 0, realCorrect: 0, generatedCorrect: 0 };
    let real = 0;
    let generated = 0;
    let realCorrect = 0;
    let generatedCorrect = 0;
    for (const ans of attempt.answers) {
      if (ans.source === 'generated') {
        generated += 1;
        if (ans.correct) generatedCorrect += 1;
      } else {
        real += 1;
        if (ans.correct) realCorrect += 1;
      }
    }
    return { real, generated, realCorrect, generatedCorrect };
  }, [attempt]);

  if (!attempt) {
    return (
      <div className="card p-6 text-center">
        <h1 className="text-xl font-bold mb-2">Attempt not found</h1>
        <p className="text-neutral-600 dark:text-neutral-400 mb-4">
          This attempt may have been cleared from this device.
        </p>
        <Link to="/dashboard" className="btn-primary inline-flex">
          Go to dashboard
        </Link>
      </div>
    );
  }

  const correct = attempt.correctCount;
  const total = attempt.totalQuestions;
  const pct = attempt.percentage;

  return (
    <div className="space-y-6">
      <nav
        className="text-sm text-neutral-500 dark:text-neutral-400"
        aria-label="Breadcrumb"
      >
        <Link to="/dashboard" className="hover:underline">
          Progress
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700 dark:text-neutral-200 font-medium">
          {attempt.exam} · {attempt.subject} · {attempt.year}
        </span>
      </nav>

      <header className="card p-6 grid grid-cols-1 sm:grid-cols-[auto_1fr] gap-6 items-center">
        <ProgressRing value={total === 0 ? 0 : correct / total} size={120} stroke={12} />
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`pill text-white ${gradeColor(attempt.gradeBand)}`}>
              Grade {attempt.gradeBand}
            </span>
            <span className="text-sm text-neutral-500 dark:text-neutral-400">
              {formatDate(attempt.submittedAt)}
            </span>
          </div>
          <h1 className="mt-2 text-2xl font-bold leading-tight">
            {correct} / {total} correct · {pct}%
          </h1>
          <p className="text-neutral-600 dark:text-neutral-400 mt-1">
            {attempt.exam} · {attempt.subject} · {attempt.year} · Time used{' '}
            {formatDuration(attempt.durationSeconds)}
          </p>
          {sourceStats.real + sourceStats.generated > 0 ? (
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-2 flex flex-wrap gap-x-3 gap-y-1">
              {sourceStats.real > 0 ? (
                <span>
                  <span className="font-semibold text-emerald-700 dark:text-emerald-400">
                    {sourceStats.realCorrect}/{sourceStats.real}
                  </span>{' '}
                  past-exam correct
                </span>
              ) : null}
              {sourceStats.generated > 0 ? (
                <span>
                  <span className="font-semibold text-amber-700 dark:text-amber-400">
                    {sourceStats.generatedCorrect}/{sourceStats.generated}
                  </span>{' '}
                  practice correct
                </span>
              ) : null}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-2 mt-4">
            <button
              type="button"
              className="btn-primary"
              onClick={() =>
                navigate(
                  `/practice/${attempt.exam}/${encodeURIComponent(attempt.subject)}`,
                )
              }
            >
              Retry this test
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => navigate(`/exam/${attempt.exam}`)}
            >
              More {attempt.exam} subjects
            </button>
            <Link to="/dashboard" className="btn-ghost">
              Back to progress
            </Link>
          </div>
        </div>
      </header>

      <section aria-labelledby="topic-breakdown">
        <h2 id="topic-breakdown" className="text-lg font-bold mb-3">
          Topic breakdown
        </h2>
        <div className="card divide-y divide-neutral-200 dark:divide-neutral-800">
          {topicStats.length === 0 ? (
            <div className="p-5 text-sm text-neutral-500 dark:text-neutral-400">
              No topics recorded for this attempt.
            </div>
          ) : (
            topicStats.map((s) => (
              <div key={s.topic} className="p-4">
                <div className="flex items-baseline justify-between mb-1.5">
                  <div className="font-medium">{s.topic}</div>
                  <div className="text-sm tabular-nums text-neutral-600 dark:text-neutral-400">
                    {s.correct}/{s.total} · {s.pct}%
                  </div>
                </div>
                <div
                  className="h-2 rounded-full bg-neutral-200 dark:bg-neutral-800 overflow-hidden"
                  role="progressbar"
                  aria-valuenow={s.pct}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <div
                    className={`h-full ${scoreColor(s.pct)}`}
                    style={{ width: `${s.pct}%` }}
                  />
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      <section aria-labelledby="all-questions">
        <div className="flex items-baseline justify-between mb-3">
          <h2 id="all-questions" className="text-lg font-bold">
            All questions
          </h2>
          <button
            type="button"
            onClick={() => setShowAll((v) => !v)}
            className="text-sm font-medium text-nigeria-green dark:text-nigeria-green-light hover:underline"
            aria-expanded={showAll}
          >
            {showAll ? 'Hide question list' : `Show all ${total} questions`}
          </button>
        </div>

        {showAll ? (
          <div className="space-y-4">
            {reconstructedQuestions.map((q, i) => {
              const a = attempt.answers.find((x) => x.questionId === q.id);
              return (
                <div key={q.id}>
                  <QuestionCard
                    question={q}
                    questionNumber={i + 1}
                    totalQuestions={total}
                    selectedOptionId={a?.selectedOptionId ?? null}
                    showCorrect
                    onSelect={() => undefined}
                  />
                </div>
              );
            })}
          </div>
        ) : null}
      </section>
    </div>
  );
}
