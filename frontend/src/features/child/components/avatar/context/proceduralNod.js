// The nod when the GLB has no Nod clip: a damped pitch impulse on the head bone, applied after the
// mixer. Pure maths here (no three.js); headLayer.js applies the angle.
//
//   angle(t) = peak * weight * bump(t * timeScale)
//   bump: down over the attack (0.12 s), then back up through rest to a small overshoot and a settle
//         over the release (0.35 s). Every segment is a minimum-jerk curve, so the head starts and stops
//         with zero velocity (no "tick" at the start of a nod) and rises a little past rest before it
//         settles, like the Nod clip of spec 4.1 (+6 deg down, then -1.5 deg up, then rest).
//
// Up to two nods may overlap (the double nod). Positive pitch about the head's x axis is a nod down.
// `timeScale` is the clip's timeScale (spec 5.4: 0.85-1.15, 0.8 for empathy: slower), not an amplitude.
// Nothing is allocated after construction.

export const MAX_NODS = 2;
export const NOD_OVERSHOOT = 0.2; // the head rises this share of the dip past rest before it settles
const UP_SHARE = 0.6; // share of the release spent coming back up, through rest, to the overshoot

/** Minimum-jerk 0..1: zero velocity and acceleration at both ends. */
const mj = (k) => k * k * k * (10 + k * (-15 + 6 * k));

export function createProceduralNod({ peak = 0.08, attack = 0.12, release = 0.35 } = {}) {
  const amp = new Float64Array(MAX_NODS);
  const rate = new Float64Array(MAX_NODS).fill(1);
  const age = new Float64Array(MAX_NODS).fill(-1); // nod time since it began (scaled), -1 free
  const total = attack + release;
  const up = release * UP_SHARE;
  const settle = release - up;

  const bump = (a) => {
    if (a < 0 || a >= total) return 0;
    if (a < attack) return mj(a / attack); // down
    const r = a - attack;
    if (r < up) return 1 - (1 + NOD_OVERSHOOT) * mj(r / up); // back up, a little past rest
    return -NOD_OVERSHOOT * (1 - mj((r - up) / settle)); // settle
  };

  return {
    /** Start a nod. `weight` 0..1 of the peak; `timeScale` > 1 is quicker, < 1 slower. */
    fire(weight = 1, timeScale = 1) {
      let slot = -1;
      for (let i = 0; i < MAX_NODS; i++) if (age[i] < 0) slot = i;
      if (slot < 0) {
        // both busy: replace the older one
        slot = age[0] >= age[1] ? 0 : 1;
      }
      amp[slot] = peak * weight;
      rate[slot] = timeScale > 0.1 ? timeScale : 1;
      age[slot] = 0;
    },
    /** Advance and return the head pitch (radians, positive is a nod down). */
    step(dt) {
      let angle = 0;
      for (let i = 0; i < MAX_NODS; i++) {
        if (age[i] < 0) continue;
        age[i] += dt * rate[i];
        if (age[i] >= total) {
          age[i] = -1;
          continue;
        }
        angle += amp[i] * bump(age[i]);
      }
      return angle;
    },
    get active() {
      return age[0] >= 0 || age[1] >= 0;
    },
    reset() {
      age.fill(-1);
    },
    duration: total,
  };
}
