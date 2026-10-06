// Natural blinking for a "blink" morph target. Pure timing logic; the caller writes the weight.
//   - a blink every 2 to 6 s at random;
//   - now and then a double blink;
//   - none starts while a stressed syllable is being spoken (it waits for the stress to pass);
//   - at the end of a phrase a blink is likely, as people blink at the end of a thought.
// A blink closes fast, holds a moment and opens slower, as a real lid does.

import { BLINK } from './lipsyncConfig.js';

const between = (range, rng) => range[0] + rng() * (range[1] - range[0]);
const easeOut = (x) => 1 - (1 - x) * (1 - x);
const easeInOut = (x) => x * x * (3 - 2 * x);

const IDLE = 0;
const CLOSING = 1;
const HOLD = 2;
const OPENING = 3;

export class BlinkScheduler {
  /**
   * @param {object} [opts]
   * @param {() => number} [opts.rng] returns [0,1); inject a seeded one in tests
   * @param {object} [opts.config] overrides for BLINK
   */
  constructor({ rng = Math.random, config } = {}) {
    this.cfg = { ...BLINK, ...config };
    this.rng = rng;
    this.phase = IDLE;
    this.phaseTime = 0;
    this.weight = 0;
    this.timer = this.nextInterval(); // seconds until the next blink may start
    this.sinceBlink = 0;
    this.deferred = 0; // seconds a due blink has waited for a stressed syllable to pass
    this.secondOfPair = false; // the blink that is due is the second of a double blink
    this.blinks = 0; // how many blinks have started (for tests and the dev page)
  }

  nextInterval() {
    return between([this.cfg.minInterval, this.cfg.maxInterval], this.rng);
  }

  /** Call when a spoken phrase has just ended. Pulls the next blink forward, often. */
  notifyPhraseEnd() {
    const c = this.cfg;
    if (this.phase !== IDLE || this.secondOfPair) return;
    if (this.sinceBlink < c.phraseEndMinSince) return;
    if (this.rng() > c.phraseEndChance) return;
    this.timer = Math.min(this.timer, between(c.phraseEndDelay, this.rng));
  }

  /**
   * @param {number} dt seconds since the previous call
   * @param {{stress?: number, reduced?: boolean}} [ctx] stress 0..1 from the lip-sync;
   *   reduced = prefers-reduced-motion (no double blinks)
   * @returns {number} blink weight 0..1
   */
  update(dt, { stress = 0, reduced = false } = {}) {
    const c = this.cfg;
    this.sinceBlink += dt;
    if (this.phase === IDLE) {
      this.timer -= dt;
      if (this.timer <= 0) {
        if (stress <= c.stressBlock || this.deferred >= c.maxDefer) {
          this.start();
        } else if (this.secondOfPair) {
          // A stressed syllable came between the pair: drop the second blink.
          this.secondOfPair = false;
          this.timer = this.nextInterval();
        } else {
          this.deferred += dt;
        }
      }
      this.weight = 0;
      return 0;
    }
    this.phaseTime += dt;
    if (this.phase === CLOSING) {
      this.weight = easeOut(Math.min(1, this.phaseTime / c.closeTime));
      if (this.phaseTime >= c.closeTime) this.go(HOLD);
    } else if (this.phase === HOLD) {
      this.weight = 1;
      if (this.phaseTime >= c.holdTime) this.go(OPENING);
    } else {
      this.weight = 1 - easeInOut(Math.min(1, this.phaseTime / c.openTime));
      if (this.phaseTime >= c.openTime) {
        this.weight = 0;
        this.go(IDLE);
        if (this.secondOfPair) {
          this.secondOfPair = false;
          this.timer = this.nextInterval();
        } else if (!reduced && this.rng() < c.doubleChance) {
          this.secondOfPair = true;
          this.timer = between(c.doubleGap, this.rng);
        } else {
          this.timer = this.nextInterval();
        }
      }
    }
    return this.weight;
  }

  start() {
    this.blinks++;
    this.sinceBlink = 0;
    this.deferred = 0;
    this.go(CLOSING);
  }

  go(phase) {
    this.phase = phase;
    this.phaseTime = 0;
  }
}
