// Text to mouth: turns the spoken characters of one reply, with the time each one was spoken (the
// TTS character alignment), into a track of mouth segments. Pure functions, no DOM.
//
// The text has no short vowels, so the track marks a "slot" where one is heard and leaves the
// choice of a, i or u to the audio (timelineTrack.js). Everything the text does know is in the
// track: every م and ب (a lip closure), long vowels, silent letters, pauses, and which letters
// show teeth or a rounded mouth. The letter map is PLAN.md section 3; every number is in
// TIMELINE and ROLE_PARAMS (lipsyncConfig.js).
//
// Input items: [char, startMs, durMs], times from the first audio sample of the reply.
// Output: { segs, onsets, startMs, endMs, lang }.

import { TIMELINE } from './lipsyncConfig.js';
import { VI } from './visemes.js';

/** Segment roles (dominance classes, Cohen and Massaro 1993). Index into ROLE_PARAMS. */
export const ROLE = Object.freeze({ DOM: 0, DOMU: 1, SEMI: 2, REC: 3, VOWEL: 4, SIL: 5, UNK: 6 });

/** Segment kinds. */
export const KIND = Object.freeze({ CONS: 0, VOWEL: 1, SIL: 2, UNK: 3, DIP: 4 });

/** Vowel classes of a vowel segment (same order as arabicVowels.js: a, i, u). */
export const CLS = Object.freeze({ A: 0, I: 1, U: 2 });

const FATHATAN = 'ً';
const DAMMATAN = 'ٌ';
const KASRATAN = 'ٍ';
const FATHA = 'َ';
const DAMMA = 'ُ';
const KASRA = 'ِ';
const SHADDA = 'ّ';
const SUKUN = 'ْ';
const DAGGER = 'ٰ';
const TATWEEL = 'ـ';

const isMark = (c) => (c >= FATHATAN && c <= SUKUN) || c === DAGGER;
const isArabicLetter = (c) => (c >= 'ء' && c <= 'ي') || c === 'ٱ' || c === 'ى';
const isLatin = (c) => (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
const PUNCT = new Set([
  '،', '؛', '؟', '.', ',', '!', '?', ':', ';', '…', '-', '–', '—', '(', ')', '"', '«', '»',
  '\n', '\r',
]);
const isSpace = (c) => c === ' ' || c === ' ' || c === '\t' || c === '‏' || c === '‎' || c === '‌' || c === '‍';

const PREFIX = new Set(['و', 'ف', 'ب', 'ك', 'ل']); // و ف ب ك ل
const EMPHATIC = new Set([...'صضطظقخغ']); // ص ض ط ظ ق خ غ
const STOPS = new Set([...'بتدطضكقءأإؤئ']); // ب ت د ط ض ك ق and hamza

// Consonant letter -> [role, [viseme, weight, ...]]. PLAN.md section 3.
const T = TIMELINE;
const CONS = {};
const put = (letters, role, ...pairs) => {
  for (const ch of letters) CONS[ch] = { role, pairs };
};
put('ب', ROLE.DOM, VI.PP, 1.0); // ب
put('م', ROLE.DOM, VI.PP, 1.0); // م
put('ف', ROLE.DOM, VI.FF, 0.9); // ف
put('سز', ROLE.SEMI, VI.SS, 0.95); // س ز
put('ص', ROLE.SEMI, VI.SS, 0.85); // ص
put('ش', ROLE.SEMI, VI.CH, 0.85, VI.SS, 0.2); // ش
put('ج', ROLE.SEMI, VI.CH, 0.85); // ج
put('ثذ', ROLE.REC, VI.DD, 0.45, VI.FF, 0.15); // ث ذ
put('ظ', ROLE.REC, VI.DD, 0.45, VI.FF, 0.1); // ظ
put('تدطض', ROLE.REC, VI.DD, 0.35); // ت د ط ض
put('نل', ROLE.REC, VI.nn, 0.3); // ن ل
put('ر', ROLE.REC, VI.DD, 0.25); // ر
put('ك', ROLE.REC, VI.kk, 0.3); // ك
put('ق', ROLE.REC, VI.kk, 0.35, VI.aa, 0.15); // ق
put('خغ', ROLE.REC, VI.kk, 0.25, VI.aa, 0.2); // خ غ
put('ع', ROLE.REC, VI.aa, 0.35); // ع
put('ح', ROLE.REC, VI.aa, 0.25); // ح
put('ه', ROLE.REC, VI.aa, 0.2); // ه
put('و', ROLE.DOMU, VI.U, 0.9); // و as a consonant
put('يى', ROLE.SEMI, VI.I, 0.6); // ي as a consonant

const WAW = 'و';
const YA = 'ي';
const ALEF = 'ا';
const ALEF_WASLA = 'ٱ';
const ALEF_MAQSURA = 'ى';
const ALEF_MADDA = 'آ';
const LAM = 'ل';
const TA_MARBUTA = 'ة';
const HAMZA_SEATS = { 'ء': -1, 'أ': CLS.A, 'إ': CLS.I, 'ؤ': CLS.U, 'ئ': CLS.I };
const MARK_VOWEL = {
  [FATHA]: CLS.A, [FATHATAN]: CLS.A, [KASRA]: CLS.I, [KASRATAN]: CLS.I, [DAMMA]: CLS.U, [DAMMATAN]: CLS.U,
};

const VOWEL_VI = [VI.aa, VI.I, VI.U];

function makeSeg(t0, t1, role, kind) {
  return {
    t0,
    t1,
    role,
    kind,
    target: null, // Float32Array(14) for a consonant, else null
    base: 0, // vowel: weight before the loudness law
    cls: CLS.A, // vowel: the class shown now (a slot starts on the prior and follows the audio)
    slot: false, // vowel whose identity comes from the audio
    votes: null, // slot: the audio's votes for a, i, u (set when the slot is created)
    emph: false, // next to an emphatic consonant
    bilab: false, // a closure: PP is held at the floor inside the span
    labio: false, // an FF consonant
    minHold: 0,
    stop: false,
    ch: '',
  };
}

function consTarget(pairs, scale = 1) {
  const t = new Float32Array(14);
  for (let i = 0; i < pairs.length; i += 2) t[pairs[i]] = pairs[i + 1] * scale;
  return t;
}

/**
 * Group the items into tokens: a letter with the marks after it, a space, punctuation, a Latin
 * letter or something else. Times in ms.
 */
function tokenise(items) {
  const toks = [];
  let last = null;
  for (const it of items) {
    const ch = String(it[0]);
    const t0 = +it[1] || 0;
    const t1 = t0 + Math.max(0, +it[2] || 0);
    if (ch === TATWEEL) continue;
    if (isMark(ch)) {
      if (last && last.type === 'ar') {
        if (ch === SHADDA) last.shadda = true;
        else if (ch === SUKUN) last.sukun = true;
        else if (ch === DAGGER) last.dagger = true;
        else {
          last.vowel = MARK_VOWEL[ch];
          if (ch === FATHATAN || ch === DAMMATAN || ch === KASRATAN) last.tanween = true;
        }
        last.t1 = Math.max(last.t1, t1);
      }
      continue;
    }
    let type = 'unk';
    if (isSpace(ch)) type = 'space';
    else if (PUNCT.has(ch)) type = 'punct';
    else if (isArabicLetter(ch) || ch === ALEF_MADDA) type = 'ar';
    else if (isLatin(ch)) type = 'lat';
    last = { type, ch, t0, t1, vowel: undefined, shadda: false, sukun: false, dagger: false, tanween: false };
    toks.push(last);
  }
  return toks;
}

/**
 * @param {Array<[string, number, number]>} items characters with start and duration in ms
 * @param {{lang?: 'ar'|'en'}} [opts] 'en' keeps the labials only (everything else is left to the audio)
 */
export function buildTrack(items, { lang = 'ar' } = {}) {
  const toks = tokenise(items);
  const segs = [];
  const arabic = lang !== 'en';
  let seenSound = false; // for the utterance-initial alef

  // Split into words (runs of letters) and separators.
  let i = 0;
  while (i < toks.length) {
    const tk = toks[i];
    if (tk.type === 'space' || tk.type === 'punct') {
      const dur = tk.t1 - tk.t0;
      if (tk.type === 'punct' ? dur >= 40 : dur >= T.pauseMs) {
        const s = makeSeg(tk.t0, tk.t1, ROLE.SIL, KIND.SIL);
        segs.push(s);
      }
      i++;
      continue;
    }
    let j = i;
    while (j < toks.length && toks[j].type !== 'space' && toks[j].type !== 'punct') j++;
    const word = toks.slice(i, j);
    const after = j < toks.length ? toks[j] : null; // the separator after the word, if any
    const beforePause = !after || after.type === 'punct';
    wordSegments(word, beforePause, arabic, !seenSound, segs);
    if (segs.length) seenSound = true;
    i = j;
  }

  finish(segs);
  const first = segs.find((s) => s.kind !== KIND.SIL);
  const lastSeg = segs.length ? segs[segs.length - 1] : null;
  const startMs = first ? first.t0 : 0;
  const endMs = lastSeg ? Math.max(...segs.map((s) => s.t1)) : 0;
  return { segs, onsets: expectedOnsets(segs), startMs, endMs, lang: arabic ? 'ar' : 'en', startsClosed: !!(first && first.bilab) };
}

/** True when word[k] is read as a long vowel (alef, or an unmarked waw or ya after a consonant). */
function isLongAt(word, k) {
  const tk = word[k];
  if (!tk || tk.type !== 'ar') return false;
  const ch = tk.ch;
  if (ch === ALEF_MAQSURA || ch === ALEF_MADDA) return true;
  if (ch === ALEF) return k > 0;
  if (ch === WAW || ch === YA) {
    const next = word[k + 1];
    return k > 0 && tk.vowel === undefined && !tk.shadda && !tk.sukun && !(next && next.ch === ALEF);
  }
  return false;
}

/** The mouth segments of one word. */
function wordSegments(word, beforePause, arabic, utteranceStart, out) {
  // Latin words: labials only.
  if (word.length && word[0].type !== 'ar') {
    latinSegments(word, out);
    return;
  }
  // Arabic words: any non-Arabic token in the middle becomes an unknown span.
  const n = word.length;
  const emphAt = (k) => k >= 0 && k < n && word[k].type === 'ar' && EMPHATIC.has(word[k].ch);
  for (let k = 0; k < n; k++) {
    const tk = word[k];
    if (tk.type !== 'ar') {
      pushUnknown(out, tk.t0, tk.t1);
      continue;
    }
    const ch = tk.ch;
    const span = tk.t1 - tk.t0;
    const prev = k > 0 ? word[k - 1] : null;
    const next = k + 1 < n ? word[k + 1] : null;
    const nextIsLong = isLongAt(word, k + 1);
    const emphNear = emphAt(k - 1) || emphAt(k + 1);

    // Alef (long a), with the silent cases.
    if (ch === ALEF || ch === ALEF_WASLA || ch === ALEF_MADDA || ch === ALEF_MAQSURA) {
      if (ch === ALEF_MADDA) {
        pushVowel(out, tk.t0, tk.t1, CLS.A, T.longA, false, emphNear);
        continue;
      }
      const article = (k === 0 && next && next.ch === LAM) || (k === 1 && PREFIX.has(word[0].ch) && next && next.ch === LAM);
      if (ch !== ALEF_MAQSURA && article) {
        if (k === 0 && utteranceStart) pushVowel(out, tk.t0, tk.t1, CLS.A, T.markA, false, emphNear);
        // else the wasla alef is silent: no shape, its time goes to the neighbours
        continue;
      }
      if (ch === ALEF && prev && prev.ch === WAW && prev.vowel === undefined && !prev.shadda && k === n - 1) continue; // a silent final alef
      if (ch === ALEF_WASLA || (ch === ALEF && k === 0)) {
        // A written mark on a first alef (kasra or damma) gives the vowel it says; else a.
        const mc = tk.vowel !== undefined ? tk.vowel : CLS.A;
        pushVowel(out, tk.t0, tk.t1, mc, mc === CLS.A ? T.markA : mc === CLS.I ? T.markI : T.markU, false, emphNear);
        continue;
      }
      pushVowel(out, tk.t0, tk.t1, CLS.A, T.longA, false, emphNear);
      continue;
    }

    // Waw and ya: a consonant, or a long vowel when they carry no mark and follow a consonant.
    if ((ch === WAW || ch === YA) && isLongAt(word, k)) {
      pushVowel(out, tk.t0, tk.t1, ch === WAW ? CLS.U : CLS.I, ch === WAW ? T.longU : T.longI, false, emphNear);
      continue;
    }

    // Ta marbuta: silent before a pause, else a soft t and a vowel.
    if (ch === TA_MARBUTA) {
      if (beforePause && k === n - 1) continue;
      pushConsonant(out, tk, ch, emphNear);
      continue;
    }

    // Hamza and its seats: a short dip, then the vowel the seat tells.
    if (ch in HAMZA_SEATS) {
      const seat = HAMZA_SEATS[ch];
      const dip = Math.min(T.hamzaMaxMs, Math.max(T.hamzaMinMs, 0.4 * span));
      const d = makeSeg(tk.t0, Math.min(tk.t1, tk.t0 + dip), ROLE.REC, KIND.DIP);
      d.target = new Float32Array(14);
      out.push(d);
      const known = tk.vowel;
      const slotStart = d.t1;
      if (seat >= 0 || known !== undefined) {
        const cls = known !== undefined ? known : seat;
        if (tk.t1 - slotStart >= T.slotMinMs) {
          pushVowel(out, slotStart, tk.t1, cls, known !== undefined ? markBase(cls) : T.slotWeight, known === undefined, emphNear);
        }
      }
      continue;
    }

    // An ordinary consonant, then its vowel slot.
    const info = CONS[ch];
    if (!info) {
      pushUnknown(out, tk.t0, tk.t1);
      continue;
    }
    pushConsonantAndSlot(out, tk, ch, info, { next, nextIsLong, beforePause, last: k === n - 1, emphNear });
  }
}

const markBase = (cls) => (cls === CLS.A ? T.markA : cls === CLS.I ? T.markI : T.markU);

function pushConsonantAndSlot(out, tk, ch, info, ctx) {
  const span = Math.max(1, tk.t1 - tk.t0);
  const { next, nextIsLong, beforePause, last, emphNear } = ctx;
  const bilab = ch === 'ب' || ch === 'م';
  const geminate = tk.shadda;
  const minHold = bilab ? (ch === 'م' ? T.mMinMs : T.bMinMs) * (geminate ? T.shaddaHold : 1) : 0;

  // Does a short vowel follow this consonant?
  let slot = false;
  let slotCls = CLS.A;
  let fixedVowel = false;
  if (tk.vowel !== undefined) {
    slot = true;
    slotCls = tk.vowel;
    fixedVowel = true;
  } else if (!tk.sukun) {
    const nextIsConsonant = next && next.type === 'ar' && !nextIsLong;
    if (nextIsConsonant) slot = true;
    else if (last) slot = !beforePause && span >= T.finalSlotMinMs;
  }

  // A long vowel letter follows: the mouth starts to take its shape before the letter itself
  // (the time of the short vowel mark the text does not carry belongs to it).
  let leadCls = -1;
  if (!slot && nextIsLong && !tk.sukun && !tk.shadda && next && next.type === 'ar') {
    leadCls = next.ch === WAW ? CLS.U : next.ch === YA ? CLS.I : CLS.A;
  }

  let consEnd = tk.t1;
  let slotStart = tk.t1;
  if (leadCls >= 0) {
    const frac = bilab ? Math.max(T.slotConsFrac * span, minHold) : T.slotConsFrac * span;
    const consPart = Math.min(bilab ? T.bilabMaxMs : T.slotConsMaxMs, Math.max(bilab ? minHold : T.slotConsMinMs, frac));
    if (span - consPart >= T.slotMinMs) {
      consEnd = tk.t0 + consPart;
      slotStart = consEnd;
    } else {
      leadCls = -1;
    }
  } else if (slot && !(nextIsLong && !fixedVowel)) {
    const frac = bilab ? Math.max(T.slotConsFrac * span, minHold) : T.slotConsFrac * span;
    const consPart = Math.min(bilab ? T.bilabMaxMs : T.slotConsMaxMs, Math.max(bilab ? minHold : T.slotConsMinMs, frac));
    if (span - consPart >= T.slotMinMs) {
      consEnd = tk.t0 + consPart;
      slotStart = consEnd;
    } else {
      slot = false;
    }
  } else {
    slot = false;
  }

  const s = makeSeg(tk.t0, consEnd, info.role, KIND.CONS);
  s.target = consTarget(info.pairs);
  s.ch = ch;
  s.stop = STOPS.has(ch);
  if (bilab) {
    s.bilab = true;
    s.minHold = minHold;
  }
  if (ch === 'ف') {
    s.labio = true;
    s.minHold = T.ffMinMs;
  }
  out.push(s);
  if (leadCls >= 0) pushVowel(out, slotStart, tk.t1, leadCls, T.leadVowelWeight, false, emphNear);
  if (slot) {
    pushVowel(out, slotStart, tk.t1, slotCls, fixedVowel ? markBase(slotCls) : T.slotWeight, !fixedVowel, emphNear);
    if (tk.tanween) {
      const nt0 = slotStart + 0.6 * (tk.t1 - slotStart);
      const nn = makeSeg(nt0, tk.t1, ROLE.REC, KIND.CONS);
      nn.target = consTarget([VI.nn, 0.3]);
      out.push(nn);
    }
  }
}

function pushConsonant(out, tk, ch, emphNear) {
  const span = Math.max(1, tk.t1 - tk.t0);
  const s = makeSeg(tk.t0, tk.t0 + Math.min(span, T.slotConsMaxMs), ROLE.REC, KIND.CONS);
  s.target = consTarget([VI.DD, 0.35]);
  s.ch = ch;
  out.push(s);
  if (span - (s.t1 - s.t0) >= T.slotMinMs) pushVowel(out, s.t1, tk.t1, CLS.A, T.slotWeight, true, emphNear);
}

function pushVowel(out, t0, t1, cls, base, slot, emph) {
  const s = makeSeg(t0, Math.max(t1, t0 + 1), ROLE.VOWEL, KIND.VOWEL);
  s.cls = cls;
  s.base = base;
  s.slot = slot;
  if (slot) s.votes = new Float32Array(3);
  s.emph = !!emph;
  out.push(s);
  return s;
}

function pushUnknown(out, t0, t1) {
  const last = out[out.length - 1];
  if (last && last.kind === KIND.UNK && t0 - last.t1 < 30) {
    last.t1 = Math.max(last.t1, t1);
    return;
  }
  out.push(makeSeg(t0, Math.max(t1, t0 + 1), ROLE.UNK, KIND.UNK));
}

/** Latin letters: b m p close the lips, f v show the teeth, w rounds, the rest is left to the audio. */
function latinSegments(word, out) {
  const n = word.length;
  for (let k = 0; k < n; k++) {
    const tk = word[k];
    if (tk.type !== 'lat') {
      pushUnknown(out, tk.t0, tk.t1);
      continue;
    }
    const c = tk.ch.toLowerCase();
    const next = k + 1 < n ? word[k + 1].ch.toLowerCase() : '';
    const prev = k > 0 ? word[k - 1].ch.toLowerCase() : '';
    const span = Math.max(1, tk.t1 - tk.t0);
    if (c === 'p' && next === 'h') {
      // "ph" says f: show the teeth on the p and give the h no shape of its own.
      pushLatin(out, tk, 'f', span);
      continue;
    }
    if (c === 'h' && prev === 'p') {
      pushUnknown(out, tk.t0, tk.t1);
      continue;
    }
    if (c === 'b' && prev === 'm' && k === n - 1) {
      pushUnknown(out, tk.t0, tk.t1); // a silent final b ("lamb")
      continue;
    }
    if (c === 'b' || c === 'm' || c === 'p' || c === 'f' || c === 'v' || c === 'w') pushLatin(out, tk, c, span);
    else pushUnknown(out, tk.t0, tk.t1);
  }
}

function pushLatin(out, tk, c, span) {
  const closure = c === 'b' || c === 'm' || c === 'p';
  const part = Math.min(span, closure ? Math.min(T.bilabMaxMs, Math.max(T.bMinMs, T.slotConsFrac * span)) : Math.max(T.slotConsMinMs, T.slotConsFrac * span));
  const s = makeSeg(tk.t0, tk.t0 + part, closure ? ROLE.DOM : c === 'w' ? ROLE.DOMU : ROLE.DOM, KIND.CONS);
  if (closure) {
    s.target = consTarget([VI.PP, 1]);
    s.bilab = true;
    s.minHold = T.bMinMs;
  } else if (c === 'w') {
    s.target = consTarget([VI.U, 0.9]);
  } else {
    s.target = consTarget([VI.FF, 0.9]);
    s.labio = true;
    s.minHold = T.ffMinMs;
  }
  s.ch = c;
  out.push(s);
  if (span - part > 20) pushUnknown(out, s.t1, tk.t1);
}

/** Close small gaps, widen short closures, damp short and crowded vowels. */
function finish(segs) {
  segs.sort((a, b) => a.t0 - b.t0 || a.t1 - b.t1);
  // Gaps under 100 ms are not pauses: split them between the neighbours.
  for (let k = 0; k + 1 < segs.length; k++) {
    const a = segs[k];
    const b = segs[k + 1];
    const gap = b.t0 - a.t1;
    if (gap > 0 && gap < T.pauseMs && a.kind !== KIND.SIL && b.kind !== KIND.SIL) {
      const mid = 0.5 * (a.t1 + b.t0);
      a.t1 = mid;
      b.t0 = mid;
    }
  }
  for (const s of segs) {
    if (s.minHold > 0 && s.t1 - s.t0 < s.minHold) {
      const c = 0.5 * (s.t0 + s.t1);
      s.t0 = c - 0.5 * s.minHold;
      s.t1 = c + 0.5 * s.minHold;
    }
  }
  segs.sort((a, b) => a.t0 - b.t0 || a.t1 - b.t1);
  // Natural undershoot: very short vowels do not reach the full pose, and fast speech
  // under-articulates (more than fastCount vowels inside one second).
  const vowels = segs.filter((s) => s.kind === KIND.VOWEL);
  for (let k = 0; k < vowels.length; k++) {
    const v = vowels[k];
    v.scale = 1;
    if (v.t1 - v.t0 < T.undershootMs) v.scale *= T.undershoot;
    let count = 0;
    for (let m = k; m >= 0 && v.t0 - vowels[m].t0 < 1000; m--) count++;
    if (count > T.fastCount) v.scale *= T.fast;
  }
  for (const s of segs) if (s.scale === undefined) s.scale = 1;
}

/**
 * The moments speech is expected to start after silence: the first sound of the track and the
 * first sound after every pause. Stops get a small delay (the burst comes after the closure).
 * @returns {number[]} ms, ascending
 */
function expectedOnsets(segs) {
  const out = [];
  let afterSil = true;
  for (const s of segs) {
    if (s.kind === KIND.SIL) {
      afterSil = true;
      continue;
    }
    if (afterSil) {
      out.push(s.t0 + (s.stop ? Math.min(0.5 * (s.t1 - s.t0), T.stopOnsetMaxMs) : 0));
      afterSil = false;
    }
  }
  return out;
}

export { VOWEL_VI };
