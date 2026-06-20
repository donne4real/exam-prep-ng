import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  getQuestions,
  loadQuestions,
  resetForTests,
  type LoaderState,
} from './loader';
import type { QuestionsFile, Question } from '../types/exam';

function makeFile(overrides: Partial<QuestionsFile> = {}): QuestionsFile {
  return {
    version: 1,
    exams: [
      {
        id: 'BECE',
        name: 'BECE',
        fullName: 'Basic Education Certificate Examination',
        description: '',
        durationMinutes: 60,
      },
    ],
    subjects: [],
    questions: [],
    ...overrides,
  };
}

function makeQuestion(overrides: Partial<Question> = {}): Question {
  return {
    id: Math.random().toString(36).slice(2),
    exam: 'BECE',
    subject: 'Math',
    year: 2020,
    prompt: 'Sample?',
    options: [
      { id: 'a', text: 'A' },
      { id: 'b', text: 'B' },
    ],
    correctOptionId: 'a',
    ...overrides,
  };
}

describe('loader: loadQuestions', () => {
  beforeEach(() => {
    resetForTests();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns empty state when fetch 404s', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('not found', { status: 404 })),
    );
    const state: LoaderState = await loadQuestions(true);
    expect(state.status).toBe('empty');
    expect(state.error).toContain('404');
  });

  it('returns empty state when JSON is malformed', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('not json', { status: 200 })),
    );
    const state = await loadQuestions(true);
    expect(state.status).toBe('empty');
  });

  it('returns ready when questions present', async () => {
    const file = makeFile({ questions: [makeQuestion()] });
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify(file), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        }),
      ),
    );
    const state = await loadQuestions(true);
    expect(state.status).toBe('ready');
    expect(state.file?.questions).toHaveLength(1);
  });
});

describe('loader: getQuestions pooling', () => {
  beforeEach(() => {
    resetForTests();
    vi.restoreAllMocks();
  });

  it('returns the exact year when it has >= 30 questions', async () => {
    const questions = Array.from({ length: 40 }, () =>
      makeQuestion({ year: 2020, subject: 'Math' }),
    );
    const other = Array.from({ length: 50 }, () =>
      makeQuestion({ year: 2019, subject: 'Math' }),
    );
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(
          JSON.stringify(makeFile({ questions: [...questions, ...other] })),
          { status: 200, headers: { 'content-type': 'application/json' } },
        ),
      ),
    );
    await loadQuestions(true);
    const result = getQuestions('BECE', 'Math', 2020);
    expect(result).toHaveLength(40);
    expect(result.every((q) => q.year === 2020)).toBe(true);
  });

  it('pools across years when exact year has < 30 questions', async () => {
    const exact = Array.from({ length: 5 }, () =>
      makeQuestion({ year: 2020, subject: 'Math' }),
    );
    const other = Array.from({ length: 50 }, () =>
      makeQuestion({ year: 2019, subject: 'Math' }),
    );
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response(
            JSON.stringify(makeFile({ questions: [...exact, ...other] })),
            { status: 200, headers: { 'content-type': 'application/json' } },
          ),
      ),
    );
    await loadQuestions(true);
    const result = getQuestions('BECE', 'Math', 2020);
    expect(result.length).toBeGreaterThanOrEqual(50);
  });

  it('returns exact (possibly empty) when no other-year data exists', async () => {
    const exact = Array.from({ length: 5 }, () =>
      makeQuestion({ year: 2020, subject: 'Math' }),
    );
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response(JSON.stringify(makeFile({ questions: exact })), {
            status: 200,
            headers: { 'content-type': 'application/json' },
          }),
      ),
    );
    await loadQuestions(true);
    const result = getQuestions('BECE', 'Math', 2020);
    expect(result).toHaveLength(5);
  });
});
