// Core data types for Nigerian exam prep content.

export type ExamType = 'BECE' | 'NECO' | 'JAMB' | 'WAEC';

export interface ExamMeta {
  id: ExamType;
  name: string;
  fullName: string;
  description: string;
  durationMinutes: number;
}

export interface SubjectMeta {
  id: string;
  exam: ExamType;
  name: string;
  topics: string[];
}

/** Subject entry in the lightweight data index (no questions inside). */
export interface SubjectIndex extends SubjectMeta {
  /** Total questions in this subject's bank file. */
  questionCount: number;
  /** Exam years actually present in the bank, newest first. */
  years: number[];
  /** Questions per year, key = year as string. */
  yearCounts: Record<string, number>;
  /** Bank file path relative to the data directory. */
  file: string;
}

export interface BankIndex {
  version: number;
  generatedAt?: string;
  exams: ExamMeta[];
  subjects: SubjectIndex[];
}

/** A per-subject bank file: data/<file> */
export interface BankFile {
  subject: { id: string; exam: ExamType; name: string };
  questions: Question[];
}

export interface QuestionOption {
  /** Stable id (e.g. "a", "b", "c", "d"). */
  id: string;
  text: string;
}

export interface Question {
  id: string;
  exam: ExamType;
  subject: string;
  year: number;
  topic?: string;
  prompt: string;
  options: QuestionOption[];
  /** id of the correct option (e.g. "b"). */
  correctOptionId: string;
  explanation?: string;
}

export interface QuestionsFile {
  version: number;
  generatedAt?: string;
  exams: ExamMeta[];
  subjects: SubjectMeta[];
  questions: Question[];
}

export interface AttemptAnswer {
  questionId: string;
  selectedOptionId: string | null;
  /** Whether the answer was correct at submission time. */
  correct: boolean;
  topic?: string;
  subject?: string;
}

export interface Attempt {
  id: string;
  exam: ExamType;
  subject: string;
  year: number;
  startedAt: number;
  submittedAt: number;
  durationSeconds: number;
  answers: AttemptAnswer[];
  totalQuestions: number;
  correctCount: number;
  percentage: number;
  gradeBand: 'A' | 'B' | 'C' | 'D' | 'F';
}
