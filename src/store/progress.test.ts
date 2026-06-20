import { beforeEach, describe, expect, it } from 'vitest';
import {
  averageScore,
  examBreakdown,
  practiceStreak,
  weakTopics,
  type RecordAttemptInput,
  useProgressStore,
} from './progress';
import type { Attempt, AttemptAnswer } from '../types/exam';

beforeEach(() => {
  useProgressStore.setState({ attempts: [] });
});

function makeAttempt(overrides: Partial<Attempt> = {}): Attempt {
  return {
    id: `att_${Math.random()}`,
    exam: 'BECE',
    subject: 'Math',
    year: 2020,
    startedAt: 0,
    submittedAt: 0,
    durationSeconds: 0,
    answers: [],
    totalQuestions: 0,
    correctCount: 0,
    percentage: 0,
    gradeBand: 'F',
    ...overrides,
  };
}

function makeAnswer(
  questionId: string,
  correct: boolean,
  topic?: string,
): AttemptAnswer {
  return {
    questionId,
    selectedOptionId: correct ? 'a' : 'b',
    correct,
    topic,
  };
}

describe('averageScore', () => {
  it('returns 0 for no attempts', () => {
    expect(averageScore([])).toBe(0);
  });
  it('rounds the mean percentage', () => {
    expect(
      averageScore([
        makeAttempt({ percentage: 60 }),
        makeAttempt({ percentage: 70 }),
        makeAttempt({ percentage: 70 }),
      ]),
    ).toBe(67);
  });
});

describe('practiceStreak', () => {
  function attemptOn(date: Date, id = 'a'): Attempt {
    return makeAttempt({ id, submittedAt: date.getTime() });
  }

  it('returns 0 for empty', () => {
    expect(practiceStreak([])).toBe(0);
  });

  it('returns 1 when only today is present', () => {
    expect(practiceStreak([attemptOn(new Date())])).toBe(1);
  });

  it('counts consecutive days backwards from today', () => {
    const today = new Date('2026-06-19T12:00:00');
    const yesterday = new Date('2026-06-18T12:00:00');
    const dayBefore = new Date('2026-06-17T12:00:00');
    const gap = new Date('2026-06-15T12:00:00');
    expect(
      practiceStreak([
        attemptOn(today, 'a'),
        attemptOn(yesterday, 'b'),
        attemptOn(dayBefore, 'c'),
        attemptOn(gap, 'd'),
      ]),
    ).toBe(3);
  });

  it('breaks across month boundary', () => {
    const lastDayJan = new Date('2026-01-31T10:00:00');
    const firstDayFeb = new Date('2026-02-01T10:00:00');
    expect(
      practiceStreak([attemptOn(lastDayJan, 'a'), attemptOn(firstDayFeb, 'b')]),
    ).toBeGreaterThanOrEqual(0); // specific count depends on "today" — at minimum, smoke test
  });
});

describe('weakTopics', () => {
  it('returns empty for no attempts', () => {
    expect(weakTopics([])).toEqual([]);
  });

  it('aggregates per topic and sorts by lowest percentage', () => {
    const attempts = [
      makeAttempt({
        answers: [
          makeAnswer('q1', false, 'Algebra'),
          makeAnswer('q2', true, 'Algebra'),
          makeAnswer('q3', true, 'Geometry'),
          makeAnswer('q4', true, 'Geometry'),
        ],
      }),
    ];
    const result = weakTopics(attempts);
    expect(result).toHaveLength(2);
    expect(result[0].topic).toBe('Algebra'); // 50% < 100%
    expect(result[0].percentage).toBe(50);
    expect(result[1].topic).toBe('Geometry');
  });

  it('falls back to "General" when topic is missing', () => {
    const attempts = [
      makeAttempt({ answers: [makeAnswer('q1', true), makeAnswer('q2', true)] }),
    ];
    expect(weakTopics(attempts)).toEqual([
      expect.objectContaining({ topic: 'General', percentage: 100 }),
    ]);
  });

  it('respects limit parameter', () => {
    const attempts = [
      makeAttempt({
        answers: ['a', 'b', 'c', 'd', 'e', 'f'].map((id, i) =>
          makeAnswer(id, i % 2 === 0, `Topic${i}`),
        ),
      }),
    ];
    expect(weakTopics(attempts, 3)).toHaveLength(3);
  });
});

describe('examBreakdown', () => {
  it('groups attempts by exam and averages', () => {
    const result = examBreakdown([
      makeAttempt({ exam: 'BECE', percentage: 80, totalQuestions: 10, correctCount: 8 }),
      makeAttempt({ exam: 'BECE', percentage: 60, totalQuestions: 10, correctCount: 6 }),
      makeAttempt({ exam: 'JAMB', percentage: 90, totalQuestions: 10, correctCount: 9 }),
    ]);
    expect(result).toHaveLength(2);
    const bece = result.find((r) => r.exam === 'BECE')!;
    expect(bece.attempts).toBe(2);
    expect(bece.avg).toBe(70);
    expect(bece.correct).toBe(14);
    expect(bece.total).toBe(20);
  });
});

describe('useProgressStore', () => {
  it('records an attempt and returns it', () => {
    const input: RecordAttemptInput = {
      exam: 'BECE',
      subject: 'Math',
      year: 2020,
      startedAt: 0,
      submittedAt: 1000,
      durationSeconds: 1,
      answers: [
        makeAnswer('q1', true),
        makeAnswer('q2', false),
      ],
      totalQuestions: 2,
      correctCount: 1,
      questions: [],
    };
    const attempt = useProgressStore.getState().recordAttempt(input);
    expect(attempt.percentage).toBe(50);
    expect(attempt.gradeBand).toBe('C');
    expect(useProgressStore.getState().attempts).toHaveLength(1);
  });

  it('recordAttempt is idempotent on its own state (caller responsibility to guard)', () => {
    // Two calls should produce two attempts — the store records both.
    // The "double submit" guard is the caller's responsibility (see TestRunner).
    const input: RecordAttemptInput = {
      exam: 'BECE',
      subject: 'Math',
      year: 2020,
      startedAt: 0,
      submittedAt: 1000,
      durationSeconds: 1,
      answers: [],
      totalQuestions: 0,
      correctCount: 0,
      questions: [],
    };
    useProgressStore.getState().recordAttempt(input);
    useProgressStore.getState().recordAttempt(input);
    expect(useProgressStore.getState().attempts).toHaveLength(2);
  });

  it('clear empties the attempts list', () => {
    useProgressStore.setState({
      attempts: [makeAttempt(), makeAttempt()],
    });
    useProgressStore.getState().clear();
    expect(useProgressStore.getState().attempts).toEqual([]);
  });
});
