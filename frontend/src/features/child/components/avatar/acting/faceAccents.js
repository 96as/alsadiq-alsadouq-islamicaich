// Face accents [MB 6.7, 6.8]: brow flashes on stress, a held inner-brow lift for questions and
// empathy, lids that follow the jaw, and cheeks that fill on closures. Pure math: it returns 0..1
// targets for morphs the caller binds only if they exist (browUp needs the WP5 mesh).

import { FACE } from './actingConfig.js';
import { between, clamp, damp, easeOut } from './dynamics.js';

export class FaceAccents {
  constructor({ rng = Math.random, config } = {}) {
    this.cfg = { ...FACE, ...config };
    this.rng = rng;
    this.time = 0;
    this.flashT = 99; // time since the current brow flash began
    this.flashAmp = 0;
    this.nextFlash = 0;
    this.inner = 0;
    this.lid = 0;
    this.cheek = 0;
    this.flashes = 0;
    this.out = { browUp: 0, browInnerUp: 0, lid: 0, cheek: 0 };
  }

  reset() {
    this.flashT = 99;
    this.inner = this.lid = this.cheek = 0;
  }

  /** Force a flash (tests, or the director asking for one). */
  flash(strength = 1) {
    const c = this.cfg;
    this.flashT = 0;
    this.flashAmp = c.browMin + (c.browMax - c.browMin) * clamp(strength, 0, 1);
    this.nextFlash = this.time + between(c.browGap, this.rng);
    this.flashes++;
  }

  /**
   * @param {number} dt
   * @param {object} ctx
   * @param {boolean} [ctx.accent] stress accent this frame
   * @param {number} [ctx.accentStrength]
   * @param {number} [ctx.jaw] jaw angle, rad
   * @param {number} [ctx.lookDown] 0..1 how far the eyes are looking down
   * @param {number} [ctx.pp] bilabial weight 0..1
   * @param {number} [ctx.aa] open-vowel weight 0..1
   * @param {number} [ctx.level] loudness 0..1
   * @param {number} [ctx.questionEnd] 0..1 inside the last 0.6 s of a question
   * @param {string} [ctx.tone] 'empathy' | 'gentle' | other
   * @param {boolean} [ctx.speaking]
   * @param {boolean} [ctx.reduced] no brow flashes
   */
  update(
    dt,
    { accent = false, accentStrength = 0.5, jaw = 0, lookDown = 0, pp = 0, aa = 0, level = 0, questionEnd = 0, tone = '', speaking = false, reduced = false } = {},
  ) {
    const c = this.cfg;
    this.time += dt;

    // Brow flash on a stress accent: a chance per accent, with a minimum gap between flashes.
    if (accent && speaking && !reduced && this.time >= this.nextFlash && this.rng() < c.browChance) this.flash(accentStrength);
    this.flashT += dt;
    let flash = 0;
    if (this.flashT < c.browUp) flash = this.flashAmp * easeOut(this.flashT / c.browUp);
    else if (this.flashT < c.browUp + c.browDown) flash = this.flashAmp * (1 - easeOut((this.flashT - c.browUp) / c.browDown));
    this.out.browUp = flash;

    // Inner brow: questions and empathy hold it up.
    let innerTarget = 0;
    if (questionEnd > 0) innerTarget = c.innerQuestion * clamp(questionEnd, 0, 1);
    if (tone === 'empathy' || tone === 'gentle') innerTarget = Math.max(innerTarget, c.innerEmpathy);
    if (reduced) innerTarget *= 0.5;
    this.inner = damp(this.inner, innerTarget, c.innerRate, dt);
    this.out.browInnerUp = this.inner;

    // Lids follow the jaw, and drop when the eyes look down.
    const jawLid = c.lidJawAmount * clamp((jaw - c.lidJawAt) / c.lidJawSpan, 0, 1);
    const lidTarget = clamp(jawLid + c.lidLookDown * clamp(lookDown, 0, 1), 0, c.lidMax);
    this.lid = damp(this.lid, lidTarget, c.lidRate, dt);
    this.out.lid = this.lid;

    // Cheeks: bilabial closures and loud open vowels.
    const cheekTarget = clamp(c.cheekPP * pp + c.cheekAa * aa * clamp(level, 0, 1), 0, 1);
    this.cheek = damp(this.cheek, cheekTarget, c.cheekRate, dt);
    this.out.cheek = this.cheek;
    return this.out;
  }
}
