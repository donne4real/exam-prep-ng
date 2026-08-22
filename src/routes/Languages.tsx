import { useState } from 'react';
import { Link } from 'react-router-dom';
import { LANGUAGES } from '../data/languages';

export function Languages() {
  const [active, setActive] = useState('yoruba');

  const lang = LANGUAGES.find(l => l.id === active) ?? LANGUAGES[0];
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);

  if (lang.status === 'coming') {
    return (
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-bold">Languages</h1>
          <p className="text-neutral-600 dark:text-neutral-400 mt-1">
            Nigerian language learning — coming soon.
          </p>
        </header>
        <div className="card p-6 text-center border-l-4 border-l-nigeria-gold">
          <div className="text-4xl mb-3">🔜</div>
          <h2 className="text-xl font-bold">{lang.name}</h2>
          <p className="text-neutral-600 dark:text-neutral-400 mt-2">
            The {lang.name} curriculum is being built. Check back soon!
          </p>
          <Link to="/languages" className="btn-outline mt-4 inline-flex">
            Back to Languages
          </Link>
        </div>
      </div>
    );
  }

  const current = lang.phrases[index] ?? lang.phrases[0];
  const progress = Math.round(((index + 1) / lang.phrases.length) * 100);

  function next() {
    if (index < lang.phrases.length - 1) {
      setIndex(i => i + 1);
      setFlipped(false);
    }
  }
  function prev() {
    if (index > 0) {
      setIndex(i => i - 1);
      setFlipped(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Languages</h1>
        <p className="text-neutral-600 dark:text-neutral-400 mt-1">
          Learn Nigerian languages — one phrase at a time.
        </p>
      </header>

      {/* Language tabs */}
      <div className="flex gap-2 flex-wrap">
        {LANGUAGES.map(l => (
          <button
            key={l.id}
            type="button"
            onClick={() => { setActive(l.id); setIndex(0); setFlipped(false); }}
            disabled={l.status === 'coming'}
            className={`px-4 py-2 rounded-xl text-sm font-semibold border-2 transition ${
              active === l.id
                ? 'bg-nigeria-green text-white border-nigeria-green'
                : l.status === 'coming'
                ? 'bg-neutral-100 dark:bg-neutral-800 text-neutral-400 border-neutral-200 dark:border-neutral-700 cursor-not-allowed'
                : 'bg-white dark:bg-neutral-900 text-neutral-700 dark:text-neutral-300 border-neutral-200 dark:border-neutral-700 hover:border-nigeria-green'
            }`}
          >
            {l.name}
            {l.status === 'coming' && ' 🔜'}
          </button>
        ))}
      </div>

      {/* Phrase counter */}
      <div className="flex items-center gap-3 text-sm">
        <div className="h-2 flex-1 rounded-full bg-neutral-200 dark:bg-neutral-800 overflow-hidden">
          <div
            className="h-full bg-nigeria-green transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="tabular-nums text-neutral-500 dark:text-neutral-400 shrink-0">
          {index + 1} / {lang.phrases.length}
        </span>
      </div>

      {/* Phrase card */}
      <div
        role="button"
        tabIndex={0}
        onClick={() => !flipped && setFlipped(true)}
        onKeyDown={e => e.key === 'Enter' && !flipped && setFlipped(true)}
        className={`relative w-full min-h-[180px] rounded-2xl border-2 cursor-pointer select-none transition-all duration-300 p-6 flex flex-col justify-center ${
          flipped
            ? 'border-nigeria-green bg-nigeria-green/5'
            : 'border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900'
        }`}
      >
        {!flipped ? (
          <>
            <div className="text-xs text-neutral-500 dark:text-neutral-400 mb-3 uppercase tracking-wide">English</div>
            <p className="text-xl font-medium leading-relaxed">{current.english}</p>
            <p className="text-xs text-neutral-400 mt-4 text-center">Tap to see {lang.name}</p>
          </>
        ) : (
          <>
            <div
              className="text-xs font-semibold mb-3 uppercase tracking-wide"
              style={{ color: lang.color }}
            >
              {lang.name}
            </div>
            <p className="text-2xl font-bold leading-snug" style={{ color: lang.color }}>
              {current.native}
            </p>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-2">
              🔊 {current.pronunciation}
            </p>
            {current.notes ? (
              <p className="text-xs text-neutral-500 dark:text-neutral-500 mt-1 italic">{current.notes}</p>
            ) : null}
          </>
        )}
      </div>

      {/* Navigation */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="btn-secondary flex-1"
          onClick={prev}
          disabled={index === 0}
        >
          ← Previous
        </button>
        {flipped && index < lang.phrases.length - 1 ? (
          <button
            type="button"
            className="btn-primary flex-1"
            onClick={next}
          >
            Next →
          </button>
        ) : (
          <button
            type="button"
            className="btn-primary flex-1"
            onClick={() => !flipped && setFlipped(true)}
            disabled={flipped && index === lang.phrases.length - 1}
          >
            {flipped ? 'Last card' : 'Reveal'}
          </button>
        )}
      </div>

      {/* Phrase list */}
      <details className="card p-4">
        <summary className="cursor-pointer text-sm font-medium select-none">
          All phrases ({lang.phrases.length})
        </summary>
        <div className="mt-3 space-y-2 max-h-64 overflow-y-auto">
          {lang.phrases.map((p, i) => (
            <button
              key={p.id}
              type="button"
              onClick={() => { setIndex(i); setFlipped(false); }}
              className={`w-full text-left p-3 rounded-lg text-sm transition ${
                i === index
                  ? 'bg-nigeria-green/10 border border-nigeria-green'
                  : 'hover:bg-neutral-50 dark:hover:bg-neutral-800'
              }`}
            >
              <div className="font-medium text-neutral-800 dark:text-neutral-200">{p.english}</div>
              <div className="text-xs" style={{ color: lang.color }}>{p.native}</div>
            </button>
          ))}
        </div>
      </details>
    </div>
  );
}
