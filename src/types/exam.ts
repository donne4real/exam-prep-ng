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
  /**
   * Provenance: 'real' = past exam question (the default if omitted),
   * 'generated' = synthesized for practice by scripts/generate-questions.mjs.
   * The UI surfaces this so students can distinguish real past questions
   * from practice items.
   */
  source?: 'real' | 'generated';
  generatedAt?: string;
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
  /** Snapshotted at submit time so it survives question-bank changes. */
  source?: 'real' | 'generated';
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
