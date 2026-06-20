import { Link, useParams } from 'react-router-dom';
import { useMemo } from 'react';
import { listQuestionsForSubject, listSubjects } from '../data/loader';
import { useLoaderState } from '../lib/useLoaderState';
import type { ExamType } from '../types/exam';
import { useSettingsStore } from '../store/settings';
import { useProgressStore } from '../store/progress';

const KNOWN: ExamType[] = ['BECE', 'NECO', 'JAMB', 'WAEC'];

export function Subjects() {
  const { examId } = useParams<{ examId: string }>();
  const exam = (KNOWN.includes(examId as ExamType) ? examId : 'BECE') as ExamType;

  const loaderState = useLoaderState();
  const setLast = useSettingsStore((s) => s.setLast);
  const attempts = useProgressStore((s) => s.attempts);

  const subjects = useMemo(
    () => listSubjects(exam),
    [exam, loaderState.status, loaderState.file],
  );

  const counts = useMemo(() => {
    const map = new Map<string, number>();
    for (const a of attempts) {
      if (a.exam !== exam) continue;
      map.set(a.subject, (map.get(a.subject) ?? 0) + 1);
    }
    return map;
  }, [attempts, exam]);

  return (
    <div className="space-y-6">
      <nav
        className="text-sm text-neutral-500 dark:text-neutral-400"
        aria-label="Breadcrumb"
      >
        <Link to="/" className="hover:underline">
          Home
        </Link>
        <span className="mx-2">/</span>
        <span className="text-neutral-700 dark:text-neutral-200 font-medium">
          {exam}
        </span>
      </nav>

      <header>
        <h1 className="text-2xl font-bold">{exam} subjects</h1>
        <p className="text-neutral-600 dark:text-neutral-400 mt-1">
          Pick a subject to start a practice test.
        </p>
      </header>

      {loaderState.status === 'empty' || loaderState.status === 'error' ? (
        <div className="card p-5 text-sm text-neutral-600 dark:text-neutral-400">
          Subject list will appear here once the question bank is loaded.
        </div>
      ) : null}

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {subjects.map((subject) => {
          const attempted = counts.get(subject.name) ?? 0;
          const questionCount = listQuestionsForSubject(
            exam,
            subject.name,
          ).length;
          return (
            <Link
              key={subject.id}
              to={`/practice/${exam}/${encodeURIComponent(subject.name)}`}
              onClick={() => setLast(exam, subject.name)}
              className="card p-4 hover:border-nigeria-green hover:shadow-md transition"
            >
              <div className="flex items-center justify-between">
                <div className="font-semibold leading-tight">{subject.name}</div>
                {attempted > 0 ? (
                  <span className="pill bg-nigeria-green/10 text-nigeria-green dark:text-nigeria-green-light">
                    {attempted} {attempted === 1 ? 'try' : 'tries'}
                  </span>
                ) : null}
              </div>
              <div className="mt-2 text-xs text-neutral-500 dark:text-neutral-400 flex items-center gap-2">
                <span className="pill bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300">
                  {questionCount} {questionCount === 1 ? 'question' : 'questions'}
                </span>
                {subject.topics.length > 0 ? (
                  <span className="line-clamp-1">
                    {subject.topics.slice(0, 3).join(' · ')}
                  </span>
                ) : null}
              </div>
            </Link>
          );
        })}
      </div>

      {subjects.length === 0 ? (
        <div className="card p-5 text-center text-neutral-500 dark:text-neutral-400">
          No subjects available yet.
        </div>
      ) : null}
    </div>
  );
}
