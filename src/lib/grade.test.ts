import { describe, expect, it } from 'vitest';
import { gradeFor, gradeColor, scoreColor, formatDuration } from './grade';

describe('gradeFor', () => {
  it('returns A for 75% and above', () => {
    expect(gradeFor(75)).toBe('A');
    expect(gradeFor(90)).toBe('A');
    expect(gradeFor(100)).toBe('A');
  });

  it('returns B for 60-74%', () => {
    expect(gradeFor(60)).toBe('B');
    expect(gradeFor(74)).toBe('B');
  });

  it('returns C for 50-59%', () => {
    expect(gradeFor(50)).toBe('C');
    expect(gradeFor(59)).toBe('C');
  });

  it('returns D for 40-49%', () => {
    expect(gradeFor(40)).toBe('D');
    expect(gradeFor(49)).toBe('D');
  });

  it('returns F below 40%', () => {
    expect(gradeFor(39)).toBe('F');
    expect(gradeFor(0)).toBe('F');
  });

  it('handles out-of-band values', () => {
    expect(gradeFor(-10)).toBe('F');
    expect(gradeFor(150)).toBe('A');
  });
});

describe('gradeColor / scoreColor', () => {
  it('maps every grade to a class', () => {
    expect(gradeColor('A')).toMatch(/^bg-/);
    expect(gradeColor('B')).toMatch(/^bg-/);
    expect(gradeColor('C')).toMatch(/^bg-/);
    expect(gradeColor('D')).toMatch(/^bg-/);
    expect(gradeColor('F')).toMatch(/^bg-/);
  });

  it('scoreColor uses green/amber/red thresholds', () => {
    expect(scoreColor(80)).toContain('emerald');
    expect(scoreColor(60)).toContain('amber');
    expect(scoreColor(30)).toContain('red');
    // boundary
    expect(scoreColor(70)).toContain('emerald');
    expect(scoreColor(50)).toContain('amber');
  });
});

describe('formatDuration', () => {
  it('formats short durations in seconds', () => {
    expect(formatDuration(0)).toBe('0s');
    expect(formatDuration(45)).toBe('45s');
  });

  it('formats minute+second durations', () => {
    expect(formatDuration(60)).toBe('1m 00s');
    expect(formatDuration(125)).toBe('2m 05s');
  });

  it('clamps negative inputs', () => {
    expect(formatDuration(-10)).toBe('0s');
  });
});
