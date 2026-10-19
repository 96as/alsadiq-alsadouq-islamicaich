// The companion's Arabic nickname is «الصديق» (lead decision, 5 Oct). The old «الصادق» / «صادق» must not come back
// into the app source, including with a prefix (للصادق, بالصادق, يا صادق). Run with `npm run test:nickname`.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const SRC = fileURLToPath(new URL('../src', import.meta.url));
const TEXT_FILE = /\.(js|jsx|mjs|ts|tsx|css|json|html|md)$/;

// Any substring counts, so prefixes (لل، ل، بال، وال) and the bare name are all caught.
const OLD_NICKNAME = /صادق/;

// Legitimate uses go here as 'relative/path:line' with a comment saying why. Empty today: all three old uses were fixed.
const ALLOWED = new Set([]);

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* walk(p);
    else if (TEXT_FILE.test(name)) yield p;
  }
}

test('the old nickname صادق is not in frontend/src', () => {
  const hits = [];
  for (const file of walk(SRC)) {
    readFileSync(file, 'utf8').split(/\r?\n/).forEach((line, i) => {
      const where = `${relative(SRC, file).replace(/\\/g, '/')}:${i + 1}`;
      if (OLD_NICKNAME.test(line) && !ALLOWED.has(where)) hits.push(`${where}  ${line.trim()}`);
    });
  }
  assert.deepEqual(hits, [], 'use «الصديق» (the nickname) or «الصديق الصدوق» (the product), never صادق / الصادق');
});

test('the guard itself catches the prefixed forms', () => {
  for (const s of ['للصادق', 'قل للصادق', 'بالصادق', 'يا صادق', 'الصادق']) assert.ok(OLD_NICKNAME.test(s), s);
  for (const s of ['للصديق', 'الصديق الصدوق']) assert.ok(!OLD_NICKNAME.test(s), s);
});
