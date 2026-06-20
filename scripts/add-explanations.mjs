// One-off: re-emit scripts/knowledge-base.js with `explanation` populated
// for every fact. Run once; not part of the regular build.
//
// Each fact already has: prompt, options, correct, topic.
// We compute the correct-answer string and inject:
//   explanation: makeExplanation('<correct answer>', '<topic>')

import { readFile, writeFile } from 'node:fs/promises';

const PATH = new URL('../scripts/knowledge-base.js', import.meta.url);
let src = await readFile(PATH, 'utf8');

// Match a single fact: { prompt: '...', options: [...], correct: N, topic: '...' },
// We rewrite it to include explanation.
const factRe =
  /\{ prompt: ('(?:[^'\\]|\\.)*'), options: (\[[^\]]+\]), correct: (\d+), topic: ('(?:[^'\\]|\\.)*') \},?/g;

let added = 0;
const next = src.replace(factRe, (_m, prompt, optionsLiteral, correctIdx, topic) => {
  // Parse the options array literal to find the correct-answer text.
  // The options are simple string arrays like ['foo', 'bar', 'baz', 'qux'].
  const arr = JSON.parse(optionsLiteral.replace(/'/g, '"').replace(/\\\\/g, '\\\\'));
  const correctAnswer = arr[Number(correctIdx)];
  // Escape single quotes for the embedded string literal
  const esc = (s) => s.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
  added += 1;
  return `{ prompt: ${prompt}, options: ${optionsLiteral}, correct: ${correctIdx}, topic: ${topic}, explanation: makeExplanation('${esc(correctAnswer)}', ${topic}) },`;
});

await writeFile(PATH, next);
console.log('Injected explanation into', added, 'facts');
