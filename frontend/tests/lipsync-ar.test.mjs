// Run with: npm run test:lipsync   (node's built-in test runner, no extra dependency)
// The Arabic vowel mode of the audio-only lip-sync: three vowel classes, no r viseme, a visible
// amplitude floor, and the jaw coupling. The 22 tests in lipsync.test.mjs keep covering 'en'.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ArabicVowelRule, VOWEL_A, VOWEL_I, VOWEL_U } from '../src/features/child/components/avatar/lipsync/arabicVowels.js';
import { VisemeClassifier } from '../src/features/child/components/avatar/lipsync/visemeClassifier.js';
import { ARABIC, CLASSIFIER } from '../src/features/child/components/avatar/lipsync/lipsyncConfig.js';
import { jawOpenTable, jawTarget } from '../src/features/child/components/avatar/lipsync/jaw.js';
import { analyseBuffer } from '../src/features/child/components/avatar/lipsync/lipsyncEngine.js';
import { VISEMES, VI } from '../src/features/child/components/avatar/lipsync/visemes.js';
import { JAW } from '../src/features/child/components/avatar/avatarConfig.js';
import {
  VOWEL_FORMANTS,
  concat,
  silence,
  vowel,
} from '../src/features/child/components/avatar/lipsync/testSignals.js';

const SR = 48000;

function meanWeights(frames, from, to) {
  const sum = new Float32Array(VISEMES.length);
  let n = 0;
  for (const f of frames) {
    if (f.t < from || f.t > to) continue;
    n++;
    for (let i = 0; i < sum.length; i++) sum[i] += f.weights[i];
  }
  return Array.from(sum, (v) => v / Math.max(1, n));
}
const top = (w) => VISEMES[w.indexOf(Math.max(...w))];

test('rule: a frame run at a, i and u formants gives the three classes', () => {
  const rule = new ArabicVowelRule(ARABIC);
  let c = VOWEL_A;
  for (let k = 0; k < 5; k++) c = rule.push(560, 1500);
  assert.equal(c, VOWEL_A);
  for (let k = 0; k < 5; k++) c = rule.push(300, 2150);
  assert.equal(c, VOWEL_I);
  for (let k = 0; k < 5; k++) c = rule.push(360, 1050);
  assert.equal(c, VOWEL_U);
});

test('rule: one noisy frame does not flip the class (median) and a frame without formants is skipped', () => {
  const rule = new ArabicVowelRule({ ...ARABIC, medianFrames: 3 });
  for (let k = 0; k < 4; k++) rule.push(300, 2150);
  assert.equal(rule.push(780, 1250), VOWEL_I, 'a single outlier is outvoted');
  assert.equal(rule.push(0, 0), VOWEL_I, 'no formants keeps the last class');
});

test('rule: ambiguous formants default to a, the commonest vowel', () => {
  const rule = new ArabicVowelRule(ARABIC);
  let c = VOWEL_I;
  for (let k = 0; k < 5; k++) c = rule.push(520, 1700);
  assert.equal(c, VOWEL_A);
});

for (const [name, want] of [['aa', 'aa'], ['I', 'I'], ['U', 'U']]) {
  test(`ar: a sustained ${name} vowel gives ${want}`, () => {
    const sig = concat(silence(0.3), vowel({ ...VOWEL_FORMANTS[name], dur: 0.5 }), silence(0.4));
    const r = analyseBuffer(sig, SR, { lang: 'ar' });
    const w = meanWeights(r.frames, 0.5, 0.7);
    assert.equal(top(w), want, JSON.stringify(w.map((v) => +v.toFixed(2))));
  });
}

test('ar: the weights of a vowel are one class, not a blend of five', () => {
  const sig = concat(silence(0.3), vowel({ ...VOWEL_FORMANTS.aa, dur: 0.5 }), silence(0.3));
  const r = analyseBuffer(sig, SR, { lang: 'ar' });
  const w = meanWeights(r.frames, 0.5, 0.7);
  assert.ok(w[VI.aa] > 0.5, `aa ${w[VI.aa]}`);
  assert.ok(w[VI.E] + w[VI.O] < 0.05);
});

test('ar: a quiet vowel still opens the mouth visibly (amplitude floor)', () => {
  const sig = concat(silence(0.3), vowel({ ...VOWEL_FORMANTS.aa, dur: 0.5, rms: 0.02 }), silence(0.3));
  const loud = concat(silence(0.3), vowel({ ...VOWEL_FORMANTS.aa, dur: 0.5, rms: 0.3 }), silence(0.3));
  const q = meanWeights(analyseBuffer(sig, SR, { lang: 'ar' }).frames, 0.5, 0.7)[VI.aa];
  const l = meanWeights(analyseBuffer(loud, SR, { lang: 'ar' }).frames, 0.5, 0.7)[VI.aa];
  assert.ok(q > 0.3, `quiet aa ${q}`);
  assert.ok(l >= q, 'a louder vowel is not smaller');
});

test('ar: the r viseme is off, and en keeps it', () => {
  // Features of a voiced frame with a low F3 and F1 and a mid-low F2: the American r.
  const frame = {
    rms: 0.1, voicing: 0.95, f1: 450, f2: 900, f3: 1700, centroid: 900,
    low: 1, mid: 0.2, high: 0.02, sib: 0.01,
  };
  const peak = (lang) => {
    const cls = new VisemeClassifier(CLASSIFIER, lang);
    let m = 0;
    for (let k = 0; k < 20; k++) m = Math.max(m, cls.update(frame, 1 / 60)[VI.RR]);
    return m;
  };
  assert.equal(peak('ar'), 0);
  assert.ok(peak('en') > 0.1, `en RR ${peak('en')}`);
});

test('en is the default and is unchanged by the lang option', () => {
  const sig = concat(silence(0.3), vowel({ ...VOWEL_FORMANTS.E, dur: 0.5 }), silence(0.3));
  const a = analyseBuffer(sig, SR);
  const b = analyseBuffer(sig, SR, { lang: 'en' });
  assert.equal(a.frames.length, b.frames.length);
  for (let n = 0; n < a.frames.length; n++) {
    for (let i = 0; i < VISEMES.length; i++) assert.equal(a.frames[n].weights[i], b.frames[n].weights[i]);
  }
  assert.equal(top(meanWeights(a.frames, 0.5, 0.7)), 'E');
});

test('jaw: loudness scales the opening and a lip closure holds the chin up', () => {
  const table = jawOpenTable(JAW.open);
  const shown = new Float32Array(VISEMES.length);
  shown[VI.aa] = 1;
  const opts = { couple: JAW.levelCouple, ppMax: JAW.ppMax, ppAt: JAW.ppAt };
  const loud = jawTarget(shown, table, { ...opts, level: 1 });
  const quiet = jawTarget(shown, table, { ...opts, level: 0.2 });
  assert.ok(loud > quiet, `${loud} vs ${quiet}`);
  assert.equal(jawTarget(shown, table), jawTarget(shown, table, { level: 0.2 }), 'couple 0 ignores level');
  shown[VI.PP] = 0.9;
  shown[VI.aa] = 0.6;
  assert.ok(jawTarget(shown, table, { ...opts, level: 1 }) <= JAW.ppMax + 1e-9);
});
