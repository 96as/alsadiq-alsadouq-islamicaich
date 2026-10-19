// Attack/release smoothing of the raw viseme targets, so the mouth moves like a mouth and not
// like a meter. Two stages:
//   1. a fast low-pass that removes single-frame jitter from the classifier;
//   2. a per-viseme attack (opening toward a target) and release (letting go), with the lip
//      closures fast and the rounded vowels slow.
// Because every viseme eases independently, neighbouring shapes overlap in time: that overlap
// is the co-articulation (the mouth is already rounding for the "oo" while it leaves the "ee").
// The weights are then scaled so they never add up to more than 1, and `sil` takes the rest.

import { SMOOTHING } from './lipsyncConfig.js';
import { VISEME_COUNT, VI } from './visemes.js';

const damp = (a, b, rate, dt) => b + (a - b) * Math.exp(-rate * dt);

export class VisemeSmoother {
  constructor(cfg = SMOOTHING) {
    this.cfg = cfg;
    this.pre = new Float32Array(VISEME_COUNT);
    this.out = new Float32Array(VISEME_COUNT);
    this.out[VI.sil] = 1;
  }

  reset() {
    this.pre.fill(0);
    this.out.fill(0);
    this.out[VI.sil] = 1;
  }

  /**
   * @param {Float32Array} raw targets from the classifier (entry 0 ignored)
   * @param {number} dt seconds since the previous step
   * @returns {Float32Array} smoothed weights, sil included (reused between calls)
   */
  step(raw, dt) {
    const { pre, out, cfg } = this;
    let sum = 0;
    for (let i = 1; i < VISEME_COUNT; i++) {
      pre[i] = damp(pre[i], raw[i], cfg.preRate, dt);
      const rate = pre[i] > out[i] ? cfg.attack[i] : cfg.release[i];
      out[i] = damp(out[i], pre[i], rate, dt);
      sum += out[i];
    }
    const scale = sum > cfg.maxSum ? cfg.maxSum / sum : 1;
    sum = 0;
    for (let i = 1; i < VISEME_COUNT; i++) {
      out[i] *= scale;
      sum += out[i];
    }
    out[VI.sil] = sum < 1 ? 1 - sum : 0;
    return out;
  }
}
