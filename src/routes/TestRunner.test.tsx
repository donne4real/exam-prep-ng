import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { TestRunner } from './TestRunner';
import { resetForTests, loadQuestions } from '../data/loader';
import { useProgressStore } from '../store/progress';
import type { QuestionsFile, Question } from '../types/exam';

function makeQuestion(id: string, correctOptionId: 'a' | 'b' = 'a'): Question {
  return {
    id,
    exam: 'BECE',
    subject: 'Math',
    year: 2020,
    prompt: `Question ${id}?`,
    options: [
      { id: 'a', text: 'Choice A' },
      { id: 'b', text: 'Choice B' },
    ],
    correctOptionId,
  };
}

const fakeFile: QuestionsFile = {
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
  questions: [
    makeQuestion('q1', 'a'),
    makeQuestion('q2', 'a'),
    makeQuestion('q3', 'b'),
  ],
};

beforeEach(() => {
  resetForTests();
  useProgressStore.setState({ attempts: [] });
  vi.stubGlobal(
    'fetch',
    vi.fn(async () =>
      new Response(JSON.stringify(fakeFile), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      }),
    ),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function renderRunner() {
  return render(
    <MemoryRouter initialEntries={['/practice/BECE/Math']}>
      <Routes>
        <Route path="/practice/:examId/:subjectId" element={<TestRunner />} />
        <Route path="/results/:attemptId" element={<div>Results</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('TestRunner submit is idempotent', () => {
  it('clicking Submit twice records exactly one attempt', async () => {
    const user = userEvent.setup();
    await loadQuestions(true);
    renderRunner();

    // Wait for the first question to render. The header reads
    // "Question 1 of 3" and the QuestionCard also reads "Question 1 of 3".
    // Scope the wait to the main article element to avoid the duplicate.
    await waitFor(() => {
      const articles = document.querySelectorAll('article');
      expect(articles.length).toBeGreaterThan(0);
      expect(within(articles[0]).getByText(/Question 1 of/)).toBeInTheDocument();
    });

    // Answer each of the 3 questions by clicking option A in the article.
    for (let i = 0; i < 3; i++) {
      const article = document.querySelectorAll('article')[0];
      const optA = within(article).getByRole('radio', { name: /Choice A/ });
      await user.click(optA);
      // Advance: click Next if not on the last question.
      const nextBtn = screen.queryByRole('button', { name: /^Next$/ });
      if (nextBtn && !(nextBtn as HTMLButtonElement).disabled) {
        await user.click(nextBtn);
      }
    }

    // Click the visible Submit in the sticky footer (not the one in <details>).
    const submitButtons = screen.getAllByRole('button', { name: /^Submit$/ });
    // First match is in the sticky nav (visible on the last question).
    await user.click(submitButtons[0]);

    // Confirm dialog appears — find the dialog and click its Submit.
    const dialog = await screen.findByRole('dialog');
    const confirmBtn = within(dialog).getByRole('button', { name: /^Submit$/ });
    await user.click(confirmBtn);

    // Test should navigate to /results; the TestRunner unmounts.
    await waitFor(() => {
      expect(screen.queryByText('Results')).toBeInTheDocument();
    });

    // Exactly one attempt is recorded, regardless of any double-submit.
    expect(useProgressStore.getState().attempts).toHaveLength(1);
  });
});
