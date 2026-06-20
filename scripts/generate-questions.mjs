// Generates synthetic practice questions to fill per-subject deficits.
//
// Output: appends new questions to public/data/questions.json, with
// `source: 'generated'`. Existing real questions are preserved.
//
// Run: `node scripts/generate-questions.mjs`
//
// The generator pulls facts from a curated knowledge base (see
// knowledge-base.js). Each fact is a fill-in-the-blank question with
// 4 options and an explanation. From each fact we derive up to 12
// distinct questions by varying the option order, so the prompt dedup
// doesn't reject them.

import { readFile, writeFile } from 'node:fs/promises';
import { KNOWLEDGE } from './knowledge-base.js';

const PUBLIC_PATH = new URL('../public/data/questions.json', import.meta.url);
const GENERATED_AT = new Date().toISOString();
const TARGET = 150;
const YEAR_FOR_NEW = 2024;
const VARIANTS_PER_FACT = 12; // 4 positions for correct answer × 3 wrong orderings

const LETTERS = ['a', 'b', 'c', 'd'];

function slug(s) {
  return s.toLowerCase().replace(/\s+/g, '-');
}

function makeQuestionId(exam, subject, n) {
  return `${slug(exam)}-${slug(subject)}-gen-q${n}`;
}

// Returns a 3-tuple of stable, distinct option orderings for the 3
// wrong options. Combined with the 4 possible positions for the correct
// answer, this gives 4 × 3 = 12 unique questions per fact.
function wrongOrderings(seed) {
  // The base is wrong = [B, C, D] in fact order. We produce 3 distinct
  // permutations: identity, swap-last-two, rotate-123.
  return [
    [0, 1, 2],
    [0, 2, 1],
    [2, 0, 1],
    [1, 2, 0],
    [2, 1, 0],
    [1, 0, 2],
  ][seed % 6];
}

function makeQuestionFromFact(fact, exam, subject, n) {
  // Shuffle options using n as seed for the wrong-order + correct-position
  const correct = fact.options[fact.correct];
  const wrong = fact.options.filter((_, i) => i !== fact.correct);
  const order = wrongOrderings(n);
  const shuffledWrong = order.map((idx) => wrong[idx]);
  // Position of correct answer varies with n
  const correctPos = n % 4;
  const final = shuffledWrong.slice();
  final.splice(correctPos, 0, correct);
  const options = final.map((text, i) => ({ id: LETTERS[i], text }));
  const correctId = options.find((o) => o.text === correct).id;

  return {
    id: makeQuestionId(exam, subject, n),
    exam,
    subject,
    year: YEAR_FOR_NEW,
    topic: fact.topic,
    prompt: fact.prompt,
    options,
    correctOptionId: correctId,
    explanation: fact.explanation,
    source: 'generated',
    generatedAt: GENERATED_AT,
  };
}

function questionKey(q) {
  // Dedup key: prompt + sorted option texts. This catches
  // accidentally-identical questions even when the option order differs.
  return [q.prompt, ...q.options.map((o) => o.text)].join('|').toLowerCase();
}

async function main() {
  const raw = await readFile(PUBLIC_PATH, 'utf8');
  const data = JSON.parse(raw);

  const counts = new Map();
  const seenIds = new Set(data.questions.map((q) => q.id));
  // Dedup against real questions by (prompt + option-text) so generated
  // questions don't duplicate anything already in the bank.
  const seenKeys = new Set(
    data.questions.map((q) => {
      return [q.prompt, ...q.options.map((o) => o.text)].join('|').toLowerCase();
    }),
  );
  for (const q of data.questions) {
    const k = `${q.exam}|${q.subject}`;
    counts.set(k, (counts.get(k) ?? 0) + 1);
  }

  const generated = [];
  const reportRows = [];

  for (const [key, facts] of Object.entries(KNOWLEDGE)) {
    const [exam, subject] = key.split('|');
    const current = counts.get(key) ?? 0;
    const needed = Math.max(0, TARGET - current);

    if (needed === 0) {
      reportRows.push({ exam, subject, before: current, after: current, added: 0 });
      continue;
    }

    let added = 0;
    let n = 0;
    // For each fact, try up to VARIANTS_PER_FACT * passes variants
    // (fact cycle) until we have enough.
    const totalPasses = Math.ceil(needed / facts.length) + 2;
    outer:
    for (let pass = 0; pass < totalPasses; pass++) {
      for (let i = 0; i < facts.length; i++) {
        if (added >= needed) break outer;
        const fact = facts[i];
        // Try a few option-shuffle variants per (fact, pass) until we
        // find one that doesn't collide.
        let success = false;
        for (let v = 0; v < VARIANTS_PER_FACT; v++) {
          const q = makeQuestionFromFact(fact, exam, subject, n + v);
          if (seenIds.has(q.id)) continue;
          const k = questionKey(q);
          if (seenKeys.has(k)) continue;
          seenIds.add(q.id);
          seenKeys.add(k);
          generated.push(q);
          added++;
          success = true;
          n += VARIANTS_PER_FACT; // skip past variants we just tried
          break;
        }
        if (!success) {
          n += VARIANTS_PER_FACT; // all variants of this fact collides, move on
        }
      }
    }

    reportRows.push({ exam, subject, before: current, after: current + added, added });
  }

  if (generated.length === 0) {
    console.log('No questions needed generation. All exam-subject pairs already meet the target.');
    return;
  }

  const next = {
    ...data,
    questions: [...data.questions, ...generated],
    lastGenerationRun: GENERATED_AT,
  };

  await writeFile(PUBLIC_PATH, JSON.stringify(next));

  console.log('\n--- Generation report ---');
  for (const r of reportRows) {
    console.log(
      `${r.exam.padEnd(5)} ${r.subject.padEnd(25)} ${String(r.before).padStart(4)} -> ${String(r.after).padStart(4)} (+${r.added})`,
    );
  }
  console.log(`\nTotal generated: ${generated.length}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
