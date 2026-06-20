import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  getExamMeta,
  listQuestionsForSubject,
  loadQuestions,
} from '../data/loader';
import { useLoaderState } from '../lib/useLoaderState';
import type { AttemptAnswer, ExamType, Question } from '../types/exam';
import { QuestionCard } from '../components/QuestionCard';
import { Timer } from '../components/Timer';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { useProgressStore } from '../store/progress';

const KNOWN: ExamType[] = ['BECE', 'NECO', 'JAMB', 'WAEC'];

function shuffle<T>(items: T[]): T[] {
  const arr = items.slice();
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

export function TestRunner() {
  const { examId, subjectId } = useParams<{
    examId: string;
    subjectId: string;
  }>();
  const exam = (KNOWN.includes(examId as ExamType) ? examId : 'BECE') as ExamType;
  const subject = subjectId ? decodeURIComponent(subjectId) : '';

  const navigate = useNavigate();
  const recordAttempt = useProgressStore((s) => s.recordAttempt);
  const loaderState = useLoaderState();

  // Kick off data load as soon as we mount. Safe under React 18 StrictMode:
  // loadQuestions is idempotent and short-circuits when already ready.
  useEffect(() => {
    void loadQuestions();
  }, []);

  const questions = useMemo<Question[]>(() => {
    const all = listQuestionsForSubject(exam, subject);
    const shuffled = shuffle(all);
    return shuffled.slice(0, Math.min(40, shuffled.length));
  }, [exam, subject, loaderState.status, loaderState.file]);

  const meta = getExamMeta(exam);
  const durationSeconds = (meta?.durationMinutes ?? 30) * 60;

  const [startedAt] = useState(() => Date.now());
  const [answers, setAnswers] = useState<Record<string, string | null>>({});
  const [index, setIndex] = useState(0);
  const [confirming, setConfirming] = useState(false);
  const submittedRef = useRef(false);

  const total = questions.length;
  const current: Question | undefined = questions[index];
  const answered = useMemo(
    () => Object.values(answers).filter(Boolean).length,
    [answers],
  );
  const allAnswered = answered === total && total > 0;

  // Source of truth: Timer fires onExpire exactly once. The caller
  // (TestRunner) is responsible for the "submit on expiry" logic and for
  // the double-submit guard via submittedRef.
  const handleExpire = () => {
    if (submittedRef.current) return;
    submit();
  };

  const handleSelect = (optionId: string) => {
    if (submittedRef.current || !current) return;
    setAnswers((prev) => ({ ...prev, [current.id]: optionId }));
  };

  const submit = () => {
    if (submittedRef.current) return;
    submittedRef.current = true;

    const attemptAnswers: AttemptAnswer[] = questions.map((q) => {
      const selected = answers[q.id] ?? null;
      const correct = selected === q.correctOptionId;
      return {
        questionId: q.id,
        selectedOptionId: selected,
        correct,
        topic: q.topic,
        subject: q.subject,
        source: q.source,
      };
    });
    const correctCount = attemptAnswers.filter((a) => a.correct).length;
    const submittedAt = Date.now();
    const attempt = recordAttempt({
      exam,
      subject,
      // Use the dominant year from the question set, falling back to
      // the current year for synthetic/empty cases.
      year: questions[0]?.year ?? new Date().getFullYear(),
      startedAt,
      submittedAt,
      durationSeconds: Math.min(
        durationSeconds,
        Math.round((submittedAt - startedAt) / 1000),
      ),
      answers: attemptAnswers,
      totalQuestions: questions.length,
      correctCount,
    });
    setConfirming(false);
    navigate(`/results/${attempt.id}`);
  };

  if (loaderState.status === 'loading' || loaderState.status === 'idle') {
    return (
      <div className="card p-6 text-center text-neutral-500 dark:text-neutral-400">
        Loading questions…
      </div>
    );
  }

  if (total === 0 || !current) {
    return (
      <div className="space-y-4">
        <div className="card p-6 text-center">
          <h1 className="text-xl font-bold mb-2">No questions available</h1>
          <p className="text-neutral-600 dark:text-neutral-400">
            We don't have {subject} {exam} questions in the bank yet. Please
            try another subject.
          </p>
          <Link
            to={`/exam/${exam}`}
            className="btn-primary mt-4 inline-flex"
          >
            Pick another subject
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <header className="sticky top-14 z-20 -mx-4 px-4 py-2 bg-white/85 dark:bg-neutral-950/85 backdrop-blur border-b border-neutral-200 dark:border-neutral-800 flex items-center gap-3">
        <div className="min-w-0 flex-1">
          <div className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
            {exam} · {subject}
          </div>
          <div className="text-sm font-semibold">
            Question {index + 1} of {total}
          </div>
        </div>
        <Timer
          durationSeconds={durationSeconds}
          onExpire={handleExpire}
        />
      </header>

      <div className="flex items-center gap-2">
        <div
          className="h-2 flex-1 rounded-full bg-neutral-200 dark:bg-neutral-800 overflow-hidden"
          role="progressbar"
          aria-valuenow={index + 1}
          aria-valuemin={1}
          aria-valuemax={total}
        >
          <div
            className="h-full bg-nigeria-green transition-all"
            style={{ width: `${((index + 1) / total) * 100}%` }}
          />
        </div>
        <span className="text-xs tabular-nums text-neutral-500 dark:text-neutral-400">
          {answered}/{total} answered
        </span>
      </div>

      <div key={current.id}>
        <QuestionCard
          question={current}
          questionNumber={index + 1}
          totalQuestions={total}
          selectedOptionId={answers[current.id] ?? null}
          showCorrect={false}
          onSelect={handleSelect}
        />
      </div>

      <nav
        className="flex items-center gap-2 sticky bottom-0 -mx-4 px-4 py-3 bg-white/90 dark:bg-neutral-950/90 backdrop-blur border-t border-neutral-200 dark:border-neutral-800"
        aria-label="Test navigation"
      >
        <button
          type="button"
          className="btn-secondary"
          onClick={() => setIndex((i) => Math.max(0, i - 1))}
          disabled={index === 0}
        >
          Previous
        </button>
        {index < total - 1 ? (
          <button
            type="button"
            className="btn-primary ml-auto"
            onClick={() => setIndex((i) => Math.min(total - 1, i + 1))}
          >
            Next
          </button>
        ) : (
          <button
            type="button"
            className="btn-primary ml-auto"
            onClick={() => setConfirming(true)}
          >
            Submit
          </button>
        )}
      </nav>

      <details className="card p-4">
        <summary className="cursor-pointer text-sm font-medium select-none">
          Question grid ({answered}/{total} answered)
        </summary>
        <div className="grid grid-cols-8 sm:grid-cols-10 gap-2 mt-3">
          {questions.map((q, i) => {
            const ans = answers[q.id];
            const cls =
              i === index
                ? 'bg-nigeria-green text-white'
                : ans
                ? 'bg-nigeria-green/15 text-nigeria-green dark:text-nigeria-green-light'
                : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300';
            return (
              <button
                key={q.id}
                type="button"
                onClick={() => setIndex(i)}
                className={`h-9 w-9 rounded-lg text-sm font-semibold tabular-nums ${cls}`}
                aria-label={`Jump to question ${i + 1}`}
                aria-current={i === index ? 'true' : undefined}
              >
                {i + 1}
              </button>
            );
          })}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            className="btn-primary"
            disabled={!allAnswered}
            onClick={() => setConfirming(true)}
          >
            {allAnswered
              ? 'Submit test'
              : `Answer all ${total - answered} remaining`}
          </button>
          {!allAnswered ? (
            <button
              type="button"
              className="btn-ghost"
              onClick={() => setConfirming(true)}
            >
              Submit anyway
            </button>
          ) : null}
        </div>
      </details>

      {confirming ? (
        <ConfirmDialog
          title="Submit your test?"
          description={
            <>
              You answered <strong>{answered}</strong> of {total} questions.
              {answered < total ? (
                <>
                  {' '}
                  {total - answered}{' '}
                  {total - answered === 1 ? 'question is' : 'questions are'}{' '}
                  unanswered and will be marked wrong.
                </>
              ) : (
                <> Great — everything answered.</>
              )}
            </>
          }
          confirmLabel="Submit"
          cancelLabel="Keep going"
          onCancel={() => setConfirming(false)}
          onConfirm={submit}
        />
      ) : null}
    </div>
  );
}
