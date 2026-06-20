import type { QuestionOption } from '../types/exam';
import { CheckIcon, XIcon } from './icons';

interface Props {
  option: QuestionOption;
  selected: boolean;
  showCorrect: boolean;
  isCorrect: boolean;
  isWrongSelected: boolean;
  onSelect: () => void;
}

const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F'];

export function OptionButton({
  option,
  selected,
  showCorrect,
  isCorrect,
  isWrongSelected,
  onSelect,
}: Props) {
  // Compute letter from the option id if it's a letter; otherwise index.
  const idx = LETTERS.indexOf(option.id.toUpperCase());
  const letter = idx >= 0 ? LETTERS[idx] : LETTERS[0];

  const base =
    'w-full text-left flex items-start gap-3 rounded-xl border-2 p-4 min-h-tap transition select-none';
  const stateClass = (() => {
    if (showCorrect && isCorrect) {
      return 'border-emerald-500 bg-emerald-50 dark:bg-emerald-950/40';
    }
    if (showCorrect && isWrongSelected) {
      return 'border-red-500 bg-red-50 dark:bg-red-950/40';
    }
    if (selected) {
      return 'border-nigeria-green bg-nigeria-green/5 dark:bg-nigeria-green/10';
    }
    return 'border-neutral-200 dark:border-neutral-700 hover:border-nigeria-green hover:bg-neutral-50 dark:hover:bg-neutral-800';
  })();

  const letterClass = (() => {
    if (showCorrect && isCorrect) return 'bg-emerald-500 text-white';
    if (showCorrect && isWrongSelected) return 'bg-red-500 text-white';
    if (selected) return 'bg-nigeria-green text-white';
    return 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-200';
  })();

  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      onClick={onSelect}
      disabled={showCorrect}
      className={`${base} ${stateClass}`}
    >
      <span
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg font-bold text-sm ${letterClass}`}
        aria-hidden="true"
      >
        {letter}
      </span>
      <span className="flex-1 pt-1.5 leading-relaxed whitespace-pre-line">
        {option.text}
      </span>
      {showCorrect && isCorrect ? (
        <span className="text-emerald-600 dark:text-emerald-400 font-semibold pt-2 inline-flex">
          <CheckIcon size={18} />
        </span>
      ) : null}
      {showCorrect && isWrongSelected ? (
        <span className="text-red-600 dark:text-red-400 font-semibold pt-2 inline-flex">
          <XIcon size={18} />
        </span>
      ) : null}
    </button>
  );
}
