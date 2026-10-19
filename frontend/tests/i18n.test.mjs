// The interface strings and formatters (src/i18n). Run with `npm run test:i18n`.
// Pure modules only: no React, no demoService.
import test from 'node:test';
import assert from 'node:assert/strict';
import { arCount, clockTime, num, pct, shortDate } from '../src/i18n/format.js';
import { normalizeLang, stringsFor } from '../src/i18n/stringsFor.js';
import { STRINGS } from '../src/i18n/strings.js';
import { validateStrongPassword } from '../src/utils/validators.js';

const ARABIC_INDIC = /[٠-٩]/;
const LATIN_DIGIT = /[0-9]/;

test('num and pct give Arabic-Indic digits in Arabic and plain digits in English', () => {
  assert.equal(num(1234, 'ar'), '١٢٣٤');
  assert.equal(num(1234, 'en'), '1234');
  assert.equal(pct(60, 'ar'), '٦٠٪');
  assert.equal(pct(60, 'en'), '60%');
  assert.equal(num(0, 'ar'), '٠');
});

test('arCount follows the Arabic plural forms', () => {
  const f = (n) => arCount(n, 'يوم واحد', 'يومان', 'أيام', 'يومًا');
  assert.equal(f(1), 'يوم واحد');
  assert.equal(f(2), 'يومان');
  assert.equal(f(3), '٣ أيام');
  assert.equal(f(10), '١٠ أيام');
  assert.equal(f(11), '١١ يومًا');
  assert.equal(f(25), '٢٥ يومًا');
});

test('dates and times are Gregorian with Arabic-Indic digits in Arabic, whatever the device calendar', () => {
  const iso = '2026-10-05T15:05:00Z';
  const date = shortDate(iso, 'ar');
  assert.match(date, ARABIC_INDIC);
  assert.doesNotMatch(date, LATIN_DIGIT);
  assert.match(date, /أكتوبر/);
  assert.equal(shortDate(iso, 'en'), 'Oct 5');
  assert.equal(shortDate(null, 'ar'), '');
  assert.equal(shortDate('not a date', 'en'), '');
  const time = clockTime(iso, 'ar');
  assert.match(time, ARABIC_INDIC);
  assert.doesNotMatch(time, LATIN_DIGIT);
  assert.match(clockTime(iso, 'en'), /^\d{1,2}:\d{2} (AM|PM)$/);
  assert.equal(clockTime('nope', 'ar'), '');
});

test('normalizeLang and stringsFor default to Arabic', () => {
  assert.equal(normalizeLang('en-US'), 'en');
  assert.equal(normalizeLang('EN'), 'en');
  assert.equal(normalizeLang('ar'), 'ar');
  assert.equal(normalizeLang(undefined), 'ar');
  assert.equal(normalizeLang('fr'), 'ar');
  assert.equal(stringsFor(null), STRINGS.ar);
  assert.equal(stringsFor('en'), STRINGS.en);
  assert.equal(STRINGS.ar.dir, 'rtl');
  assert.equal(STRINGS.en.dir, 'ltr');
});

// Every key in one language exists in the other, with the same kind of value.
const shape = (value, path, out) => {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    for (const key of Object.keys(value)) shape(value[key], `${path}.${key}`, out);
  } else {
    out.set(path, Array.isArray(value) ? 'array' : typeof value);
  }
  return out;
};

test('the Arabic and English dictionaries have the same keys', () => {
  const ar = shape(STRINGS.ar, 'ar', new Map());
  const en = shape(STRINGS.en, 'en', new Map());
  // badgeCatalog and levels map English backend names to Arabic, so English has nothing to add there.
  const skip = (p) => /\.(badgeCatalog|levels|themes|status)\./.test(p);
  const arKeys = [...ar.keys()].map((k) => k.slice(3)).filter((k) => !skip(`x.${k}.`));
  const enKeys = [...en.keys()].map((k) => k.slice(3)).filter((k) => !skip(`x.${k}.`));
  assert.deepEqual(arKeys.sort(), enKeys.sort());
  for (const key of arKeys) {
    assert.equal(ar.get(`ar.${key}`), en.get(`en.${key}`), `type of ${key}`);
  }
});

test('Arabic strings with counts return Arabic-Indic digits only', () => {
  const s = STRINGS.ar;
  const samples = [
    s.quests.progress(2, 5),
    s.badges.count(3, 19),
    s.parent.insights.waiting(4),
    s.parent.insights.levelHint(120, 60),
    s.parent.insights.streakValue(7),
    s.parent.alerts.unread(2),
    s.parent.children.lastActivity(s.time.minutesAgo(5)),
    s.parent.summary.messages(12),
    s.time.daysAgo(3),
  ];
  for (const text of samples) {
    assert.match(text, ARABIC_INDIC, text);
    assert.doesNotMatch(text, LATIN_DIGIT, text);
  }
});

test('task 04: "discussed N times" on a parent source card follows the plural forms in both languages', () => {
  const ar = STRINGS.ar.parent.insights.discussed;
  const en = STRINGS.en.parent.insights.discussed;
  assert.deepEqual([1, 2, 3, 11].map(ar), ['نوقش مرة واحدة', 'نوقش مرتين', 'نوقش ٣ مرات', 'نوقش ١١ مرة']);
  assert.deepEqual([1, 2, 5].map(en), ['Discussed 1 time', 'Discussed 2 times', 'Discussed 5 times']);
});

test('the badge catalog covers every seeded badge with a name and a description', () => {
  const entries = Object.entries(STRINGS.ar.badgeCatalog);
  assert.equal(entries.length, 19);
  for (const [english, value] of entries) {
    assert.ok(/^[A-Za-z' -]+$/.test(english), `${english} is an English badge name`);
    assert.equal(value.length, 2, english);
    for (const text of value) {
      assert.ok(typeof text === 'string' && text.trim().length > 0, english);
      assert.match(text, /[؀-ۿ]/, `${english} is written in Arabic`);
    }
  }
});

test('every English level name has an Arabic name', () => {
  for (const [english, arabic] of Object.entries(STRINGS.ar.levels)) {
    assert.ok(english.length > 0);
    assert.match(arabic, /[؀-ۿ]/, english);
  }
  assert.equal(Object.keys(STRINGS.ar.levels).length, 8);
});

test('lead decisions 5 Oct: values-practised badges, Helpful Heart, the Values category, the nickname الصديق', () => {
  const names = Object.keys(STRINGS.ar.badgeCatalog);
  for (const n of ['First Value Practised', 'Five Values Practised', 'Fifteen Values Practised']) assert.ok(names.includes(n), n);
  for (const n of ['Truthful Heart', 'Honest Soul', 'As-Sadiq Companion']) assert.ok(!names.includes(n), `${n} was renamed by migration 0005`);
  assert.ok('Helpful Heart' in STRINGS.ar.levels && !('Honest Helper' in STRINGS.ar.levels));
  for (const lang of ['ar', 'en']) {
    assert.ok(STRINGS[lang].badges.categories.values && !STRINGS[lang].badges.categories.honesty, lang);
  }
  // the old nickname (الصادق, not the adjective inside another word) is gone from every string
  assert.ok(!/الصادق(?![ء-ي])/.test(JSON.stringify(STRINGS)), 'the nickname is الصديق');
});

test('the quests heading, and the Badges tab heading, are the Arabic tab labels', () => {
  assert.equal(STRINGS.ar.badges.title, 'الأوسمة');
  assert.equal(STRINGS.ar.quests.title, 'المهام');
  assert.equal(STRINGS.en.badges.title, 'Badges');
});

test('password rules are explained in the chosen language', () => {
  assert.match(validateStrongPassword('abc', 'ar'), /[؀-ۿ]/);
  assert.match(validateStrongPassword('abc', 'en'), /[A-Za-z]/);
  assert.equal(validateStrongPassword('Str0ng!Passw0rd', 'ar'), null);
  // callers that do not pass a language keep the English wording
  assert.match(validateStrongPassword('abc'), /[A-Za-z]/);
});

test('the chat suggestions ask for things the agent answers (no story request), in both languages', async () => {
  const { VOICE_COPY } = await import('../src/features/child/voice/copy.js');
  for (const lang of ['ar', 'en']) {
    const ideas = VOICE_COPY[lang].ideas;
    assert.ok(ideas.length >= 3, `${lang} has the suggestions`);
    for (const idea of ideas) {
      // Short value stories are a separate decision; the agent declines a story request today.
      assert.doesNotMatch(idea, /story|قصة|قصّة|احك/i, `${lang}: "${idea}" asks for a story`);
    }
  }
});
