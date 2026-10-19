// Studio blink timing [MB 5.3]: a drop-in for BlinkScheduler whose intervals are gamma
// distributed (k = 2.5) instead of uniform, with a mean that depends on what the avatar is doing
// (3.5 s idle, 2.6 s speaking), 10% double blinks, a 1.2 s minimum gap and the same stress
// deferral and phrase-end blink as the base class. Same API: update(dt, ctx) -> weight,
// notifyPhraseEnd(), .blinks, .sinceBlink, so lipsyncRig and ClipAvatar need no other change.

import { BlinkScheduler } from '../lipsync/blinkScheduler.js';
import { BLINK_STUDIO } from './actingConfig.js';

/** One standard normal from two uniforms (Box-Muller). */
function normal(rng) {
  const u = Math.max(1e-9, rng());
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rng());
}

/** Gamma(k, theta) by Marsaglia and Tsang, with the k < 1 boost. Mean is k x theta. */
export function gammaSample(k, theta, rng) {
  if (k < 1) return gammaSample(k + 1, theta, rng) * Math.pow(Math.max(1e-9, rng()), 1 / k);
  const d = k - 1 / 3;
  const c = 1 / Math.sqrt(9 * d);
  for (;;) {
    let x;
    let v;
    do {
      x = normal(rng);
      v = 1 + c * x;
    } while (v <= 0);
    v = v * v * v;
    const u = rng();
    if (u < 1 - 0.0331 * x * x * x * x || Math.log(Math.max(1e-12, u)) < 0.5 * x * x + d * (1 - v + Math.log(v))) return d * v * theta;
  }
}

export class StudioBlinkScheduler extends BlinkScheduler {
  /**
   * @param {object} [opts]
   * @param {() => number} [opts.rng]
   * @param {object} [opts.config] overrides for BLINK_STUDIO
   */
  constructor({ rng = Math.random, config } = {}) {
    const studio = { ...BLINK_STUDIO, ...config };
    // The base constructor draws the first interval, so the studio config is set first via cfg
    // overrides and `mean` is read through a field that already exists at that point.
    super({
      rng,
      config: {
        doubleChance: studio.doubleChance,
        doubleGap: studio.doubleGap,
        closeTime: studio.closeTime,
        holdTime: studio.holdTime,
        openTime: studio.openTime,
        phraseEndChance: studio.phraseEndChance,
        minInterval: studio.minGap,
        maxInterval: 99,
      },
    });
    this.studio = studio;
    this.mean = studio.meanIdle;
    this.timer = this.nextInterval();
  }

  /** Set what the avatar is doing: 'idle' | 'listening' | 'thinking' | 'speaking'. */
  setState(state) {
    this.mean = this.studio.meanByState[state] ?? this.studio.meanIdle;
  }

  nextInterval() {
    const s = this.studio ?? BLINK_STUDIO; // the base constructor calls this before `studio` is set
    const mean = this.mean ?? s.meanIdle;
    const gap = gammaSample(s.shape, mean / s.shape, this.rng);
    return Math.max(s.minGap, Math.min(gap, mean * 3));
  }
}
