import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ensureBank,
  getBank,
  getBankStatus,
  getState,
  listSubjects,
  subscribe,
} from '../data/loader';
import type { ExamType, Question } from '../types/exam';

const DECK_SIZE = 20;
const EXAMS: ExamType[] = ['BECE', 'NECO', 'WAEC', 'JAMB'];

// Fisher-Yates shuffle
function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function Flashcards() {
  const [tick, setTick] = useState(0);
  useEffect(() => { const unsub = subscribe(() => setTick(t => t + 1)); return unsub; }, []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Flashcards</h1>
        <p className="text-neutral-600 dark:text-neutral-400 mt-1">
          Flip, learn, and track what you know. Pick an exam to begin.
        </p>
      </header>
      <div className="grid grid-cols-2 gap-3">
        {EXAMS.map(exam => (
          <ExamDeckCard key={exam} exam={exam} tick={tick} />
        ))}
      </div>
    </div>
  );
}

function ExamDeckCard({ exam, tick }: { exam: ExamType; tick: number }) {
  const [expanded, setExpanded] = useState(false);
  const subjects = useMemo(() => listSubjects(exam), [exam, tick, getState().status]);
  const cardCount = useMemo(
    () => subjects.reduce((sum, s) => sum + s.questionCount, 0),
    [subjects],
  );

  if (subjects.length === 0 || cardCount === 0) {
    return (
      <div className="card p-4">
        <div className="font-semibold">{exam}</div>
        <p className="text-xs text-neutral-500 mt-1">No flashcards available</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div
        className="p-4 bg-nigeria-green text-white cursor-pointer"
        onClick={() => setExpanded(v => !v)}
      >
        <div className="flex items-center justify-between">
          <span className="font-bold">{exam}</span>
          <svg
            width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
            className={`transition-transform ${expanded ? 'rotate-180' : ''}`}
          >
            <path d="M6 9l6 6 6-6" />
          </svg>
        </div>
        <p className="text-xs text-white/80 mt-1">{cardCount} cards available</p>
      </div>
      {expanded ? (
        <div className="p-3 space-y-2">
          {subjects.map(s => (
            <Link
              key={s.id}
              to={`/flashcards/${exam}/${encodeURIComponent(s.name)}`}
              className="flex items-center justify-between p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900 hover:bg-nigeria-green/10 transition"
            >
              <span className="text-sm font-medium">{s.name}</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M9 18l6-6-6-6" />
              </svg>
            </Link>
          ))}
        </div>
      ) : null}
    </div>
  );
}

// ── Deck view ───────────────────────────────────────────────────
export function FlashcardDeck() {
  const { exam, subject } = useParams<{ exam: ExamType; subject: string }>() ?? { exam: undefined, subject: undefined };
  if (!exam || !subject) {
    return (
      <div className="space-y-4">
        <div className="card p-6 text-center">
          <h2 className="text-xl font-bold mb-2">Subject not found</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            Please select a subject from the flashcards page.
          </p>
          <Link to="/flashcards" className="btn-primary mt-4 inline-flex">
            Go to Flashcards
          </Link>
        </div>
      </div>
    );
  }
  const [tick, setTick] = useState(0);
  useEffect(() => { const unsub = subscribe(() => setTick(t => t + 1)); return unsub; }, []);
  useEffect(() => { void ensureBank(exam, subject); }, [exam, subject]);

  const all = useMemo(() => getBank(exam, subject), [exam, subject, tick, getBankStatus(exam, subject)]);
  const deck = useMemo(() => shuffle(all).slice(0, Math.min(DECK_SIZE, all.length)), [exam, subject, tick]);

  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [known, setKnown] = useState(0);
  const [unknown, setUnknown] = useState(0);
  const [done, setDone] = useState(false);

  if (deck.length === 0) {
    return (
      <div className="space-y-4">
        <div className="card p-6 text-center">
          <h2 className="text-xl font-bold mb-2">No flashcards available</h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            We don't have {subject} {exam} questions yet.
          </p>
          <Link to="/flashcards" className="btn-primary mt-4 inline-flex">
            Pick another subject
          </Link>
        </div>
      </div>
    );
  }

  if (done) {
    const pct = Math.round((known / (known + unknown || 1)) * 100);
    return (
      <div className="space-y-6">
        <header className="card p-6 text-center">
          <div className="text-5xl mb-3">{pct >= 70 ? '🎉' : '📚'}</div>
          <h2 className="text-2xl font-bold">
            {pct >= 80 ? 'Excellent work!' : pct >= 60 ? 'Good job!' : 'Keep practicing!'}
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400 mt-2">
            {known} mastered · {unknown} to revisit
          </p>
          <div className="mt-4">
            <div className="text-4xl font-bold text-nigeria-green">{pct}%</div>
          </div>
          <div className="flex gap-3 mt-5 justify-center">
            <button
              type="button"
              className="btn-primary"
              onClick={() => {
                setIndex(0); setFlipped(false); setKnown(0); setUnknown(0); setDone(false);
              }}
            >
              Study Again
            </button>
            <Link to="/flashcards" className="btn-ghost">All Flashcards</Link>
          </div>
        </header>
      </div>
    );
  }

  const card = deck[index];
  const progress = Math.round((index / deck.length) * 100);

  return (
    <div className="space-y-4">
      {/* Header */}
      <nav className="flex items-center justify-between text-sm text-neutral-500 dark:text-neutral-400">
        <Link to="/flashcards" className="flex items-center gap-1 hover:underline">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M15 18l-6-6 6-6" />
          </svg>
          Flashcards
        </Link>
        <span>{exam} · {subject}</span>
      </nav>

      <div className="flex items-center gap-3 text-sm">
        <div className="h-2 flex-1 rounded-full bg-neutral-200 dark:bg-neutral-800 overflow-hidden">
          <div
            className="h-full bg-nigeria-green transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="tabular-nums text-neutral-500 dark:text-neutral-400 shrink-0">
          {index + 1}/{deck.length}
        </span>
      </div>

      {/* Stats */}
      <div className="flex justify-between text-sm px-1">
        <span className="text-emerald-600 dark:text-emerald-400">✅ {known} known</span>
        <span className="text-red-600 dark:text-red-400">❌ {unknown} to review</span>
      </div>

      {/* Card */}
      <FlipCard
        question={card}
        flipped={flipped}
        onFlip={() => setFlipped(true)}
      />

      {/* Controls */}
      {flipped ? (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => {
                setUnknown(u => u + 1);
                // push card to end for later
                deck.push(card);
                advance();
              }}
            >
              Still Learning
            </button>
            <button
              type="button"
              className="btn-primary"
              onClick={() => {
                setKnown(k => k + 1);
                advance();
              }}
            >
              Got It!
            </button>
          </div>
          <button
            type="button"
            className="btn-ghost w-full"
            onClick={() => setFlipped(false)}
          >
            ← Show Question
          </button>
        </div>
      ) : (
        <button
          type="button"
          className="btn-primary w-full"
          onClick={() => setFlipped(true)}
        >
          Reveal Answer
        </button>
      )}
    </div>
  );

  function advance() {
    if (index + 1 >= deck.length) {
      setDone(true);
    } else {
      setIndex(i => i + 1);
      setFlipped(false);
    }
  }
}

// ── Flip Card ───────────────────────────────────────────────────
function FlipCard({
  question,
  flipped,
  onFlip,
}: {
  question: Question;
  flipped: boolean;
  onFlip: () => void;
}) {
  // animation tracking

  function handleFlip() {
    if (!flipped) {
      
      onFlip();
    }
  }

  return (
    <div className="perspective-1000">
      <div
        role="button"
        tabIndex={0}
        aria-label={flipped ? 'Showing answer' : 'Tap to reveal answer'}
        onClick={handleFlip}
        onKeyDown={e => e.key === 'Enter' && handleFlip()}
        className={`relative w-full min-h-[200px] cursor-pointer select-none transition-transform duration-500`}
        style={{
          transformStyle: 'preserve-3d',
          transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
        }}
      >
        {/* Front */}
        <div
          className="absolute inset-0 rounded-2xl border-2 border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-6 flex flex-col justify-center"
          style={{ backfaceVisibility: 'hidden' }}
        >
          <div className="text-xs text-neutral-500 dark:text-neutral-400 mb-4 uppercase tracking-wide">
            {question.exam} · {question.subject}
          </div>
          <p className="text-base font-medium leading-relaxed">{question.prompt}</p>
          <p className="text-xs text-neutral-400 mt-4 text-center">Tap to reveal answer</p>
        </div>

        {/* Back */}
        <div
          className="absolute inset-0 rounded-2xl border-2 border-nigeria-green bg-nigeria-green/5 p-6 flex flex-col justify-center"
          style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
        >
          <div className="text-xs text-nigeria-green font-semibold mb-3 uppercase tracking-wide">Answer</div>
          {question.options.map(opt => {
            const isCorrect = opt.id === question.correctOptionId;
            return (
              <div
                key={opt.id}
                className={`text-sm font-medium py-1 ${isCorrect ? 'text-emerald-700 dark:text-emerald-400' : 'text-neutral-600 dark:text-neutral-400'}`}
              >
                <span className="mr-2">{opt.id.toUpperCase()}.</span>
                {opt.text}
                {isCorrect && ' ✓'}
              </div>
            );
          })}
          {question.explanation ? (
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-3 leading-relaxed">
              {question.explanation}
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
