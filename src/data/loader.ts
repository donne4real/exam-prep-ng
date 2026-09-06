// Loads the lightweight data index and per-subject question banks on demand.
//
// The old design fetched one monolithic questions.json (~6MB) before the app
// was usable. Now a small index.json (~5KB) drives Home/Subjects/YearPicker,
// and a subject's questions (~100-300KB) are only downloaded when the user
// actually opens that subject — then cached by the service worker for
// offline use.

import type {
  BankFile,
  BankIndex,
  ExamMeta,
  ExamType,
  Question,
  SubjectIndex,
} from '../types/exam';

export type BankStatus = 'idle' | 'loading' | 'ready' | 'error';

interface LoaderState {
  status: 'idle' | 'loading' | 'ready' | 'error' | 'empty';
  index: BankIndex | null;
  error: string | null;
}

let cache: LoaderState = { status: 'idle', index: null, error: null };
const listeners = new Set<() => void>();

const banks = new Map<string, { status: BankStatus; questions: Question[] }>();

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

const EMPTY_INDEX: BankIndex = {
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
};

export async function loadIndex(force = false): Promise<LoaderState> {
  if (!force && (cache.status === 'ready' || cache.status === 'empty')) return cache;

  cache = { ...cache, status: 'loading', error: null };
  notify();

  try {
    const res = await fetch(`${import.meta.env.BASE_URL}data/index.json`, {
      cache: force ? 'no-store' : 'default',
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const json = (await res.json()) as Partial<BankIndex>;
    if (!json || !Array.isArray(json.exams) || !Array.isArray(json.subjects)) {
      cache = { status: 'empty', index: EMPTY_INDEX, error: null };
      notify();
      return cache;
    }
    const index: BankIndex = {
      version: json.version ?? 1,
      generatedAt: json.generatedAt,
      exams: json.exams as ExamMeta[],
      subjects: json.subjects as SubjectIndex[],
    };
    const isEmpty = index.subjects.length === 0;
    cache = { status: isEmpty ? 'empty' : 'ready', index, error: null };
    notify();
    return cache;
  } catch (err) {
    // Network failure or 404 — assume empty so the UI can show a friendly state.
    cache = {
      status: 'empty',
      index: EMPTY_INDEX,
      error: err instanceof Error ? err.message : 'Unknown error',
    };
    notify();
    return cache;
  }
}

function findSubjectIndex(exam: ExamType, subject: string): SubjectIndex | undefined {
  return (cache.index?.subjects ?? []).find(
    (s) => s.exam === exam && s.name === subject,
  );
}

/** Fetch (once) and cache the questions for one subject. */
export async function ensureBank(
  exam: ExamType,
  subject: string,
): Promise<Question[]> {
  await loadIndex();
  const meta = findSubjectIndex(exam, subject);
  if (!meta) return [];

  const existing = banks.get(meta.id);
  if (existing && (existing.status === 'ready' || existing.status === 'loading')) {
    return existing.questions;
  }

  banks.set(meta.id, { status: 'loading', questions: [] });
  notify();
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}data/${meta.file}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = (await res.json()) as Partial<BankFile>;
    const questions = Array.isArray(json.questions) ? (json.questions as Question[]) : [];
    banks.set(meta.id, { status: 'ready', questions });
    notify();
    return questions;
  } catch (err) {
    cache = {
      ...cache,
      error: err instanceof Error ? err.message : 'Unknown error',
    };
    banks.set(meta.id, { status: 'error', questions: [] });
    notify();
    return [];
  }
}

/** Sync snapshot of a subject's questions ([] until ensureBank resolves). */
export function getBank(exam: ExamType, subject: string): Question[] {
  const meta = findSubjectIndex(exam, subject);
  if (!meta) return [];
  return banks.get(meta.id)?.questions ?? [];
}

export function getBankStatus(exam: ExamType, subject: string): BankStatus {
  const meta = findSubjectIndex(exam, subject);
  if (!meta) return 'idle';
  return banks.get(meta.id)?.status ?? 'idle';
}

export function listExams(): ExamMeta[] {
  return cache.index?.exams ?? EMPTY_INDEX.exams;
}

export function listSubjects(exam: ExamType): SubjectIndex[] {
  return (cache.index?.subjects ?? []).filter((s) => s.exam === exam);
}

/**
 * Years with questions in the bank for this subject, newest first.
 * Unlike the old scaffold, this only reports years that actually exist.
 */
export function listYears(exam: ExamType, subject: string): number[] {
  return findSubjectIndex(exam, subject)?.years ?? [];
}

export function countQuestionsForSubject(exam: ExamType, subject: string): number {
  return findSubjectIndex(exam, subject)?.questionCount ?? 0;
}

export function countQuestionsForYear(
  exam: ExamType,
  subject: string,
  year: number,
): number {
  return findSubjectIndex(exam, subject)?.yearCounts[String(year)] ?? 0;
}

export function getExamMeta(exam: ExamType): ExamMeta | undefined {
  return listExams().find((e) => e.id === exam);
}
