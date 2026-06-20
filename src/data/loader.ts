// Loads questions.json from the public folder and exposes typed accessors.
// Handles the empty / loading state gracefully while the content agent
// finishes generating the data file.

import type {
  ExamMeta,
  ExamType,
  Question,
  QuestionsFile,
  SubjectMeta,
} from '../types/exam';

export interface LoaderState {
  status: 'idle' | 'loading' | 'ready' | 'error' | 'empty';
  file: QuestionsFile | null;
  error: string | null;
}

let cache: LoaderState = { status: 'idle', file: null, error: null };
const listeners = new Set<() => void>();

function notify(): void {
  for (const cb of listeners) cb();
}

export function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

export function getState(): LoaderState {
  return cache;
}

const EMPTY_FILE: QuestionsFile = {
  version: 0,
  exams: [
    {
      id: 'BECE',
      name: 'BECE',
      fullName: 'Basic Education Certificate Examination',
      description: 'Junior secondary school leaving exam.',
      durationMinutes: 60,
    },
    {
      id: 'NECO',
      name: 'NECO',
      fullName: 'National Examinations Council (SSCE)',
      description: 'Senior secondary school leaving exam.',
      durationMinutes: 60,
    },
    {
      id: 'JAMB',
      name: 'JAMB',
      fullName: 'Joint Admissions and Matriculation Board (UTME)',
      description: 'University entrance examination.',
      durationMinutes: 40,
    },
  ],
  subjects: [],
  questions: [],
};

export async function loadQuestions(force = false): Promise<LoaderState> {
  if (!force && cache.status === 'ready') return cache;
  if (!force && cache.status === 'empty') return cache;

  cache = { ...cache, status: 'loading', error: null };
  notify();

  try {
    const res = await fetch(`${import.meta.env.BASE_URL}data/questions.json`, {
      cache: force ? 'no-store' : 'default',
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const json = (await res.json()) as Partial<QuestionsFile>;
    if (!json || !Array.isArray(json.exams) || !Array.isArray(json.questions)) {
      cache = {
        status: 'empty',
        file: { ...EMPTY_FILE, subjects: json?.subjects ?? [] },
        error: null,
      };
      notify();
      return cache;
    }
    const file: QuestionsFile = {
      version: json.version ?? 1,
      generatedAt: json.generatedAt,
      exams: json.exams as ExamMeta[],
      subjects: (json.subjects ?? []) as SubjectMeta[],
      questions: json.questions as Question[],
    };
    const isEmpty =
      file.questions.length === 0 && file.subjects.length === 0;
    cache = {
      status: isEmpty ? 'empty' : 'ready',
      file,
      error: null,
    };
    notify();
    return cache;
  } catch (err) {
    // Network failure or 404 — assume empty so the UI can show a friendly state.
    cache = {
      status: 'empty',
      file: EMPTY_FILE,
      error: err instanceof Error ? err.message : 'Unknown error',
    };
    notify();
    return cache;
  }
}

export function listExams(): ExamMeta[] {
  return cache.file?.exams ?? EMPTY_FILE.exams;
}

export function listSubjects(exam: ExamType): SubjectMeta[] {
  const all = cache.file?.subjects ?? [];
  if (all.length > 0) {
    return all.filter((s) => s.exam === exam);
  }
  // Fallback: infer subjects from questions when subjects list is missing.
  const fromQuestions = new Set<string>();
  for (const q of cache.file?.questions ?? []) {
    if (q.exam === exam) fromQuestions.add(q.subject);
  }
  return Array.from(fromQuestions).sort().map((name) => ({
    id: `${exam.toLowerCase()}-${name.toLowerCase().replace(/\s+/g, '-')}`,
    exam,
    name,
    topics: [],
  }));
}

export function listYears(exam: ExamType, subject: string): number[] {
  const set = new Set<number>();
  for (const q of cache.file?.questions ?? []) {
    if (q.exam === exam && q.subject === subject) set.add(q.year);
  }
  if (set.size === 0) {
    // No data — provide the year scaffold so the UI still renders meaningfully.
    const start = 2015;
    const end = 2024;
    for (let y = start; y <= end; y++) set.add(y);
  }
  return Array.from(set).sort((a, b) => b - a);
}

export function countQuestions(
  exam: ExamType,
  subject: string,
  year: number,
): number {
  return (cache.file?.questions ?? []).filter(
    (q) => q.exam === exam && q.subject === subject && q.year === year,
  ).length;
}

export function countEffectiveQuestions(
  exam: ExamType,
  subject: string,
  year: number,
): { count: number; pooled: boolean } {
  const exact = (cache.file?.questions ?? []).filter(
    (q) => q.exam === exam && q.subject === subject && q.year === year,
  );
  if (exact.length >= 30) {
    return { count: exact.length, pooled: false };
  }
  const all = (cache.file?.questions ?? []).filter(
    (q) => q.exam === exam && q.subject === subject,
  );
  if (all.length > exact.length) {
    return { count: all.length, pooled: true };
  }
  return { count: exact.length, pooled: false };
}

export function getQuestions(
  exam: ExamType,
  subject: string,
  year: number,
): Question[] {
  // First try the exact year
  const exact = (cache.file?.questions ?? []).filter(
    (q) => q.exam === exam && q.subject === subject && q.year === year,
  );
  if (exact.length >= 30) {
    return exact;
  }
  // Fall back to all questions for this exam + subject (any year) for a fuller test
  const all = (cache.file?.questions ?? []).filter(
    (q) => q.exam === exam && q.subject === subject,
  );
  if (all.length > exact.length) {
    return all;
  }
  return exact;
}

export function listQuestionsForSubject(
  exam: ExamType,
  subject: string,
): Question[] {
  return (cache.file?.questions ?? []).filter(
    (q) => q.exam === exam && q.subject === subject,
  );
}

export function getExamMeta(exam: ExamType): ExamMeta | undefined {
  return listExams().find((e) => e.id === exam);
}

// Test-only helper. Not exported in the public API.
export function resetForTests(): void {
  cache = { status: 'idle', file: null, error: null };
  listeners.clear();
}
