// The avatar's walk-in: it starts further up the path, waddles toward the camera, stops at its
// spot, turns to face the child and waves.
//
// Two halves share one plain object (`createWalk()`), so React never re-renders for it:
// - the avatar canvas steps the timeline and plays the gait on the rig (`stepWalk`, `applyWalk`),
// - the forest canvas reads `distance` and moves the avatar's ground point along the path.
// There are two gaits. With avatar-animated.glb the Walk clip plays and the avatar moves at the
// clip's own ground speed (see stepWalk's `clip` option), so the feet stay planted. With the old
// avatar-web.glb the gait is procedural and its cadence follows the distance actually travelled.
//
// Nothing here may contain scripture or any other Islamic text; it is pure animation data.
import { MathUtils, Quaternion, Vector3 } from 'three';
import { startStudio, stepStudioTurn, stepStudioWalk } from './studioWalk.js';

const { damp, clamp } = MathUtils;
const TAU = Math.PI * 2;

/** Tuning. Angles are radians, distances are avatar units (the avatar is about 0.85 tall). */
export const WALK = {
  distance: 5.2, // how far up the path the avatar starts
  vmax: 0.85, // cruising speed, units per second
  rampUp: 0.7, // seconds to reach full speed
  brakeRate: 2.6, // 1/s, how hard it slows in the last stretch (speed = rate * distance left)
  rushFactor: 2.6, // time-lapse when the child starts the session before the walk is over
  stride: 0.42, // ground covered by one full gait cycle (two steps)
  // legs
  hip: 0.62, // thigh swing
  knee: 0.95, // extra shin fold while the foot is in the air
  foot: 0.8, // how much of the leg's tilt the foot cancels, to keep the sole flat
  // body (applied to the whole model, because the torso is skinned to a static bone)
  bob: 0.014, // up and down per step
  roll: 0.055, // side to side roll
  swayYaw: 0.1, // twist of the body
  swayX: 0.012, // weight shift
  headingMax: 0.55, // three-quarter turn toward the side it is heading to
  // arms
  armSwing: 0.55,
  armPump: 0.1,
  // finish
  turnTime: 0.75, // seconds to turn from the heading to face the child
  wavePec: 0.9, // shoulder lift for the raised arm
  waveArm: 1.85, // arm lift
  waveHand: 0.55, // hand wag
  waveHz: 2.6,
  waveRaise: 0.45,
  waveHold: 1.7,
  waveLower: 0.6,
  fadeIn: 0.7, // seconds to fade in at the far end of the path
  hopHeight: 0.07, // the fallback hop
  hopTime: 0.9,
};

/**
 * Presets. 'landing' is the shorter walk for the demo landing page: a judge is waiting, so the
 * avatar starts closer, walks a little faster and waves a little less. Only the fields listed
 * here differ from WALK; everything else (gait shape, amplitudes) is shared.
 */
export const WALK_PRESETS = {
  default: WALK,
  landing: { ...WALK, distance: 3.2, vmax: 1.0, rampUp: 0.6, turnTime: 0.6, waveHold: 1.2, fadeIn: 0.5 },
};

// A tap on the avatar (landing and child idle screen): a short happy hop, then back to rest.
const TAP_HOP_TIME = 0.35;

export const STATE = { WAIT: 0, WALK: 1, TURN: 2, WAVE: 3, HOP: 4, DONE: 5 };

// The walk plays once per page load. The preview page's replay button bypasses this.
let played = false;

/** `mode`: 'walk' (default), 'hop' (the fallback) or 'off'. `preset`: a key of WALK_PRESETS. */
export function createWalk(mode = 'walk', preset = 'default') {
  return {
    mode,
    cfg: WALK_PRESETS[preset] || WALK,
    tap: false, // the current hop is a tap reaction, not the fallback walk-in
    brief: false, // the current wave is the short idle wave, not the greeting
    armed: false, // the stage says the avatar may start (forest drawn, avatar loaded)
    state: STATE.WAIT,
    t: 0, // seconds in the current state
    distance: (WALK_PRESETS[preset] || WALK).distance, // how far up the path it starts (the avatar sets this for its gait)
    distanceLocked: false, // a preview pinned `distance`; the avatar must leave it alone
    holdIn: null, // avatar-integ: seconds to stand on Idle f0 before Walk_Start; null = the clip's own (a mid-meadow leg sets 0)
    noWave: false, // avatar-integ: end the leg at the stop, no greeting wave (a mid-meadow leg)
    traveled: 0,
    speed: 0,
    timeScale: 1, // Walk clip speed (clip gait only)
    clipWeight: 0, // the Walk clip's blend weight last frame, reported by the avatar (clip gait only)
    travelYaw: 0, // direction of travel as the camera sees it, set by the forest (clip gait only)
    camAz: null, // radians: bearing the avatar's camera takes (same rule as camElev)
    camElev: null, // radians: elevation the avatar's camera takes while it walks in (avatarCam.js), null = default camera
    stopping: false, // the walk-to-idle blend at the end of the path is under way (clip gait only)
    stopT: 0,
    stopFrom: 0,
    stopDist: 0,
    sw: null, // the studio walk's timeline (studioWalk.js), null for the legacy gait
    cycle: 0, // gait phase
    gait: 0, // 0..1 leg and body amplitude
    yaw: 0, // body heading offset
    heading: 0, // set by the forest from the path's slope
    wave: 0, // 0..1 raised-arm weight
    waveT: 0,
    fade: 0, // avatar opacity, 0..1
    hop: 0, // hop height factor
    rush: false, // the child already started the session
    reduced: false,
  };
}

/** Is the avatar still standing at the far end of the path or on its way? (drives the ground point) */
export function walkRemaining(w) {
  if (w.state === STATE.DONE || w.state === STATE.TURN || w.state === STATE.WAVE || w.state === STATE.HOP) return 0;
  return Math.max(w.distance - w.traveled, 0);
}

/** A quick happy hop once the avatar stands at its spot. Ignored while the walk-in is playing. */
export function tapHop(w) {
  if (w.state !== STATE.DONE) return false;
  w.tap = true;
  enter(w, STATE.HOP);
  return true;
}

/** A short wave while the avatar stands idle (the landing's idle beats). Ignored during the walk-in. */
export function briefWave(w) {
  if (w.state !== STATE.DONE) return false;
  w.brief = true;
  w.waveT = 0;
  enter(w, STATE.WAVE);
  return true;
}

/**
 * The avatar says how far up the path its gait starts, unless a preview pinned the distance.
 * avatar-integ: never further than the preset allows (the landing preset starts closer).
 */
export function pinWalkDistance(w, distance) {
  if (w && !w.distanceLocked) w.distance = Math.min(distance, w.cfg.distance);
}

/** Start the walk again (preview page). */
export function replayWalk(w, mode = w.mode === 'off' ? 'walk' : w.mode) {
  w.mode = mode;
  w.state = STATE.WAIT;
  w.t = 0;
  w.traveled = 0;
  w.speed = 0;
  w.gait = 0;
  w.yaw = 0;
  w.wave = 0;
  w.fade = 0;
  w.hop = 0;
  w.rush = false;
  w.clipWeight = 0;
  w.travelYaw = 0;
  w.camElev = null;
  w.camAz = null;
  w.stopping = false;
  w.sw = null;
  w.armed = true;
  played = false;
}

/**
 * avatar-integ: start one more leg of the studio walk on the meadow stage (meadowStage.js). The distance is pinned (the
 * plan lands on it with whole half steps), the leg plays Walk_Start, steps and the matching Walk_Stop, and by default ends
 * there without the greeting wave. `fade: 0` makes the avatar fade in on Idle f0 first (the arrival).
 */
export function beginLeg(w, distance, { wave = false, fade = 1 } = {}) {
  w.mode = 'walk';
  w.state = STATE.WAIT;
  w.t = 0;
  w.traveled = 0;
  w.speed = 0;
  w.gait = 0;
  w.yaw = 0;
  w.travelYaw = 0;
  w.wave = 0;
  w.hop = 0;
  w.clipWeight = 0;
  w.stopping = false;
  w.sw = null;
  w.armed = true;
  w.distance = distance;
  w.distanceLocked = true;
  w.noWave = !wave;
  w.holdIn = fade < 1 ? null : 0;
  w.fade = fade;
  played = false;
}

function finish(w) {
  w.state = STATE.DONE;
  w.tap = false;
  w.brief = false;
  w.camElev = null;
  w.camAz = null;
  w.traveled = w.distance;
  w.speed = 0;
  w.stopping = false;
  w.gait = 0;
  w.yaw = 0;
  w.wave = 0;
  w.hop = 0;
  w.fade = 1;
}

function enter(w, state) {
  w.state = state;
  w.t = 0;
}

/**
 * Advance the timeline. Called once per frame from the avatar's frame loop; allocates nothing.
 */
export function stepWalk(w, dt, { reduced, canPlay = true, clip = null }) {
  if (w.state === STATE.DONE) return;
  w.reduced = reduced;
  const C = w.cfg;
  // reduced motion switched on mid-walk: go straight to the spot
  if (reduced && w.state !== STATE.WAIT) {
    finish(w);
    return;
  }
  if (w.state === STATE.WAIT) {
    if (!w.armed) return;
    if (w.mode === 'off' || reduced || !canPlay || played) {
      finish(w);
      return;
    }
    played = true;
    if (w.mode === 'hop') {
      w.traveled = w.distance;
      enter(w, STATE.HOP);
    } else {
      enter(w, STATE.WALK);
      if (clip?.studio) startStudio(w, clip);
      else if (clip) w.timeScale = clip.minScale;
    }
  }

  if (clip) {
    stepClip(w, dt, clip);
    return;
  }

  const step = dt * (w.rush ? C.rushFactor : 1);
  w.t += step;

  if (w.state === STATE.WALK) {
    const remaining = w.distance - w.traveled;
    const ramp = clamp(w.t / C.rampUp, 0, 1);
    const cruise = C.vmax * ramp * ramp * (3 - 2 * ramp);
    w.speed = Math.min(cruise, C.brakeRate * remaining + 0.02) * (w.rush ? C.rushFactor : 1);
    const advance = Math.min(w.speed * dt, remaining);
    w.traveled += advance;
    w.cycle = (w.cycle + (advance / C.stride) * TAU) % (TAU * 8);
    // legs relax as the avatar slows to a stop, so the last step ends with the feet together
    w.gait = damp(w.gait, clamp(w.speed / (C.vmax * 0.55), 0, 1), 9, dt);
    w.fade = Math.min(1, w.fade + step / C.fadeIn);
    w.yaw = damp(w.yaw, w.heading * C.headingMax, 4, dt);
    if (w.distance - w.traveled < 0.012) {
      w.traveled = w.distance;
      w.speed = 0;
      enter(w, STATE.TURN);
    }
  } else if (w.state === STATE.TURN) {
    w.fade = 1;
    w.gait = damp(w.gait, 0, 10, dt);
    w.yaw = damp(w.yaw, 0, 5.5, dt);
    if (w.t >= C.turnTime) {
      w.yaw = 0;
      enter(w, STATE.WAVE);
    }
  } else if (w.state === STATE.WAVE) {
    w.gait = damp(w.gait, 0, 10, dt);
    const hold = w.brief ? 0.55 : C.waveHold;
    const total = C.waveRaise + hold + C.waveLower;
    w.waveT += step;
    if (w.t < C.waveRaise) w.wave = smooth(w.t / C.waveRaise);
    else if (w.t < C.waveRaise + hold) w.wave = 1;
    else w.wave = 1 - smooth((w.t - C.waveRaise - hold) / C.waveLower);
    if (w.t >= total) finish(w);
  } else if (w.state === STATE.HOP) {
    const hopTime = w.tap ? TAP_HOP_TIME : C.hopTime;
    w.fade = Math.min(1, w.fade + step / 0.25);
    w.hop = Math.sin(clamp(w.t / hopTime, 0, 1) * Math.PI);
    if (w.t >= hopTime) {
      w.hop = 0;
      if (w.tap) finish(w);
      else enter(w, STATE.WAVE);
    }
  }
}

function smooth(x) {
  const c = clamp(x, 0, 1);
  return c * c * (3 - 2 * c);
}

/**
 * The clip gait. The Walk clip is in place: at timeScale 1 its planted foot slides back at
 * speedPerScale, so the avatar's feet stay put on the ground only when its body moves at
 *   ground speed = timeScale * speedPerScale * modelScale * (the Walk clip's blend weight)
 * and faces the way it travels (walk.travelYaw, from the forest camera rig). The timeline picks
 * the cadence (it ramps from minScale to the cruise pace and then holds, so the legs never move in
 * slow motion) and derives the ground speed from it, using the weight the avatar reported last
 * frame (walk.clipWeight), so the fade-in at the start is covered too. Near the spot it stops with
 * a walk-to-idle blend at an unchanged cadence: the avatar fades Walk out over stopTime by the
 * same smoothstep while the body covers exactly the rest of the path, slowing in step with the
 * shrinking stride and turning toward the child as it settles. The Wave is a clip too, started
 * when the state becomes WAVE.
 *
 * With the studio GLB (`clip.studio`) the whole WALK and TURN run in studioWalk.js instead: Walk_Start,
 * whole half steps of Walk, a phase-synced Walk_Stop_R or _L, the root moved by the sidecar root_speed.
 *
 * clip = { speedPerScale, modelScale, cruiseScale, minScale, rushScale, rampUp, stopTime,
 *          turnTime, waveTime, fadeIn, studio }
 */
function stepClip(w, dt, clip) {
  w.t += dt;
  if (clip.studio && w.sw) {
    if (w.state === STATE.WALK) {
      if (stepStudioWalk(w, dt, clip)) enter(w, STATE.TURN);
      return;
    }
    if (w.state === STATE.TURN) {
      if (stepStudioTurn(w, dt, clip)) {
        w.yaw = 0;
        if (w.rush || w.noWave) finish(w); // the child is already talking (or a mid-meadow leg): no wave
        else enter(w, STATE.WAVE);
      }
      return;
    }
  }
  if (w.state === STATE.WALK) {
    const ground = clip.speedPerScale * clip.modelScale; // units per second at timeScale 1
    const remaining = w.distance - w.traveled;
    w.fade = Math.min(1, w.fade + dt / clip.fadeIn);
    if (!w.stopping) {
      const top = w.rush ? clip.rushScale : clip.cruiseScale;
      const want = clip.minScale + (top - clip.minScale) * smooth(w.t / clip.rampUp);
      w.timeScale = damp(w.timeScale, want, 4, dt); // a late rush speeds up smoothly, not in one frame
      w.speed = w.timeScale * ground * w.clipWeight;
      // A smoothstep fade covers half of what full speed would in the same time.
      if (remaining <= 0.5 * clip.stopTime * w.timeScale * ground) {
        w.stopping = true;
        w.stopT = 0;
        w.stopFrom = w.traveled;
        w.stopDist = remaining;
      } else {
        w.traveled += Math.min(w.speed * dt, remaining);
        w.yaw = damp(w.yaw, w.travelYaw, 4, dt);
        return;
      }
    }
    // Walk-to-idle: covered fraction C(x) = 2x - 2x^3 + x^4, whose slope 2 * (1 - smoothstep(x))
    // follows the Walk weight as the avatar fades it out over stopTime.
    w.stopT += dt;
    const x = Math.min(w.stopT / clip.stopTime, 1);
    const walkLeft = 1 - smooth(x);
    w.speed = ((2 * w.stopDist) / clip.stopTime) * walkLeft;
    w.traveled = w.stopFrom + w.stopDist * (2 * x - 2 * x * x * x + x * x * x * x);
    w.yaw = damp(w.yaw, w.travelYaw * walkLeft, 4, dt);
    if (x >= 1) {
      w.traveled = w.distance;
      w.speed = 0;
      w.stopping = false;
      enter(w, STATE.TURN);
    }
  } else if (w.state === STATE.TURN) {
    w.fade = 1;
    w.yaw = damp(w.yaw, 0, 5.5, dt);
    if (w.t >= clip.turnTime) {
      w.yaw = 0;
      if (w.rush) finish(w); // the child is already talking: no wave
      else enter(w, STATE.WAVE);
    }
  } else if (w.state === STATE.WAVE) {
    if (w.t >= clip.waveTime) finish(w);
  } else if (w.state === STATE.HOP) {
    w.fade = Math.min(1, w.fade + dt / 0.25);
    const hopTime = w.tap ? TAP_HOP_TIME : WALK.hopTime; // avatar-integ: a tap is a short hop, then rest
    w.hop = Math.sin(clamp(w.t / hopTime, 0, 1) * Math.PI);
    if (w.t >= hopTime) {
      w.hop = 0;
      if (w.tap) finish(w);
      else enter(w, STATE.WAVE);
    }
  }
}

// ---------------------------------------------------------------------------------------------
// The rig side. Local axes of the leg bones, checked against avatar-web.glb: for the hip
// (Bone.005 / Bone.006), the shin (leg.r / leg.l) and the foot (Bone.013 / Bone.014) a rotation
// about the bone's local Z swings the leg forward and back, and the left leg is mirrored.
// ---------------------------------------------------------------------------------------------
const AXIS_Z = new Vector3(0, 0, 1);
const swing = new Quaternion(); // per-frame scratch, reused

function qEntry(bone) {
  return bone ? { bone, q: bone.quaternion.clone() } : null;
}

/** Looks up the three leg bones per side. Missing bones just skip the gait for that leg. */
export function buildLegRig(byName) {
  const get = (name) => qEntry(byName.get(name) || byName.get(name.replaceAll('.', '')));
  return {
    right: { hip: get('Bone.005'), shin: get('leg.r'), foot: get('Bone.013') },
    left: { hip: get('Bone.006'), shin: get('leg.l'), foot: get('Bone.014') },
  };
}

function setSwing(e, angle) {
  if (!e) return;
  e.bone.quaternion.copy(e.q).multiply(swing.setFromAxisAngle(AXIS_Z, angle));
}

function playLeg(leg, phase, side, g) {
  const s = Math.sin(phase);
  const lift = Math.max(0, Math.cos(phase)); // foot in the air while the leg swings forward
  const hip = WALK.hip * g * s;
  const knee = -WALK.knee * g * lift * lift;
  const foot = -(hip + knee) * WALK.foot;
  setSwing(leg.hip, hip * side);
  setSwing(leg.shin, knee * side);
  setSwing(leg.foot, foot * side);
}

/**
 * Plays the gait, the waddle and the wave on top of the pose the idle code has just written.
 * `root` is the model's root object, `base` its rest position and rotation as plain numbers.
 */
export function applyWalk(rig, w, base) {
  const g = w.gait;
  const phase = w.cycle;
  const root = base.root;
  if (rig.legs) {
    playLeg(rig.legs.right, phase, 1, g);
    playLeg(rig.legs.left, phase + Math.PI, -1, g);
  }

  const s = Math.sin(phase);
  const c = Math.cos(phase);
  const step = 0.5 + 0.5 * Math.cos(phase * 2); // 1 at mid-stance, 0 at the pass-through
  root.position.set(
    base.x + WALK.swayX * g * c,
    base.y + WALK.bob * g * step + WALK.hopHeight * w.hop,
    base.z,
  );
  root.rotation.set(base.rx, base.ry + w.yaw + WALK.swayYaw * g * s, base.rz + WALK.roll * g * c);

  // arms swing against the legs, with a little pump (the wave arm is handled below)
  const sw = WALK.armSwing * g * s;
  const pump = WALK.armPump * g * Math.abs(c);
  if (rig.armL) {
    rig.armL.bone.rotation.x += sw;
    rig.armL.bone.rotation.z += pump;
  }
  if (rig.armR) {
    rig.armR.bone.rotation.x -= sw;
    rig.armR.bone.rotation.z -= pump;
  }

  // wave: the right arm goes up and the hand wags
  const wv = w.wave;
  if (wv > 0) {
    if (rig.pecR) rig.pecR.bone.rotation.z -= WALK.wavePec * wv;
    if (rig.armR) rig.armR.bone.rotation.z -= WALK.waveArm * wv;
    if (rig.handR) rig.handR.bone.rotation.z += Math.sin(w.waveT * TAU * WALK.waveHz) * WALK.waveHand * wv;
  }
}
