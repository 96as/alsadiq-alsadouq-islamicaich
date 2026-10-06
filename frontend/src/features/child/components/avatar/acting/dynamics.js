// Small pure helpers shared by the acting modules: clamps, seeded randomness, a second-order
// spring (the t3ssel8r form, the same law the Blender bakes use) and a few easing curves.
// No three.js. Nothing allocates after construction.

export const clamp = (x, lo, hi) => (x < lo ? lo : x > hi ? hi : x);
export const lerp = (a, b, t) => a + (b - a) * t;
export const damp = (a, b, rate, dt) => b + (a - b) * Math.exp(-rate * dt);
export const between = (range, rng) => range[0] + rng() * (range[1] - range[0]);

/** Minimum-jerk rise: 0 to 1 with zero velocity and acceleration at both ends. */
export const minJerk = (x) => {
  const t = clamp(x, 0, 1);
  return t * t * t * (10 + t * (-15 + 6 * t));
};
export const easeOut = (x) => 1 - (1 - clamp(x, 0, 1)) ** 2;

/** Deterministic random numbers in [0, 1). Inject one in tests; the app uses Math.random. */
export function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const TWO_PI = Math.PI * 2;

/**
 * Second-order spring, t3ssel8r form: frequency f (Hz), damping z, response r.
 * update(dt, x) follows the target x and returns the position.
 */
export class SecondOrder {
  constructor(f, z, r = 0, x0 = 0) {
    this.k1 = z / (Math.PI * f);
    this.k2 = 1 / (TWO_PI * f) ** 2;
    this.k3 = (r * z) / (TWO_PI * f);
    this.reset(x0);
  }

  reset(y = 0, yd = 0) {
    this.y = y;
    this.yd = yd;
    this.xp = y;
  }

  update(dt, x) {
    if (dt <= 0) return this.y;
    const xd = (x - this.xp) / dt;
    this.xp = x;
    // Semi-implicit Euler, with k2 clamped so a long frame cannot blow the spring up.
    const k2 = Math.max(this.k2, (dt * dt) / 2 + (dt * this.k1) / 2, dt * this.k1);
    this.y += dt * this.yd;
    this.yd += (dt * (x + this.k3 * xd - this.y - this.k1 * this.yd)) / k2;
    return this.y;
  }
}

/** A sum of a few sines at unrelated frequencies: smooth, never exactly periodic, no allocation. */
export class SineMix {
  /**
   * @param {number[]} hz frequencies in Hz
   * @param {number[]} mix their relative amplitudes
   * @param {() => number} rng picks the phases
   */
  constructor(hz, mix, rng) {
    this.hz = hz;
    this.mix = mix;
    this.phase = hz.map(() => rng() * TWO_PI);
    let sum = 0;
    for (const m of mix) sum += m;
    this.norm = 1 / sum;
  }

  /** Value in [-1, 1] at time t (seconds). */
  at(t) {
    let v = 0;
    for (let i = 0; i < this.hz.length; i++) v += this.mix[i] * Math.sin(TWO_PI * this.hz[i] * t + this.phase[i]);
    return v * this.norm;
  }
}
