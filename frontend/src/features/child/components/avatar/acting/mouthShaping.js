// Mouth shaping [MB 6.1-6.5]: turns the lip-sync's shown viseme weights into (a) a jaw angle and
// (b) the morph weights that are actually written. Pure math, no three.js and no audio.
//
//   jaw     = the main lever: 0.50 rad at full open, about 2.25 cm of chin travel on this rig.
//   morphs  = shown x gain, capped per viseme, with an open budget so a wide jaw and a wide aa
//             never stack into a black slot. Closures (PP, FF, SS) are never amplified.
//   gates   = PP clamps the jaw so the lips can seal; FF bites; a speech floor keeps the mouth
//             alive between words.
//
// The audio-only path (no text timeline) can add the vowel and stress holds and the mass lift of
// [MB 6.3-6.5]; the text timeline path leaves them off (see AUDIO_PATH.massLift and `audioPath`).

import { VI, VISEME_COUNT } from '../lipsync/visemes.js';
import { AUDIO_PATH, JAW_STUDIO, MORPH_GAIN, MOUTH_SLEW, OPEN_BUDGET, TIMED_PATH } from './actingConfig.js';
import { clamp, damp } from './dynamics.js';

const VOWEL_IDX = [VI.aa, VI.E, VI.I, VI.O, VI.U];
const CONSONANT_IDX = [VI.FF, VI.DD, VI.kk, VI.CH, VI.SS, VI.nn, VI.RR];
const NAMES = Object.keys(VI);
const OPEN_BY_INDEX = NAMES.map((name) => JAW_STUDIO.open[name] ?? 0);
const FLOOR = 1e-4;
const SEAL_FROM = 0.5; // PP at or above this is a seal (timed snap 0.97, audio hold 0.9)

export class MouthShaper {
  /**
   * @param {object} [opts]
   * @param {1|2} [opts.version] mesh version: 1 today, 2 after WP5
   * @param {boolean} [opts.audioPath] true when no text timeline drives the weights (audio holds on)
   * @param {object} [opts.jaw] overrides for JAW_STUDIO
   * @param {object} [opts.audio] overrides for AUDIO_PATH
   * @param {object} [opts.timed] overrides for TIMED_PATH
   */
  constructor({ version = 1, audioPath = false, jaw, audio, timed } = {}) {
    this.version = version === 2 ? 2 : 1;
    this.audioPath = audioPath;
    this.jawCfg = { ...JAW_STUDIO, ...jaw };
    this.audio = { ...AUDIO_PATH, ...audio };
    this.timed = { ...TIMED_PATH, ...timed };
    this.morph = new Float32Array(VISEME_COUNT); // what to write to the viseme morphs
    this.prevOut = new Float32Array(VISEME_COUNT); // last frame's written weights (the rise limit)
    this.ppShown = 0; // the PP weight after the release limit
    this.work = new Float32Array(VISEME_COUNT);
    this.jaw = 0; // rad, damped
    this.jawOpen = 0; // 0..1 target before damping (for the dev page)
    this.sinceSpeech = 99; // seconds since speech was last active
    this.holdVowel = -1; // index of the vowel being held
    this.holdLeft = 0;
    this.holdLevel = 0;
    this.stressHoldLeft = 0;
    this.stressPeak = 0;
    this.stressPeakIdx = -1;
    this.ppHoldLeft = 0;
    this.ppSeal = 0; // seconds the current timed closure has lasted (0 = open)
    this.lastVowel = -1; // dominant vowel last frame
    this.lastVowelW = 0;
    this.mass = 1;
    this.ppJawMorph = 0; // 0..1 for the PP_jaw corrective morph (V2 only, if the GLB carries it)
    this.levelSmooth = 0; // the loudness after light smoothing, so noise does not shake the jaw
  }

  setVersion(version) {
    this.version = version === 2 ? 2 : 1;
  }

  /** The jaw angle PP is allowed to reach for this mesh version. */
  get ppJaw() {
    return this.version === 2 ? this.jawCfg.ppJawV2 : this.jawCfg.ppJawV1;
  }

  reset() {
    this.jaw = 0;
    this.jawOpen = 0;
    this.morph.fill(0);
    this.prevOut.fill(0);
    this.ppShown = 0;
    this.sinceSpeech = 99;
    this.holdLeft = 0;
    this.stressHoldLeft = 0;
    this.ppHoldLeft = 0;
    this.ppSeal = 0;
    this.levelSmooth = 0;
  }

  /**
   * @param {number} dt seconds
   * @param {ArrayLike<number>} shown the 14 weights the lip-sync would show (already smoothed)
   * @param {{level?: number, stress?: number, speaking?: boolean, active?: boolean}} [ctx]
   *   level 0..1 loudness; stress 0..1; speaking = a clip is playing; active = voiced right now
   * @returns {Float32Array} morph weights; read .jaw (rad) and .jawOpen after the call
   */
  update(dt, shown, { level = 1, stress = 0, speaking = false, active = false } = {}) {
    const j = this.jawCfg;
    const w = this.work;
    for (let i = 0; i < VISEME_COUNT; i++) w[i] = shown[i] || 0;

    if (active) this.sinceSpeech = 0;
    else this.sinceSpeech += dt;

    if (this.audioPath) this.audioShaping(dt, w, stress);
    else this.timedShaping(dt, w);
    // A closure snaps on but lets go over a few frames: PP never falls faster than MOUTH_SLEW.ppFall per second.
    const ppFloor = this.ppShown - Math.min(MOUTH_SLEW.ppFall * dt, MOUTH_SLEW.maxStep);
    if (w[VI.PP] < ppFloor) w[VI.PP] = ppFloor;
    this.ppShown = w[VI.PP];
    this.fitToClosure(w);

    // ---- jaw target ----
    let want = 0;
    for (let i = 0; i < VISEME_COUNT; i++) want += w[i] * OPEN_BY_INDEX[i];
    want = clamp(want, 0, 1);
    this.levelSmooth = damp(this.levelSmooth, clamp(level, 0, 1), j.levelRate, dt);
    want *= 1 - j.levelCouple + j.levelCouple * this.levelSmooth;
    const pp = w[VI.PP];
    want *= 1 - j.ffBite * clamp(w[VI.FF], 0, 1);
    want *= 1 - this.chew(w);
    want *= 1 - clamp(pp, 0, 1); // [MB 6.1] jaw x (1 - PP) x (1 - 0.6 FF)
    this.jawOpen = want;
    let wantRad = want * j.max;

    // Speech floor: the mouth never fully shuts inside a phrase unless PP closes it.
    const inSpeech = speaking && (active || this.sinceSpeech < j.speechGap);
    if (inSpeech && pp < j.ppGateAt) wantRad = Math.max(wantRad, j.speechFloor);

    // ---- damp, then the PP gate (a hard clamp: the lips must seal on the frame PP arrives) ----
    const rate = wantRad > this.jaw ? j.attack : j.release;
    const jawBefore = this.jaw;
    this.jaw = damp(this.jaw, wantRad, rate, dt);
    // Speed limit (before the PP gate, which may still shut the jaw at once so the lips seal).
    const rise = Math.min(j.openSpeed * dt, MOUTH_SLEW.jawMaxStep);
    const fall = Math.min(j.closeSpeed * dt, MOUTH_SLEW.jawMaxStep);
    if (this.jaw > jawBefore + rise) this.jaw = jawBefore + rise;
    else if (this.jaw < jawBefore - fall) this.jaw = jawBefore - fall;
    const preGate = this.jaw;
    const gateFrom = j.ppGateAt - j.ppGateLead;
    if (pp > gateFrom) {
      const gate = this.ppJaw;
      // [MB 6.1] While PP >= ppGateAt the jaw is at most ppJaw (any more tears the V1 lower lip).
      // The clamp fades in over PP gateFrom..ppGateAt so a rising PP closes the jaw over a few frames
      // instead of one (a closure that arrives as 0.2 then 0.67 would otherwise pop the chin 4.7 cm).
      const f = clamp((pp - gateFrom) / (j.ppGateAt - gateFrom), 0, 1);
      const clamped = Math.min(this.jaw, gate);
      this.jaw += (clamped - this.jaw) * f;
    }
    // V2 mesh (it has the PP_jaw corrective): the gate drops the jaw in a frame or two; let the chin settle over about
    // 25 ms instead (a stepped jaw is a flutter once a few closures follow each other). It stays within gateSlack of
    // the gate, and the corrective morph below seals the lips for the angle that is left. V1 keeps the hard gate.
    if (this.version === 2 && this.jaw < preGate) {
      const settled = preGate - (preGate - this.jaw) * (1 - Math.exp(-MOUTH_SLEW.gateRate * dt));
      this.jaw = Math.min(settled, this.jaw + MOUTH_SLEW.gateSlack);
      if (pp < 0.6 && this.jaw < jawBefore - MOUTH_SLEW.jawMaxStep) this.jaw = jawBefore - MOUTH_SLEW.jawMaxStep;
    }
    if (this.jaw < FLOOR) this.jaw = 0;

    // ---- morph weights: gain, cap, open budget ----
    const table = MORPH_GAIN[this.version];
    const budget = OPEN_BUDGET[this.version];
    const out = this.morph;
    for (let i = 0; i < VISEME_COUNT; i++) {
      const pair = table[NAMES[i]];
      let v = w[i] * pair[0];
      let cap = pair[1];
      if (i === VI.aa || i === VI.O) cap = Math.min(cap, budget[NAMES[i]] - this.jaw / j.budgetRef);
      if (v > cap) v = cap;
      out[i] = v < FLOOR ? 0 : v;
    }
    // Nothing but a closure rises by more than MOUTH_SLEW.riseRate per second.
    const maxRise = Math.min(MOUTH_SLEW.riseRate * dt, MOUTH_SLEW.maxStep);
    for (let i = 1; i < VISEME_COUNT; i++) {
      if (i === VI.PP) continue;
      if (out[i] > this.prevOut[i] + maxRise) out[i] = this.prevOut[i] + maxRise;
      // ...and nothing but a closure drops by more than that either (a vowel that falls 0.37 in one frame reads as a pop).
      else if (w[VI.PP] < 0.5 && out[i] < this.prevOut[i] - maxRise) out[i] = this.prevOut[i] - maxRise;
    }
    // Closures are never louder than the lip-sync asked for.
    out[VI.PP] = Math.min(out[VI.PP], w[VI.PP]);
    // FF and SS may only trail a falling request by the slew limit (never exceed a rising one), so a request that
    // drops 0.4 in one frame lets go over two or three frames instead of popping.
    const fallFloor = w[VI.PP] < 0.5 ? maxRise : 0;
    out[VI.FF] = Math.min(out[VI.FF], Math.max(w[VI.FF], this.prevOut[VI.FF] - fallFloor));
    out[VI.SS] = Math.min(out[VI.SS], Math.max(w[VI.SS], this.prevOut[VI.SS] - fallFloor));
    // PP_jaw corrective (V2 mesh, when the GLB has it): PP x min(jaw, 0.2) / 0.2, so the lips seal
    // whatever angle the jaw is still at while it closes.
    this.ppJawMorph = out[VI.PP] * Math.min(this.jaw, j.ppJawMorphRef) / j.ppJawMorphRef;
    this.prevOut.set(out);
    return out;
  }

  /**
   * The viseme mass cannot exceed 1 once PP has been snapped or held: every other viseme is scaled by
   * min(1, (1 - PP) / sum_others), so a held seal never stacks with a vowel into a torn lip (the V2
   * mesh is authored for a sum of at most 1). Leaves the weights alone when the sum is already fine.
   */
  fitToClosure(w) {
    const pp = w[VI.PP];
    if (pp < SEAL_FROM) return; // only a snapped or held seal; a passing PP keeps the lip-sync's blend
    let others = 0;
    for (let i = 0; i < VISEME_COUNT; i++) if (i !== VI.PP) others += w[i];
    const room = Math.max(0, 1 - pp);
    if (others <= room || others <= 0) return;
    const k = room / others;
    for (let i = 0; i < VISEME_COUNT; i++) if (i !== VI.PP) w[i] *= k;
  }

  /**
   * The consonant bridge [MB 6.4]: while a consonant (not PP, which has its own gate) outweighs the
   * vowel next to it, the jaw is cut by up to chewDepth. The viseme weights already last 40-120 ms
   * per consonant, so the cut lasts as long: the jaw chews at the syllable rate (4-5 Hz).
   * @returns {number} 0..chewDepth
   */
  chew(w) {
    const j = this.jawCfg;
    let cons = 0;
    for (const i of CONSONANT_IDX) cons += w[i];
    let vow = 0;
    for (const i of VOWEL_IDX) vow += w[i];
    const x = cons - 0.5 * vow;
    return j.chewDepth * clamp((x - j.chewFrom) / (j.chewFull - j.chewFrom), 0, 1);
  }

  /**
   * The text timeline path: the closure snap [MB 6.4]. PP at or above snapAt is shown as snapTo, and a
   * seal that began is kept until it has lasted minMs, so no b or m is a one-frame flicker.
   */
  timedShaping(dt, w) {
    const t = this.timed;
    const pp = w[VI.PP];
    if (pp >= t.snapAt) {
      this.ppSeal += dt;
      w[VI.PP] = Math.max(pp, t.snapTo);
    } else if (this.ppSeal > 0) {
      this.ppSeal += dt;
      if (this.ppSeal * 1000 < t.minMs) w[VI.PP] = Math.max(pp, t.snapTo);
      else this.ppSeal = 0;
    }
    // Weak audio-drawn spans: lift the mass (not inside a closure, and never the closure itself).
    if (w[VI.PP] < 0.3) {
      let mass = 0;
      for (let i = 2; i < VISEME_COUNT; i++) mass += w[i];
      if (mass > t.massMin && mass < t.massTarget) {
        const lift = Math.min(t.massMax, t.massTarget / mass);
        // FF and SS are caps the lip-sync asked for (never amplified, M4); the rest may grow.
        for (let i = 2; i < VISEME_COUNT; i++) if (i !== VI.FF && i !== VI.SS) w[i] *= lift;
      }
    }
  }

  /** Mass lift, vowel hold, stress hold and PP hold for the audio-only path [MB 6.3-6.5]. */
  audioShaping(dt, w, stress) {
    const a = this.audio;
    // PP hold: a bilabial seal lasts at least 70 ms, two frames at 24 fps.
    if (w[VI.PP] >= a.ppHoldAt) this.ppHoldLeft = a.ppHoldTime;
    else if (this.ppHoldLeft > 0) {
      this.ppHoldLeft -= dt;
      w[VI.PP] = Math.max(w[VI.PP], a.ppHoldAt);
    }

    // Dominant vowel now.
    let dom = -1;
    let domW = 0;
    for (const idx of VOWEL_IDX) {
      if (w[idx] > domW) {
        domW = w[idx];
        dom = idx;
      }
    }

    // Vowel hold: the previous dominant vowel keeps a floor for a moment after it fades.
    if (dom >= 0 && domW >= a.vowelHoldAt) {
      this.holdVowel = dom;
      this.holdLeft = a.vowelHoldTime;
    } else if (this.holdLeft > 0 && this.holdVowel >= 0) {
      this.holdLeft -= dt;
      w[this.holdVowel] = Math.max(w[this.holdVowel], a.vowelHold);
    }

    // Stress hold: a stressed vowel holds near its peak for 120 ms.
    if (stress > 0.5 && dom >= 0) {
      if (domW > this.stressPeak || dom !== this.stressPeakIdx) {
        this.stressPeak = domW;
        this.stressPeakIdx = dom;
        this.stressHoldLeft = a.stressHoldTime;
      }
    }
    if (this.stressHoldLeft > 0 && this.stressPeakIdx >= 0) {
      this.stressHoldLeft -= dt;
      w[this.stressPeakIdx] = Math.max(w[this.stressPeakIdx], this.stressPeak * a.stressHoldFrac);
      if (this.stressHoldLeft <= 0) {
        this.stressPeak = 0;
        this.stressPeakIdx = -1;
      }
    }

    // Mass lift (off by default): lift weak non-sil mass so quiet speech still reads.
    if (a.massLift) {
      let mass = 0;
      for (let i = 1; i < VISEME_COUNT; i++) mass += w[i];
      this.mass = mass;
      if (mass > a.massMin) {
        const lift = Math.min(a.massMax, a.vowelSumMax / mass);
        if (lift > 1) for (let i = 1; i < VISEME_COUNT; i++) w[i] *= lift;
      }
    }
  }
}
