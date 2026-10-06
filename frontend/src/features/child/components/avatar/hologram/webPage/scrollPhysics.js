// w3: how the held page scrolls (BEHAVIOUR-SPEC 6.4). Pure and allocation-free: one object, mutated in place.
//
//   reading   a slow drift, 14 px/s, as if a thumb were resting on the page
//   flick     an impulse that decays exponentially: v0 = travel / tau, so it travels exactly `travel` (one card)
//   end       a short rubber band (at most 24 px) and then the page drifts back up, slowly
//   found     a critically damped spring brings the found card to a quarter of the way down the viewport
//
// Units are page pixels (the window is 360 x 480 logical px). `pos` is how far the page has moved up.

export const SCROLL = {
  drift: 14, // px/s while reading
  tau: 0.33, // s, flick decay time
  maxFlicks: 6, // per search
  minGap: 1.6, // s between flicks
  rubber: 24, // px, the most the page may stretch past an end
  rubberTau: 0.1, // s, the spring back (about 95 percent in 0.3 s)
  endBounce: 9, // px, how far a flick that lands on the end stretches the band
  endZone: 0.35, // a flick is not started within this many pitches of the end
  foundOmega: 9, // 1/s, the found spring (critically damped)
};

export function createScroll(cfg = SCROLL) {
  const s = {
    cfg,
    pos: 0,
    vel: 0, // flick velocity, px/s
    max: 0,
    pitch: 170,
    t: 0,
    flicks: 0,
    lastFlick: -999,
    mode: 'idle', // idle | read | found
    dir: 1, // drift direction: 1 down the page, -1 back up
    target: 0, // found target
    foundVel: 0,
    reduced: false,
    // set by flick(): how far the last one will travel (a test reads it)
    lastTravel: 0,
  };

  s.reset = (max, pitch) => {
    s.pos = 0;
    s.vel = 0;
    s.max = Math.max(0, max);
    s.pitch = pitch > 0 ? pitch : 170;
    s.t = 0;
    s.flicks = 0;
    s.lastFlick = -999;
    s.mode = 'idle';
    s.dir = 1;
    s.foundVel = 0;
    s.lastTravel = 0;
  };

  s.setMax = (max, pitch) => {
    s.max = Math.max(0, max);
    if (pitch > 0) s.pitch = pitch;
  };

  /** Start reading: the drift runs from now. */
  s.read = () => {
    if (s.mode !== 'found') s.mode = 'read';
  };

  /** True when a flick may start now. */
  s.canFlick = () =>
    !s.reduced &&
    s.mode === 'read' &&
    s.flicks < cfg.maxFlicks &&
    s.t - s.lastFlick >= cfg.minGap &&
    s.max > 0 &&
    s.max - s.pos > s.pitch * cfg.endZone;

  /** A flick of one card. Returns true when it started. */
  s.flick = () => {
    if (!s.canFlick()) return false;
    let travel = s.pitch;
    const left = s.max - s.pos;
    if (travel > left) travel = left + cfg.endBounce; // it lands on the end and stretches the band a little
    s.lastTravel = travel;
    s.vel = travel / cfg.tau;
    s.flicks += 1;
    s.lastFlick = s.t;
    return true;
  };

  /** Bring the found card into place. In reduced motion the page jumps there. */
  s.found = (target, reduced) => {
    s.target = Math.min(s.max, Math.max(0, target));
    s.mode = 'found';
    s.vel = 0;
    if (reduced) {
      s.pos = s.target;
      s.foundVel = 0;
    }
  };

  s.step = (dt) => {
    s.t += dt;
    if (s.mode === 'found') {
      // critically damped spring: x'' = w^2 (target - x) - 2 w x'
      const w = cfg.foundOmega;
      const a = w * w * (s.target - s.pos) - 2 * w * s.foundVel;
      s.foundVel += a * dt;
      s.pos += s.foundVel * dt;
      return s.pos;
    }
    if (s.mode === 'idle' || s.reduced) return s.pos;
    // reading drift, plus a flick if one is running
    const drifting = s.max > 0;
    let v = s.vel;
    if (drifting) {
      // the drift turns around at the far end and returns slowly to the top
      if (s.dir > 0 && s.pos >= s.max - 1) s.dir = -1;
      else if (s.dir < 0 && s.pos <= 1) s.dir = 1;
      // w3 review: the drift runs under the flick too. Gated on vel < 1 it stayed off for about 2 s after every flick,
      // so with a flick every 1.6 to 2.4 s the page all but stopped (2 to 3 px/s) before each one.
      v += s.dir * cfg.drift;
    }
    s.pos += v * dt;
    if (s.vel > 0) {
      s.vel *= Math.exp(-dt / cfg.tau);
      if (s.vel < 0.5) s.vel = 0;
    }
    // the rubber band: stretch past an end, at most cfg.rubber, and spring back
    if (s.pos > s.max) {
      let over = s.pos - s.max;
      if (s.vel === 0) over *= Math.exp(-dt / cfg.rubberTau);
      if (over > cfg.rubber) {
        over = cfg.rubber;
        s.vel = 0;
      }
      s.pos = s.max + over;
    } else if (s.pos < 0) {
      let over = -s.pos;
      over *= Math.exp(-dt / cfg.rubberTau);
      s.pos = -over;
      if (s.pos > -0.01) s.pos = 0;
    }
    return s.pos;
  };

  return s;
}
