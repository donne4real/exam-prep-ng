import { useEffect, useState } from 'react';
import type { Question } from '../types/exam';
import { OptionButton } from './OptionButton';

interface Props {
  question: Question;
  questionNumber: number;
  totalQuestions: number;
  selectedOptionId: string | null;
  showCorrect: boolean;
  onSelect: (optionId: string) => void;
}

export function QuestionCard({
  question,
  questionNumber,
  totalQuestions,
  selectedOptionId,
  showCorrect,
  onSelect,
}: Props) {
  const [showExplanation, setShowExplanation] = useState(false);

  // Reset explanation toggle when the question changes.
  useEffect(() => {
    setShowExplanation(false);
  }, [question.id]);

  return (
    <article
      className="card p-5 sm:p-6 animate-fade-in"
      aria-labelledby={`q-${question.id}-prompt`}
    >
      <header className="flex items-start justify-between gap-3 mb-4">
        <div className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
          Question {questionNumber} of {totalQuestions}
          {question.topic ? (
            <>
              <span aria-hidden="true"> · </span>
              <span className="text-neutral-700 dark:text-neutral-300">
                {question.topic}
              </span>
            </>
          ) : null}
        </div>
      </header>

      <h2
        id={`q-${question.id}-prompt`}
        className="text-lg sm:text-xl font-semibold leading-snug mb-5 whitespace-pre-line"
      >
        {question.prompt}
      </h2>

      <div
        className="space-y-3"
        role="radiogroup"
        aria-label="Answer options"
      >
        {question.options.map((opt) => {
          const isSelected = selectedOptionId === opt.id;
          const isCorrect =
            showCorrect && opt.id === question.correctOptionId;
          const isWrongSelected =
            showCorrect && isSelected && opt.id !== question.correctOptionId;
          return (
            <OptionButton
              key={opt.id}
              option={opt}
              selected={isSelected}
              showCorrect={showCorrect}
              isCorrect={isCorrect}
              isWrongSelected={isWrongSelected}
              onSelect={() => onSelect(opt.id)}
            />
          );
        })}
      </div>

      {question.explanation ? (
        <div className="mt-5">
          <button
            type="button"
            className="text-sm font-medium text-nigeria-green dark:text-nigeria-green-light hover:underline"
            onClick={() => setShowExplanation((v) => !v)}
            aria-expanded={showExplanation}
            aria-controls={`q-${question.id}-explanation`}
          >
            {showExplanation ? 'Hide explanation' : 'Show explanation'}
          </button>
          {showExplanation ? (
            <div
              id={`q-${question.id}-explanation`}
              className="mt-2 rounded-xl bg-neutral-50 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 p-4 text-sm leading-relaxed animate-slide-up"
            >
              {question.explanation}
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}
