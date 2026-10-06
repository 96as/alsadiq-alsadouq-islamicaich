// The studio walk-in timeline (WP1). Plain numbers, no three.js, so node can test it.
//
// The studio GLB carries Walk (16 f loop, heel strike R at f0 and L at f8), Walk_Start (Idle f0 to
// Walk f0, 15 f) and Walk_Stop_R / Walk_Stop_L (Walk f0 / f8 to Idle f0, 21 f). The clips are in
// place; the root travels by the sidecar's `root_speed_m_s` during the transitions and by 0.525 m/s
// during the Walk loop, so the planted feet never slide (W2, W9).
//
// This module owns the clocks. Every frame it says which leg is playing and how far into the clip it
// is (`sw.leg`, `sw.legT`, `sw.walkClock`); the avatar sets the clip times from those numbers, so
// the timeline and the pose can never drift apart. Everything is measured in clip seconds, which
// run at `timeScale` times real time, so the root travel and the legs always agree, whatever the
// pace (a late rush simply plays faster).
//
// The walk is planned in whole half steps at the start: Start, n half steps of Walk, and the stop
// whose first contact matches n (even n stops from the right heel strike, odd n from the left). The
// avatar's start distance is nudged by at most half a half step (0.07 m) so that the plan lands on
// the spot exactly.
//
// Turning (Bible 3.3): the root turns toward the path's direction at most `turnRate` rad/s; the head
// leads it by `headLead` seconds; at the stop up to `residualMax` of remaining turn goes into the
// chest and neck over `residualTime` seconds, after which the root turns at `residualRate` rad/s
// while the chest and neck hand the turn back.
//
// Nothing here may contain scripture or any other Islamic text; it is pure animation data.
import { WALK_TRANSITIONS as T } from './avatarConfig.js';

export const LEG = { START: 0, CRUISE: 1, STOP: 2 };
const EPS = 1e-9;

const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
const smooth = (x) => {
  const c = clamp(x, 0, 1);
  return c * c * (3 - 2 * c);
};

/** Metres covered between clip seconds t0 and t1 by a root_speed array (piecewise constant per frame). */
export function rootDistance(root, t0, t1) {
  let d = 0;
  let t = t0;
  const last = root.length - 1;
  while (t < t1 - 1e-12) {
    const i = Math.floor(t * T.fps + EPS);
    const end = Math.min((i + 1) / T.fps, t1);
    d += root[i > last ? last : i] * (end - t);
    t = end;
  }
  return d;
}

export const START_DIST = rootDistance(T.start.root, 0, T.start.duration);
export const STOP_R_DIST = rootDistance(T.stopR.root, 0, T.stopR.duration);
export const STOP_L_DIST = rootDistance(T.stopL.root, 0, T.stopL.duration);

/**
 * Plan the walk for a path of `modelMetres`: Start, n half steps of Walk, then the stop that
 * begins on the matching heel strike. Returns the n and the exact distance that plan covers.
 */
export function planWalk(modelMetres) {
  let best = null;
  for (let n = 0; n < 600; n++) {
    const right = n % 2 === 0;
    const total = START_DIST + n * T.halfStep + (right ? STOP_R_DIST : STOP_L_DIST);
    const err = Math.abs(total - modelMetres);
    if (!best || err < best.err) best = { n, right, total, err };
    if (total > modelMetres + 1) break;
  }
  return best;
}

/** The studio timeline state, kept on `walk.sw`. */
function makeState(plan, ts, hold = 0) {
  return {
    leg: LEG.START,
    legT: 0, // clip seconds into Start or Stop (0 while cruising)
    walkClock: 0, // clip seconds of Walk played since Start ended
    n: plan.n, // half steps of Walk between Start and the stop
    side: plan.right ? 'R' : 'L',
    total: plan.total, // model metres the plan covers
    k: 1, // root-motion scale during the stop (1 unless the distance was pinned)
    twistT: -1, // real seconds since the stop began, -1 before
    twist: 0, // radians of chest and neck turn (+ = toward the viewer's right, like yaw)
    lead: 0, // radians the head leads the root's turn
    yawRate: 0,
    stopYaw: 0, // the root's yaw when the stop began (W10: at most 15 deg)
    stopAt: -1, // walkClock seconds (clip) the stop began at
    stopPhase: -1, // Walk phase in frames (0..16) the stop began at (W9: 0 or 8, +-1)
    ts,
    clock: 0, // real seconds since the timeline started
    hold, // real seconds still to stand on Walk_Start f0 (Idle f0) while the avatar fades in
  };
}

/** Begin the studio walk (the WAIT to WALK moment). */
export function startStudio(w, clip) {
  const ts = w.rush ? clip.rushScale : clip.cruiseScale;
  w.timeScale = ts;
  const plan = planWalk(w.distance / clip.modelScale);
  w.sw = makeState(plan, ts, (w.holdIn ?? clip.holdIn) || 0); // avatar-integ: a mid-meadow leg sets walk.holdIn = 0 (no fade-in to wait for)
  // Land exactly on the spot with whole steps, unless a preview pinned the distance.
  if (!w.distanceLocked) w.distance = plan.total * clip.modelScale;
  if (w.distanceLocked) {
    const stop = plan.right ? STOP_R_DIST : STOP_L_DIST;
    const rest = w.distance / clip.modelScale - (plan.total - stop);
    w.sw.k = clamp(rest / Math.max(stop, 1e-6), 0.5, 1.5);
  }
}

/** The root turns toward `target`, smoothed and never faster than `rate` rad/s. Returns the new yaw. */
export function turnToward(yaw, target, rate, dt, smoothing = 6) {
  const want = (target - yaw) * (1 - Math.exp(-smoothing * dt));
  const max = rate * dt;
  return yaw + clamp(want, -max, max);
}

function startStop(w, sw, clip) {
  sw.leg = LEG.STOP;
  sw.legT = 0;
  sw.twistT = 0;
  sw.stopYaw = w.yaw;
  sw.stopAt = sw.walkClock;
  const cyc = clip.cycle;
  sw.stopPhase = ((sw.walkClock % cyc) / cyc) * 16;
  if (sw.stopPhase > 15.5) sw.stopPhase -= 16; // a contact at phase 16 is Walk f0 of the next cycle
  if (w.distanceLocked) {
    const stop = sw.side === 'R' ? STOP_R_DIST : STOP_L_DIST;
    const rest = (w.distance - w.traveled) / clip.modelScale;
    sw.k = clamp(rest / Math.max(stop, 1e-6), 0.5, 1.5);
  }
}

/**
 * One frame of the WALK state. Returns true when the walk has reached the spot and the stop
 * clip has played out (the caller enters TURN).
 */
export function stepStudioWalk(w, dt, clip) {
  const sw = w.sw;
  sw.clock += dt;
  w.fade = Math.min(1, w.fade + dt / clip.fadeIn);
  const want = w.rush ? clip.rushScale : clip.cruiseScale;
  w.timeScale += (want - w.timeScale) * (1 - Math.exp(-4 * dt)); // a late rush speeds up smoothly
  sw.ts = w.timeScale;

  let rem = dt * w.timeScale; // clip seconds to consume this frame
  if (sw.hold > 0) {
    // fading in on Idle f0: the clips wait, the root stays, the heading may still settle
    sw.hold = Math.max(sw.hold - dt, 0);
    rem = 0;
  }
  let dm = 0; // model metres moved this frame
  let done = false;
  for (let guard = 0; rem > EPS && guard < 8; guard++) {
    if (sw.leg === LEG.START) {
      const take = Math.min(rem, T.start.duration - sw.legT);
      dm += rootDistance(T.start.root, sw.legT, sw.legT + take);
      sw.legT += take;
      rem -= take;
      if (sw.legT >= T.start.duration - EPS) {
        sw.leg = LEG.CRUISE;
        sw.legT = 0;
        sw.walkClock = 0;
      }
    } else if (sw.leg === LEG.CRUISE) {
      const target = sw.n * (clip.cycle / 2);
      const take = Math.min(rem, Math.max(target - sw.walkClock, 0));
      dm += take * T.steadySpeed;
      sw.walkClock += take;
      rem -= take;
      if (sw.walkClock >= target - EPS) {
        sw.walkClock = target;
        startStop(w, sw, clip);
      } else break;
    } else {
      const def = sw.side === 'R' ? T.stopR : T.stopL;
      const take = Math.min(rem, def.duration - sw.legT);
      dm += rootDistance(def.root, sw.legT, sw.legT + take) * sw.k;
      sw.legT += take;
      rem -= take;
      if (sw.legT >= def.duration - EPS) {
        sw.legT = def.duration;
        done = true;
        break;
      }
    }
  }

  const advance = dm * clip.modelScale;
  w.speed = advance / Math.max(dt, 1e-6);
  w.traveled = Math.min(w.traveled + advance, w.distance);

  // Turning: the root follows the path's direction at a limited rate, the head leads it.
  const prev = w.yaw;
  w.yaw = turnToward(prev, w.travelYaw, clip.turnRate, dt);
  const rate = (w.yaw - prev) / Math.max(dt, 1e-6);
  sw.yawRate += (rate - sw.yawRate) * (1 - Math.exp(-30 * dt));
  sw.lead = sw.yawRate * clip.headLead;
  updateTwist(w, sw, dt, clip);

  if (done) {
    w.traveled = w.distance;
    w.speed = 0;
  }
  return done;
}

/** The chest and neck carry the remaining turn while the stop plays (and until the root catches up). */
function updateTwist(w, sw, dt, clip) {
  if (sw.twistT < 0) {
    sw.twist = 0;
    return;
  }
  sw.twistT += dt;
  const ramp = smooth(sw.twistT / clip.residualTime);
  sw.twist = clamp(-w.yaw, -clip.residualMax, clip.residualMax) * ramp;
}

/** One frame of TURN: the chest and neck hold the turn, then the root catches up slowly. */
export function stepStudioTurn(w, dt, clip) {
  const sw = w.sw;
  w.fade = 1;
  sw.lead = 0;
  sw.yawRate = 0;
  sw.twistT += dt;
  if (sw.twistT >= clip.residualTime) {
    w.yaw = turnToward(w.yaw, 0, clip.residualRate, dt, 8);
    if (Math.abs(w.yaw) < 1e-3) w.yaw = 0;
  }
  sw.twist = clamp(-w.yaw, -clip.residualMax, clip.residualMax) * smooth(sw.twistT / clip.residualTime);
  return sw.twistT >= clip.residualTime && w.yaw === 0;
}
