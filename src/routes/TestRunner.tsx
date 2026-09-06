import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ensureBank,
  getBank,
  getBankStatus,
  getExamMeta,
  getState,
  subscribe,
} from '../data/loader';
import type { AttemptAnswer, ExamType, Question } from '../types/exam';
import { QuestionCard } from '../components/QuestionCard';
import { Timer } from '../components/Timer';
import { useProgressStore } from '../store/progress';

const KNOWN: ExamType[] = ['BECE', 'NECO', 'JAMB', 'WAEC'];
// Below this many questions for a chosen year, fall back to a mixed set.
const MIN_YEAR_QUESTIONS = 10;
const MAX_SESSION_QUESTIONS = 40;

export function TestRunner() {
  const { examId, subjectId, year: yearParam } = useParams<{
    examId: string;
    subjectId: string;
    year?: string;
  }>();
  const exam = (KNOWN.includes(examId as ExamType) ? examId : 'BECE') as ExamType;
  const subject = subjectId ? decodeURIComponent(subjectId) : '';
  const selectedYear = yearParam && /^\d{4}$/.test(yearParam) ? Number(yearParam) : null;

  const navigate = useNavigate();
  const recordAttempt = useProgressStore((s) => s.recordAttempt);

  const [tick, setTick] = useState(0);
  useEffect(() => subscribe(() => setTick((t) => t + 1)), []);
  useEffect(() => {
    void ensureBank(exam, subject);
  }, [exam, subject]);

  const bankStatus = getBankStatus(exam, subject);

  // Pull the subject's questions, filter to the chosen year when there are
  // enough of them, and shuffle for a different test each time.
  const { questions, pooledFromOtherYears } = useMemo(() => {
    const all = getBank(exam, subject);
    let pool = all;
    let pooledFromOtherYears = false;
    if (selectedYear != null) {
      const exact = all.filter((q) => q.year === selectedYear);
      if (exact.length >= MIN_YEAR_QUESTIONS) {
        pool = exact;
      } else if (all.length > exact.length) {
        pooledFromOtherYears = true;
      }
    }
    // Shuffle (Fisher-Yates)
    const shuffled = [...pool];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    // Cap the session length to keep the test manageable.
    return {
      questions: shuffled.slice(0, Math.min(MAX_SESSION_QUESTIONS, shuffled.length)),
      pooledFromOtherYears,
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exam, subject, selectedYear, tick, bankStatus]);

  const meta = getExamMeta(exam);
  const durationSeconds = (meta?.durationMinutes ?? 30) * 60;

  const [startedAt] = useState(() => Date.now());
  const [answers, setAnswers] = useState<Record<string, string | null>>({});
  const [index, setIndex] = useState(0);
  const [submitted, setSubmitted] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const submittedRef = useRef(false);

  const total = questions.length;
  const current: Question | undefined = questions[index];
  const answered = Object.values(answers).filter(Boolean).length;
  const allAnswered = answered === total && total > 0;

  // Auto-submit when time runs out.
  const handleExpire = () => {
    if (submittedRef.current) return;
    submittedRef.current = true;
    setSubmitted(true);
  };

  const handleSelect = (optionId: string) => {
    if (submitted) return;
    setAnswers((prev) => ({ ...prev, [current!.id]: optionId }));
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
      };
    });
    const correctCount = attemptAnswers.filter((a) => a.correct).length;
    const submittedAt = Date.now();
    const attempt = recordAttempt({
      exam,
      subject,
      year: selectedYear ?? 0,
      startedAt,
      submittedAt,
      durationSeconds: Math.min(durationSeconds, Math.round((submittedAt - startedAt) / 1000)),
      answers: attemptAnswers,
      totalQuestions: questions.length,
      correctCount,
      questions,
    });
    setSubmitted(true);
    navigate(`/results/${attempt.id}`);
  };

  const loaderState = getState();
  if (
    loaderState.status === 'loading' ||
    loaderState.status === 'idle' ||
    bankStatus === 'loading' ||
    bankStatus === 'idle'
  ) {
    return (
      <div className="card p-6 text-center text-neutral-500 dark:text-neutral-400">
        Loading questions…
      </div>
    );
  }

  if (total === 0) {
    return (
      <div className="space-y-4">
        <div className="card p-6 text-center">
          <h1 className="text-xl font-bold mb-2">No questions available</h1>
          <p className="text-neutral-600 dark:text-neutral-400">
            We don't have {subject} {exam} questions in the bank yet. Please try another subject.
          </p>
          <Link to={`/exam/${exam}`} className="btn-primary mt-4 inline-flex">
            Pick another subject
          </Link>
        </div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="card p-6 text-center text-neutral-500 dark:text-neutral-400">
        Submitting…
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {pooledFromOtherYears ? (
        <div className="card p-3 border-l-4 border-l-amber-400 bg-amber-50 dark:bg-amber-950/30 text-sm text-amber-800 dark:text-amber-300">
          We only have {getBank(exam, subject).filter((q) => q.year === selectedYear).length}{' '}
          {selectedYear} question{getBank(exam, subject).filter((q) => q.year === selectedYear).length === 1 ? '' : 's'} so
          far, so this session mixes in questions from other years.
        </div>
      ) : null}
      <header className="sticky top-14 z-20 -mx-4 px-4 py-2 bg-white/85 dark:bg-neutral-950/85 backdrop-blur border-b border-neutral-200 dark:border-neutral-800 flex items-center gap-3">
        <div className="min-w-0 flex-1">
          <div className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
            {exam} · {subject}
            {selectedYear != null ? ` · ${selectedYear}` : ' · All years'}
          </div>
          <div className="text-sm font-semibold">
            Question {index + 1} of {total}
          </div>
        </div>
        <Timer
          durationSeconds={durationSeconds}
          onExpire={handleExpire}
          onTick={(remaining) => {
            if (remaining === 0 && !submittedRef.current) {
              submittedRef.current = true;
              submit();
            }
          }}
        />
      </header>

      <div className="flex items-center gap-2">
        <div className="h-2 flex-1 rounded-full bg-neutral-200 dark:bg-neutral-800 overflow-hidden">
          <div
            className="h-full bg-nigeria-green transition-all"
            style={{ width: `${((index + 1) / total) * 100}%` }}
          />
        </div>
        <span className="text-xs tabular-nums text-neutral-500 dark:text-neutral-400">
          {answered}/{total} answered
        </span>
      </div>

      <QuestionCard
        question={current}
        questionNumber={index + 1}
        totalQuestions={total}
        selectedOptionId={answers[current.id] ?? null}
        showCorrect={false}
        onSelect={handleSelect}
      />

      <nav className="flex items-center gap-2 sticky bottom-0 -mx-4 px-4 py-3 bg-white/90 dark:bg-neutral-950/90 backdrop-blur border-t border-neutral-200 dark:border-neutral-800" aria-label="Test navigation">
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
            const cls = i === index
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
            {allAnswered ? 'Submit test' : `Answer all ${total - answered} remaining`}
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
          total={total}
          answered={answered}
          onCancel={() => setConfirming(false)}
          onConfirm={submit}
        />
      ) : null}
    </div>
  );
}

function ConfirmDialog({
  total,
  answered,
  onCancel,
  onConfirm,
}: {
  total: number;
  answered: number;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const unanswered = total - answered;
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
      className="fixed inset-0 z-50 bg-black/50 flex items-end sm:items-center justify-center p-4"
    >
      <div className="card w-full max-w-md p-5 animate-slide-up">
        <h2 id="confirm-title" className="text-lg font-bold">
          Submit your test?
        </h2>
        <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
          You answered <strong>{answered}</strong> of {total} questions.
          {unanswered > 0 ? (
            <> {unanswered} {unanswered === 1 ? 'question is' : 'questions are'} unanswered and will be marked wrong.</>
          ) : (
            <> Great — everything answered.</>
          )}
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" className="btn-ghost" onClick={onCancel}>
            Keep going
          </button>
          <button type="button" className="btn-primary" onClick={onConfirm} autoFocus>
            Submit
          </button>
        </div>
      </div>
    </div>
  );
}
