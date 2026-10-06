// Samples a text track (arabicText.js buildTrack) at one moment: the 14 mouth weights the text
// asks for, blended the way real articulators overlap (Cohen and Massaro 1993, dominance
// functions), then two hard rules a lip closure and a labiodental need to read as such.
//
// Nothing here allocates: the caller owns `out` (Float32Array(14)), the sampler owns two scratch
// arrays. The audio gives two things the text cannot: which short vowel a slot is (a, i or u), and
// how loud the syllable is (ARABIC.ampBase..ampCurve, the same law as the audio-only mode).

import { ARABIC, TIMELINE } from './lipsyncConfig.js';
import { CLS, KIND, ROLE } from './arabicText.js';
import { VI, VISEME_COUNT } from './visemes.js';

const T = TIMELINE;
const VOWEL_VI = [VI.aa, VI.I, VI.U];

export class TrackSampler {
  constructor(track = null) {
    this.num = new Float32Array(VISEME_COUNT);
    this.unk = 0; // after sample(): 0..1, how much of this moment is an unknown span (use the audio)
    this.cursor = 0;
    this.track = null;
    this.leadMs = T.leadMs;
    if (track) this.setTrack(track);
  }

  setTrack(track) {
    this.track = track;
    this.cursor = 0;
  }

  /**
   * @param {number} tauMs where the audio is in the track now (the lead is added here)
   * @param {number} vowelClass the vowel class the audio is showing (CLS.A/I/U), or -1 when the
   *   voice is silent or not voiced
   * @param {number} level 0..1 loudness against the recent peak
   * @param {Float32Array} out receives the 14 weights (sil, index 0, is left to the smoother)
   * @returns {Float32Array} out
   */
  sample(tauMs, vowelClass, level, out) {
    out.fill(0);
    this.unk = 0;
    const track = this.track;
    if (!track || !track.segs.length) return out;
    const segs = track.segs;
    const tShow = tauMs + this.leadMs;
    // Vowels are shown a little later than consonants: the lips close and round ahead of the sound,
    // but a vowel's colour is only known once the audio has said it (a slot), and showing it early
    // puts the next consonant's shape on the vowel the child is hearing.
    const vLead = this.leadMs - (T.leadMs - T.vowelLeadMs);
    const tVowel = tauMs + (vLead > T.leadMinMs ? vLead : T.leadMinMs);
    const win = T.windowMs;
    const tLow = (tVowel < tShow ? tVowel : tShow) - win;

    // Move the cursor to the first segment that can still matter.
    let lo = this.cursor;
    if (lo >= segs.length) lo = segs.length - 1;
    while (lo > 0 && segs[lo - 1].t1 > tLow) lo--;
    while (lo < segs.length - 1 && segs[lo].t1 < tLow) lo++;
    this.cursor = lo;

    const num = this.num;
    num.fill(0);
    let den = T.background;
    let unk = 0;
    const amp = clamp01(ARABIC.ampBase + ARABIC.ampSpan * Math.pow(level < 0 ? 0 : level > 1 ? 1 : level, ARABIC.ampCurve));
    let ppStrength = 0;
    let ffStrength = 0;
    const shrink = T.closureShrinkMs;

    for (let k = lo; k < segs.length; k++) {
      const s = segs[k];
      if (s.t0 > tShow + win) break;
      // The slot learns its vowel from the audio: the class heard in the part of the slot the sound
      // has reached (tauMs is where the sound is, not where the mouth is).
      if (s.slot && vowelClass >= 0 && tauMs >= s.t0 + T.slotListenMs && tauMs <= s.t1 + T.slotListenEndMs) {
        const v = s.votes;
        v[vowelClass] += 0.2 + level;
        s.cls = v[1] > v[0] && v[1] >= v[2] ? CLS.I : v[2] > v[0] && v[2] > v[1] ? CLS.U : CLS.A;
      }

      const tAt = s.kind === KIND.VOWEL ? tVowel : tShow;
      const dBefore = s.t0 - tAt;
      const dAfter = tAt - s.t1;
      const r = s.role;
      let d;
      if (dBefore > 0) d = Math.exp(-dBefore / T.thetaBefore[r]);
      else if (dAfter > 0) d = Math.exp(-dAfter / T.thetaAfter[r]);
      else d = 1;

      if (s.kind === KIND.UNK) {
        // Weight 1 inside, fading out over unknownFadeMs on both sides.
        const dist = dBefore > 0 ? dBefore : dAfter > 0 ? dAfter : 0;
        const u = Math.exp(-dist / T.unknownFadeMs);
        if (u > unk) unk = u;
        // It takes part in the competition (no shape of its own: the audio draws it), so a closure beside it does not
        // start early.
        den += T.alpha[r] * d;
        continue;
      }
      const dom = T.alpha[r] * d;
      if (dom < 1e-4) continue;
      den += dom;
      if (s.kind === KIND.SIL) continue;
      if (s.kind === KIND.CONS) {
        const tg = s.target;
        for (let i = 1; i < VISEME_COUNT; i++) if (tg[i] > 0) num[i] += dom * tg[i];
        if (s.bilab && tShow >= s.t0 + shrink && tShow <= Math.max(s.t1, s.t0 + T.closureHoldMs) - shrink) ppStrength = 1;
        if (s.labio && tShow >= s.t0 + shrink && tShow <= Math.max(s.t1, s.t0 + T.labioHoldMs) - shrink) ffStrength = 1;
      } else if (s.kind === KIND.VOWEL) {
        const w = s.base * s.scale * amp;
        const vi = VOWEL_VI[s.cls];
        let ww = w;
        if (s.emph && s.cls === CLS.A) ww = Math.min(1, w * T.emphA);
        num[vi] += dom * ww;
        if (s.emph) num[VI.O] += dom * T.emphO * (s.cls === CLS.A ? 1 : 0.5);
      }
    }

    const inv = 1 / den;
    let sum = 0;
    for (let i = 1; i < VISEME_COUNT; i++) {
      const v = num[i] * inv;
      out[i] = v;
      sum += v;
    }
    // A weight above 1 cannot be shown; keep the total at most 1.
    if (sum > 1) {
      const sc = 1 / sum;
      for (let i = 1; i < VISEME_COUNT; i++) out[i] *= sc;
    }

    // Hard rules: a closure reads as a closure only if the lips are really together, a
    // labiodental only with the teeth showing.
    if (ppStrength > 0) enforce(out, VI.PP, T.ppFloor);
    else if (ffStrength > 0) enforce(out, VI.FF, T.ffFloor);

    // Inside a closure or a labiodental the text is sure: the audio share of a neighbouring unknown
    // span (an English letter next to the b, m, p or f) must not pull the lips apart again.
    this.unk = ppStrength > 0 || ffStrength > 0 ? 0 : unk;
    return out;
  }
}

/** Raise out[vi] to at least `floor`, scale the others so the total stays at most 1. */
function enforce(out, vi, floor) {
  if (out[vi] < floor) out[vi] = floor;
  let others = 0;
  for (let i = 1; i < VISEME_COUNT; i++) if (i !== vi) others += out[i];
  const room = 1 - out[vi];
  if (others > room) {
    const sc = others > 0 ? Math.max(0, room) / others : 0;
    for (let i = 1; i < VISEME_COUNT; i++) if (i !== vi) out[i] *= sc;
  }
}

const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);

export { ROLE };
