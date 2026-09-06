import { Link, useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import {
  countQuestionsForSubject,
  countQuestionsForYear,
  getState,
  listYears,
  subscribe,
} from '../data/loader';
import type { ExamType } from '../types/exam';

const KNOWN: ExamType[] = ['BECE', 'NECO', 'JAMB', 'WAEC'];

export function YearPicker() {
  const { examId, subjectId } = useParams<{ examId: string; subjectId: string }>();
  const exam = (KNOWN.includes(examId as ExamType) ? examId : 'BECE') as ExamType;
  const subject = subjectId ? decodeURIComponent(subjectId) : '';

  const [, setTick] = useState(0);
  useEffect(() => subscribe(() => setTick((t) => t + 1)), []);

  const years = listYears(exam, subject);
  const total = countQuestionsForSubject(exam, subject);
  const state = getState();

  return (
    <div className="space-y-6">
      <nav className="text-sm text-neutral-500 dark:text-neutral-400" aria-label="Breadcrumb">
        <Link to="/" className="hover:underline">Home</Link>
        <span className="mx-2">/</span>
        <Link to={`/exam/${exam}`} className="hover:underline">{exam}</Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700 dark:text-neutral-200 font-medium">{subject}</span>
      </nav>

      <header>
        <h1 className="text-2xl font-bold">{subject} · pick a year</h1>
        <p className="text-neutral-600 dark:text-neutral-400 mt-1">
          Practice questions from a specific exam year, or mix all years for variety.
        </p>
      </header>

      {state.status === 'loading' || state.status === 'idle' ? (
        <div className="card p-5 text-center text-neutral-500 dark:text-neutral-400 animate-pulse">
          Loading years…
        </div>
      ) : null}

      {state.status === 'ready' && years.length === 0 ? (
        <div className="card p-5 text-center text-neutral-500 dark:text-neutral-400">
          No {subject} questions in the bank yet — try another subject.
          <div className="mt-4">
            <Link to={`/exam/${exam}`} className="btn-primary inline-flex">
              Pick another subject
            </Link>
          </div>
        </div>
      ) : null}

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {years.map((year) => {
          const count = countQuestionsForYear(exam, subject, year);
          return (
            <Link
              key={year}
              to={`/practice/${exam}/${encodeURIComponent(subject)}/${year}`}
              className="card p-4 hover:border-nigeria-green hover:shadow-md transition"
            >
              <div className="font-semibold text-lg tabular-nums">{year}</div>
              <div className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
                {count} {count === 1 ? 'question' : 'questions'}
              </div>
            </Link>
          );
        })}
        {years.length > 1 ? (
          <Link
            to={`/practice/${exam}/${encodeURIComponent(subject)}`}
            className="card p-4 hover:border-nigeria-green hover:shadow-md transition border-dashed"
          >
            <div className="font-semibold text-lg">All years</div>
            <div className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
              Mixed set · {total} questions
            </div>
          </Link>
        ) : null}
      </div>
    </div>
  );
}
