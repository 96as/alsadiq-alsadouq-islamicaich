// Ground-truth labels for the Arabic lip-sync evaluation, built from the ElevenLabs
// character alignment of the cached test clips (dev-audio/eval-ar/, made by synth_testset.py).
//
// This file must NOT import the browser's arabicText.js: the product's letter-to-mouth mapping
// is what the score judges, so a mistake in it must not be able to hide in the labels.
//
// Nothing here may contain scripture or any other Islamic text; it is signal-processing data.
//
// What the labels are:
//   9 visual groups per 60 fps frame (SIL CLOSED LABIODENT OPEN SPREAD ROUND SIBIL TONGUE THROAT)
//   a 14-viseme label from a plain table (for the 14x14 matrix)
//   the vowel class (a, i, u) and whether it is long
//   a list of bilabial tokens (م ب) with their consonant spans, for the closure score
// Frames that no rule can name (a silent wasla alef, the assimilated lam of a sun letter) get
// group -1 and are left out of every score.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const EVAL_DIR = path.join(HERE, '..', '..', 'dev-audio', 'eval-ar');
export const FPS = 60;

export const GROUPS = ['SIL', 'CLOSED', 'LABIODENT', 'OPEN', 'SPREAD', 'ROUND', 'SIBIL', 'TONGUE', 'THROAT'];
export const G = Object.freeze(Object.fromEntries(GROUPS.map((n, i) => [n, i])));
/** How open the mouth is for each group (for the lag cross-correlation), in GROUPS order. */
export const GROUP_OPENNESS = [0, 0, 0.1, 1.0, 0.3, 0.35, 0.15, 0.25, 0.3];

const VISEMES = ['sil', 'PP', 'FF', 'DD', 'kk', 'CH', 'SS', 'nn', 'RR', 'aa', 'E', 'I', 'O', 'U'];
const V = Object.freeze(Object.fromEntries(VISEMES.map((n, i) => [n, i])));

const FATHA = 'َ';
const FATHATAN = 'ً';
const KASRA = 'ِ';
const KASRATAN = 'ٍ';
const DAMMA = 'ُ';
const DAMMATAN = 'ٌ';
const SHADDA = 'ّ';
const SUKUN = 'ْ';
const DAGGER = 'ٰ';
const VOWEL_OF = {
  [FATHA]: 'a', [FATHATAN]: 'a', [KASRA]: 'i', [KASRATAN]: 'i', [DAMMA]: 'u', [DAMMATAN]: 'u',
};
const VOWEL_GROUP = { a: G.OPEN, i: G.SPREAD, u: G.ROUND };
const VOWEL_V14 = { a: V.aa, i: V.I, u: V.U };
const isMark = (c) => (c >= 'ً' && c <= 'ْ') || c === DAGGER;
const PUNCT = new Set(['،', '؛', '؟', '.', '!', ':', ',', ';', '?']);
const isSpace = (c) => c === ' ' || c === ' ' || c === '\n';

// Consonant letter -> [group, 14-viseme label].
const LETTERS = {};
const put = (letters, group, v14) => {
  for (const ch of letters) LETTERS[ch] = [group, v14];
};
put('بم', G.CLOSED, V.PP); // ba, meem
put('ف', G.LABIODENT, V.FF); // fa
put('سصز', G.SIBIL, V.SS); // seen, sad, zay
put('شج', G.SIBIL, V.CH); // sheen, jeem
put('ثذظ', G.TONGUE, V.DD); // tha, dhal, dha (the tongue shows between the teeth)
put('تدطض', G.TONGUE, V.DD); // ta, dal, ta (emphatic), dad
put('نل', G.TONGUE, V.nn); // noon, lam
put('ر', G.TONGUE, V.RR); // ra
put('كقخغ', G.TONGUE, V.kk); // kaf, qaf, kha, ghain
put('عحه', G.THROAT, V.aa); // ain, ha, ha
put('ءأإؤئ', G.THROAT, V.sil); // hamza and its seats (a glottal stop)
put('و', G.ROUND, V.U); // waw as a consonant
put('ي', G.SPREAD, V.I); // ya as a consonant

const ALIF = 'ا';
const ALIF_MAQSURA = 'ى';
const WAW = 'و';
const YA = 'ي';
const LAM = 'ل';
const TA_MARBUTA = 'ة';
// Letters whose first sound has no silent closure before it: the audio onset lines up with the
// alignment start, so they can be used to measure the alignment bias.
const ONSET_LETTERS = new Set([...'اأإءعنمسصزشفثذظخغحهيو']);

/** Read a cached clip: raw samples, the alignment as sent, the sample rate. */
export function loadClip(id, variant, dir = EVAL_DIR) {
  const name = `${id}.${variant}`;
  const buf = fs.readFileSync(path.join(dir, `${name}.f32`));
  const pcm = new Float32Array(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
  const al = JSON.parse(fs.readFileSync(path.join(dir, `${name}.align.json`), 'utf8'));
  return { id, variant, name, pcm, sr: al.sr, text: al.text, chars: al.characters, starts: al.starts, ends: al.ends };
}

export function loadTestset() {
  return JSON.parse(fs.readFileSync(path.join(HERE, 'testset-ar.json'), 'utf8'));
}

/**
 * Turn an alignment into labelled spans (seconds, not yet shifted by the alignment bias).
 * `variant` is 'diac' (marks present: full vowel truth) or 'plain' (letters only).
 * @returns {{spans: object[], bilabials: object[]}}
 */
export function buildSpans({ chars, starts, ends }, variant) {
  const spans = [];
  const bilabials = [];
  const n = chars.length;
  let prevVowel = ''; // vowel class of the previous letter cluster ('a' | 'i' | 'u' | '')
  let prevWasWordEnd = true;
  let word = 0;
  let lettersInWord = 0; // letters of this word before the current one
  let i = 0;
  while (i < n) {
    const ch = chars[i];
    if (isMark(ch)) {
      i++;
      continue; // a stray mark with no letter before it
    }
    if (isSpace(ch) || PUNCT.has(ch)) {
      // A run of spaces and punctuation is one pause.
      let j = i;
      let punct = false;
      while (j < n && (isSpace(chars[j]) || PUNCT.has(chars[j]))) {
        if (PUNCT.has(chars[j])) punct = true;
        j++;
      }
      spans.push({ ch: chars[i], t0: starts[i], t1: ends[j - 1], kind: 'pause', punct, word });
      word++;
      prevVowel = '';
      prevWasWordEnd = true;
      lettersInWord = 0;
      i = j;
      continue;
    }
    // A letter and the marks that follow it.
    let j = i + 1;
    const marks = [];
    while (j < n && isMark(chars[j])) marks.push(j++);
    const t0 = starts[i];
    const t1 = ends[j - 1];
    let vowel = '';
    let vowelDur = 0;
    let hasSukun = false;
    let hasShadda = false;
    let consDur = ends[i] - starts[i];
    let tanween = false;
    for (const m of marks) {
      const mc = chars[m];
      const d = ends[m] - starts[m];
      if (VOWEL_OF[mc]) {
        vowel = VOWEL_OF[mc];
        vowelDur += d;
        if (mc === FATHATAN || mc === KASRATAN || mc === DAMMATAN) tanween = true;
      } else if (mc === DAGGER) {
        vowel = 'a';
        vowelDur += d;
      } else {
        if (mc === SUKUN) hasSukun = true;
        if (mc === SHADDA) hasShadda = true;
        consDur += d; // shadda and sukun time belong to the consonant
      }
    }
    // After the marks, is this the end of the word? (the next base char is a space, punctuation or the end)
    const next = j < n ? chars[j] : ' ';
    const wordEnd = isSpace(next) || PUNCT.has(next);
    const wordStart = prevWasWordEnd;
    const geminate = hasShadda;
    const nextLetterShadda = (() => {
      let k = j;
      if (k >= n || isMark(chars[k]) || isSpace(chars[k]) || PUNCT.has(chars[k])) return false;
      k++;
      while (k < n && isMark(chars[k])) {
        if (chars[k] === SHADDA) return true;
        k++;
      }
      return false;
    })();

    // The next letter cluster: does it carry a vowel mark, a sukun?
    let nextBase = '';
    let nextVowel = false;
    let nextSukun = false;
    if (j < n && !isMark(chars[j]) && !isSpace(chars[j]) && !PUNCT.has(chars[j])) {
      nextBase = chars[j];
      for (let k = j + 1; k < n && isMark(chars[k]); k++) {
        if (VOWEL_OF[chars[k]] || chars[k] === DAGGER) nextVowel = true;
        if (chars[k] === SUKUN) nextSukun = true;
      }
    }
    // A silent alef after a one-letter prefix: the article (next lam has no vowel) or an imperative
    // (next letter has a sukun; a long a is never followed by a bare sukun).
    const silentAlef =
      lettersInWord === 1 && prevVowel !== '' && ((nextBase === LAM && !nextVowel) || (nextSukun && nextBase !== LAM));
    const total = t1 - t0;
    // Layout inside the cluster: consonant first, then the vowel (the order the labels use).
    const split = vowelDur > 0 ? Math.min(total, consDur) : total;
    const cons = (group, v14, extra = {}) =>
      spans.push({ ch, t0, t1: t0 + split, kind: 'cons', group, v14, vclass: '', long: false, word, letter: ch, ...extra });
    const vow = (cls, long, extra = {}) =>
      spans.push({
        ch, t0: long ? t0 : t0 + split, t1, kind: 'vowel', group: VOWEL_GROUP[cls], v14: VOWEL_V14[cls], vclass: cls, long, word, letter: ch, ...extra,
      });
    const neutral = () => spans.push({ ch, t0, t1, kind: 'neutral', group: -1, v14: V.sil, vclass: '', long: false, word, letter: ch });

    if (variant === 'plain') {
      // Letters only: a span holds the letter and whatever short vowel follows it, so only the
      // long vowels are named. Everything else is a consonant span with an unknown vowel.
      if (ch === ALIF || ch === ALIF_MAQSURA) {
        if (!wordStart) spans.push({ ch, t0, t1, kind: 'vowel', group: G.OPEN, v14: V.aa, vclass: 'a', long: true, word, letter: ch });
        else neutral();
      } else if (LETTERS[ch]) {
        const [group, v14] = LETTERS[ch];
        spans.push({ ch, t0, t1, kind: 'cons', group, v14, vclass: '', long: false, word, letter: ch, unknownVowel: true });
        if (ch === 'ب' || ch === 'م') {
          bilabials.push({ ch, t0, t1, geminate: false, pos: wordStart ? 'initial' : wordEnd ? 'final' : 'medial' });
        }
      } else if (ch === TA_MARBUTA) {
        spans.push({ ch, t0, t1, kind: 'cons', group: G.TONGUE, v14: V.DD, vclass: '', long: false, word, letter: ch, unknownVowel: true });
      } else {
        neutral();
      }
      prevVowel = '';
      prevWasWordEnd = false;
      lettersInWord++;
      i = j;
      continue;
    }

    // ---- diac ----
    let longVowel = false;
    if (ch === ALIF || ch === ALIF_MAQSURA) {
      if (vowel) vow(vowel, false); // a carrier alef with its own vowel mark: only the vowel is heard
      else if (silentAlef) neutral();
      else if (prevVowel === 'a') {
        vow('a', true); // long a
        longVowel = true;
      } else neutral(); // wasla: silent
    } else if (ch === WAW && !vowel && !hasSukun && !hasShadda && prevVowel === 'u') {
      vow('u', true); // long u
      longVowel = true;
    } else if (ch === YA && !vowel && !hasSukun && !hasShadda && prevVowel === 'i') {
      vow('i', true); // long i
      longVowel = true;
    } else if (ch === LAM && !vowel && !hasSukun && nextLetterShadda) {
      neutral(); // the lam of the article before a sun letter is not pronounced
    } else if (ch === TA_MARBUTA && !vowel) {
      cons(G.THROAT, V.aa); // pause form
    } else if (ch === TA_MARBUTA) {
      cons(G.TONGUE, V.DD);
      if (vowel) vow(vowel, false);
    } else if (LETTERS[ch]) {
      const [group, v14] = LETTERS[ch];
      cons(group, v14, { geminate });
      if (vowel) vow(vowel, false);
      if (ch === 'ب' || ch === 'م') {
        bilabials.push({ ch, t0, t1: t0 + split, geminate, pos: wordStart ? 'initial' : wordEnd ? 'final' : 'medial' });
      }
    } else {
      neutral();
    }
    // The vowel the next letter may lengthen: this cluster's own short vowel, nothing after a
    // long vowel, a sukun or a silent letter.
    prevVowel = longVowel ? '' : vowel;
    prevWasWordEnd = false;
    lettersInWord++;
    i = j;
  }
  return { spans, bilabials };
}

/** Shift spans and bilabial tokens by `bias` seconds (audio onset minus alignment start). */
export function shiftSpans(built, bias) {
  const sh = (s) => ({ ...s, t0: s.t0 + bias, t1: s.t1 + bias });
  return { spans: built.spans.map(sh), bilabials: built.bilabials.map(sh) };
}

/**
 * Per-frame labels. Frame n is at time t = (n + 1) / fps, the convention of analyseBuffer.
 * A short pause (under 100 ms) is not a pause: its first half takes the previous group and its
 * second half the next one.
 */
export function labelFrames({ spans }, nFrames, fps = FPS) {
  const group = new Int8Array(nFrames).fill(-1);
  const v14 = new Int8Array(nFrames).fill(V.sil);
  const vclass = new Uint8Array(nFrames); // 0 none, 1 a, 2 i, 3 u
  const vlong = new Uint8Array(nFrames);
  const isVowelFrame = new Uint8Array(nFrames); // 1 inside the mid 60 % of a vowel span
  const spanOf = new Int32Array(nFrames).fill(-1);
  const CLS = { a: 1, i: 2, u: 3 };
  // Pass 1: everything except short pauses.
  for (let s = 0; s < spans.length; s++) {
    const sp = spans[s];
    if (sp.kind === 'pause' && sp.t1 - sp.t0 < 0.1) continue;
    const a = Math.max(0, Math.ceil(sp.t0 * fps - 1));
    const b = Math.min(nFrames - 1, Math.ceil(sp.t1 * fps - 1) - 1);
    for (let f = a; f <= b; f++) {
      spanOf[f] = s;
      if (sp.kind === 'pause') {
        group[f] = G.SIL;
        v14[f] = V.sil;
      } else if (sp.kind === 'neutral') {
        group[f] = -1;
      } else {
        group[f] = sp.group;
        v14[f] = sp.v14;
        if (sp.kind === 'vowel') {
          vclass[f] = CLS[sp.vclass];
          vlong[f] = sp.long ? 1 : 0;
          const d = sp.t1 - sp.t0;
          const t = (f + 1) / fps;
          if (d >= 0.04 && t >= sp.t0 + 0.2 * d && t <= sp.t1 - 0.2 * d) isVowelFrame[f] = 1;
        }
      }
    }
  }
  // Pass 2: short pauses split between the neighbours.
  for (let s = 0; s < spans.length; s++) {
    const sp = spans[s];
    if (sp.kind !== 'pause' || sp.t1 - sp.t0 >= 0.1) continue;
    const prev = spans[s - 1];
    const next = spans[s + 1];
    const mid = 0.5 * (sp.t0 + sp.t1);
    const a = Math.max(0, Math.ceil(sp.t0 * fps - 1));
    const b = Math.min(nFrames - 1, Math.ceil(sp.t1 * fps - 1) - 1);
    for (let f = a; f <= b; f++) {
      const t = (f + 1) / fps;
      const src = t < mid ? prev : next;
      spanOf[f] = s;
      if (!src || src.kind === 'pause' || src.kind === 'neutral') {
        group[f] = src && src.kind === 'neutral' ? -1 : G.SIL;
        continue;
      }
      group[f] = src.group;
      v14[f] = src.v14;
    }
  }
  return { group, v14, vclass, vlong, isVowelFrame, spanOf, fps };
}

/** For a lenient score: the group of the vowel span nearest in time to each frame. */
export function nearestVowelGroup({ spans }, nFrames, fps = FPS) {
  const out = new Int8Array(nFrames).fill(-1);
  const vs = spans.filter((s) => s.kind === 'vowel');
  if (!vs.length) return out;
  let k = 0;
  for (let f = 0; f < nFrames; f++) {
    const t = (f + 1) / fps;
    while (k + 1 < vs.length && Math.abs(0.5 * (vs[k + 1].t0 + vs[k + 1].t1) - t) < Math.abs(0.5 * (vs[k].t0 + vs[k].t1) - t)) k++;
    out[f] = vs[k].group;
  }
  return out;
}

// ---------------------------------------------------------------------------------------------
// Audio helpers used by the validity checks (plain JS, no browser code).

/** RMS of non-overlapping `hop`-second windows. */
export function rmsSeries(pcm, sr, hop = 0.005) {
  const n = Math.floor(sr * hop);
  const out = new Float32Array(Math.floor(pcm.length / n));
  for (let k = 0; k < out.length; k++) {
    let s = 0;
    for (let i = k * n; i < (k + 1) * n; i++) s += pcm[i] * pcm[i];
    out[k] = Math.sqrt(s / n);
  }
  return out;
}

const median = (a) => {
  if (!a.length) return NaN;
  const b = [...a].sort((x, y) => x - y);
  const m = b.length >> 1;
  return b.length % 2 ? b[m] : 0.5 * (b[m - 1] + b[m]);
};
const dB = (x) => 20 * Math.log10(Math.max(x, 1e-6));

/**
 * Audio onset minus alignment start for every pause-to-speech transition whose first letter is a
 * vowel, nasal or fricative. Seconds. The file start counts as a pause.
 */
export function alignmentBiasSamples(clip, built) {
  const hop = 0.005;
  const rms = rmsSeries(clip.pcm, clip.sr, hop);
  const sorted = [...rms].sort((a, b) => a - b);
  const p95 = sorted[Math.floor(sorted.length * 0.95)] || 0.01;
  const thr = Math.max(0.004, 0.1 * p95);
  const out = [];
  const { spans } = built;
  for (let s = 0; s < spans.length; s++) {
    const sp = spans[s];
    if (sp.kind === 'pause') continue;
    const prev = spans[s - 1];
    const atStart = s === 0;
    if (!atStart && !(prev && prev.kind === 'pause' && prev.t1 - prev.t0 >= 0.1)) continue;
    if (!ONSET_LETTERS.has(sp.letter ?? sp.ch)) continue;
    const from = Math.max(0, Math.floor((sp.t0 - 0.15) / hop));
    const to = Math.min(rms.length - 1, Math.floor((sp.t0 + 0.25) / hop));
    // The window must start quiet, else there was no pause to measure from.
    if (rms[from] > thr && !atStart) continue;
    let k = from;
    while (k <= to && rms[k] <= thr) k++;
    if (k > to) continue;
    out.push((k + 0.5) * hop - sp.t0);
  }
  return out;
}

/**
 * The three validity checks of the plan (7.4). `engineFrames` maps clip name -> analyseBuffer
 * frames (used for the formant order). Returns {pass, bias, checks}.
 */
export function validate(diacClips, engineFrames) {
  const checks = [];
  // 1. Pauses at least 15 dB quieter than letters.
  const letterDb = [];
  const pauseDb = [];
  const biasAll = [];
  const hop = 0.01;
  for (const clip of diacClips) {
    const built = buildSpans(clip, 'diac');
    const rms = rmsSeries(clip.pcm, clip.sr, hop);
    const mean = (t0, t1) => {
      const a = Math.max(0, Math.ceil(t0 / hop));
      const b = Math.min(rms.length - 1, Math.floor(t1 / hop) - 1);
      if (b < a) return null;
      let s = 0;
      for (let k = a; k <= b; k++) s += rms[k] * rms[k];
      return dB(Math.sqrt(s / (b - a + 1)));
    };
    for (const sp of built.spans) {
      if (sp.kind === 'pause') {
        if (sp.t1 - sp.t0 >= 0.12 && sp.punct) {
          const v = mean(sp.t0 + 0.04, sp.t1 - 0.04);
          if (v !== null) pauseDb.push(v);
        }
      } else if (sp.kind === 'cons' || sp.kind === 'vowel') {
        if (sp.t1 - sp.t0 >= 0.04) {
          const v = mean(sp.t0, sp.t1);
          if (v !== null) letterDb.push(v);
        }
      }
    }
    biasAll.push(...alignmentBiasSamples(clip, built));
  }
  const gap = median(letterDb) - median(pauseDb);
  checks.push({
    id: 'pause-vs-letter',
    ok: gap >= 15,
    value: gap,
    text: `pauses are ${gap.toFixed(1)} dB quieter than letters (need >= 15), over ${pauseDb.length} pauses and ${letterDb.length} letter spans`,
  });
  // 2. Formant order on mid-vowel frames.
  const f = { a: { f1: [], f2: [] }, i: { f1: [], f2: [] }, u: { f1: [], f2: [] } };
  for (const clip of diacClips) {
    const built = buildSpans(clip, 'diac');
    const frames = engineFrames.get(clip.name);
    if (!frames) continue;
    const lab = labelFrames(built, frames.length);
    const CLS = ['', 'a', 'i', 'u'];
    for (let n = 0; n < frames.length; n++) {
      if (!lab.isVowelFrame[n]) continue;
      const fr = frames[n];
      const cls = CLS[lab.vclass[n]];
      if (!cls || !(fr.f1 > 0 && fr.f2 > 0) || fr.voicing < 0.5) continue;
      f[cls].f1.push(fr.f1);
      f[cls].f2.push(fr.f2);
    }
  }
  const m = (c, k) => median(f[c][k]);
  const order =
    m('a', 'f1') > m('u', 'f1') && m('a', 'f1') > m('i', 'f1') && m('i', 'f2') > m('a', 'f2') && m('a', 'f2') > m('u', 'f2');
  checks.push({
    id: 'formant-order',
    ok: order,
    value: { a: [m('a', 'f1'), m('a', 'f2')], i: [m('i', 'f1'), m('i', 'f2')], u: [m('u', 'f1'), m('u', 'f2')] },
    text: `median F1/F2 (Hz): a ${m('a', 'f1').toFixed(0)}/${m('a', 'f2').toFixed(0)}, i ${m('i', 'f1').toFixed(0)}/${m('i', 'f2').toFixed(0)}, u ${m('u', 'f1').toFixed(0)}/${m('u', 'f2').toFixed(0)}; need F1(a) > F1(i,u) and F2(i) > F2(a) > F2(u)`,
  });
  // 3. Alignment bias (reported, and used to shift the labels).
  const bias = median(biasAll);
  checks.push({
    id: 'alignment-bias',
    ok: Number.isFinite(bias) && Math.abs(bias) < 0.12,
    value: bias,
    text: `alignment bias (audio onset minus alignment start) median ${(bias * 1000).toFixed(0)} ms over ${biasAll.length} transitions (labels are shifted by it; need |bias| < 120 ms)`,
  });
  return { pass: checks.every((c) => c.ok), bias, checks };
}

/** Bias per variant: the plain clips are timed apart from the diac ones, so each gets its own. */
export function biasFor(clips) {
  const all = [];
  for (const clip of clips) all.push(...alignmentBiasSamples(clip, buildSpans(clip, clip.variant)));
  return { bias: median(all), n: all.length };
}
