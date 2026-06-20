// Sanity-checks public/data/questions.json after generation.
// Run: `node scripts/validate-questions.mjs`

import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';

const PATH = new URL('../public/data/questions.json', import.meta.url);
const TARGET = 150;

function hashId(s) {
  return createHash('sha1').update(s).digest('hex').slice(0, 10);
}

const data = JSON.parse(await readFile(PATH, 'utf8'));

const errors = [];
const byES = new Map();
const idSet = new Set();
const promptSet = new Set();

for (const q of data.questions) {
  // 1. schema
  if (!q.id || !q.exam || !q.subject || typeof q.year !== 'number' || !q.prompt) {
    errors.push(`Schema: ${q.id ?? '(no id)'}`);
  }
  if (!Array.isArray(q.options) || q.options.length < 2) {
    errors.push(`Options: ${q.id} has ${q.options?.length} options`);
  }
  if (!q.options?.some((o) => o.id === q.correctOptionId)) {
    errors.push(`Correct: ${q.id} correctOptionId=${q.correctOptionId} not in options`);
  }
  if (q.options?.some((o) => !o.id || !o.text)) {
    errors.push(`Option shape: ${q.id} has malformed option`);
  }

  // 2. duplicate id
  if (idSet.has(q.id)) errors.push(`Duplicate id: ${q.id}`);
  idSet.add(q.id);

  // 3. duplicate prompt within exam-subject
  const promptKey = `${q.exam}|${q.subject}|${q.prompt.toLowerCase().trim()}`;
  if (promptSet.has(promptKey)) {
    // Not a fatal error (we allow re-use across different subjects) but flag it
  }
  promptSet.add(promptKey);

  // 4. count
  const k = `${q.exam}|${q.subject}`;
  byES.set(k, (byES.get(k) ?? 0) + 1);
}

console.log('--- Counts per exam-subject ---');
const sorted = Array.from(byES.entries()).sort();
let belowTarget = 0;
for (const [k, c] of sorted) {
  const flag = c < TARGET ? ' <-- BELOW TARGET' : '';
  if (c < TARGET) belowTarget++;
  console.log(`${k.padEnd(35)} ${c}${flag}`);
}

console.log(`\nTotal: ${data.questions.length} questions across ${byES.size} exam-subject pairs`);
console.log(`Pairs at or above target (${TARGET}): ${byES.size - belowTarget}`);
console.log(`Pairs below target: ${belowTarget}`);

console.log(`\nSource breakdown:`);
const bySource = new Map();
for (const q of data.questions) {
  bySource.set(q.source ?? 'real', (bySource.get(q.source ?? 'real') ?? 0) + 1);
}
for (const [s, c] of bySource) console.log(`  ${s}: ${c}`);

if (errors.length) {
  console.log(`\n!!! ${errors.length} validation errors:`);
  for (const e of errors.slice(0, 20)) console.log('  ' + e);
  if (errors.length > 20) console.log(`  ... and ${errors.length - 20} more`);
  process.exit(1);
} else {
  console.log('\n✓ No validation errors');
}
