// Short-vowel identity for Arabic from the sound alone: three classes (a, i, u) decided from the
// median of the last few raw per-frame F1 and F2 values.
//
// Arabic writing leaves the short vowels out, and the English five-vowel prototypes of the
// classifier read fatha as E. Here the rule is "a unless the audio clearly says i or u":
//   i  a high front vowel: F2 above `f2i` and F1 below `f1i`
//   u  a high back, rounded vowel: F2 below `f2u` and F1 below `f1u`
//   a  everything else (fatha is the commonest vowel, about 70 percent of vowel frames)
// Thresholds live in lipsyncConfig.js (ARABIC). No allocation per call.

import { ARABIC } from './lipsyncConfig.js';

export const VOWEL_A = 0;
export const VOWEL_I = 1;
export const VOWEL_U = 2;

const MAX_WINDOW = 7;

const median3 = (a, b, c) => (a < b ? (b < c ? b : a < c ? c : a) : a < c ? a : b < c ? c : b);

function medianOf(buf, n) {
  if (n === 1) return buf[0];
  if (n === 2) return 0.5 * (buf[0] + buf[1]);
  if (n === 3) return median3(buf[0], buf[1], buf[2]);
  // Rare path (a larger window was configured): sort a small copy.
  const tmp = Array.prototype.slice.call(buf, 0, n).sort((x, y) => x - y);
  return tmp[n >> 1];
}

export class ArabicVowelRule {
  constructor(cfg = ARABIC) {
    this.cfg = cfg;
    this.f1 = new Float32Array(MAX_WINDOW);
    this.f2 = new Float32Array(MAX_WINDOW);
    this.reset();
  }

  reset() {
    this.n = 0; // frames held
    this.head = 0;
    this.cls = VOWEL_A;
    this.medF1 = 0;
    this.medF2 = 0;
  }

  /**
   * Feed one voiced frame's raw formants. A frame with no formants (f1 or f2 not above 0) is
   * skipped and the previous class stays.
   * @returns {number} VOWEL_A, VOWEL_I or VOWEL_U
   */
  push(f1, f2) {
    if (!(f1 > 0 && f2 > 0)) return this.cls;
    const size = Math.min(MAX_WINDOW, Math.max(1, this.cfg.medianFrames | 0));
    this.f1[this.head] = f1;
    this.f2[this.head] = f2;
    this.head = (this.head + 1) % size;
    if (this.n < size) this.n++;
    // Ring buffers hold the newest `n` values in slots 0..n-1 (order does not matter for a median).
    const m1 = medianOf(this.f1, this.n);
    const m2 = medianOf(this.f2, this.n);
    this.medF1 = m1;
    this.medF2 = m2;
    const c = this.cfg;
    this.cls = m2 > c.f2i && m1 < c.f1i ? VOWEL_I : m2 < c.f2u && m1 < c.f1u ? VOWEL_U : VOWEL_A;
    return this.cls;
  }
}
