// The painted-meadow stage of the child's page: where Sadiq walks on the path before the talk, and the one camera
// move into the call framing when the talk starts. Plain numbers and the walk state, no React, no WebGL, so node
// can test it (tests/meadowStage.test.mjs).
//
// Two poses of the same level camera (stageFraming.js):
//   home  Sadiq a little larger than in the call (photo 2: head high, hips behind the cards). The camera is further
//         forward; a walk starts far up the path and arrives at his rest spot.
//   call  the framing the look-dev stage already solves for the whole stage (photo 1: full body above the controls).
// `m` goes 0 to 1 once, when the talk starts, and the camera then stays exactly where it is for the whole session:
// there is no zoom while he speaks or listens (conversationShot.js stays on the /page showcase only).
//
// Only the camera distance and its sideways shift change between the poses. The horizon (lens shift) and the eye
// height stay, so the painted horizon never moves. Sadiq's rest spot is fixed in the world; the camera slides
// sideways with its distance so the spot stays on the painted path in both poses. A walker at depth d is put on the
// path's centre at the row his feet project to (the painting does not move with the camera, so the path is looked
// up in the picture, not in the world).
//
// Nothing here may contain scripture or any other Islamic text; it is pure animation data.
import { LOOKDEV } from './lookdev/lookdevConfig.js';
import { paintingToScreen, pathCentreU, screenToPaintingV, solveFraming } from './lookdev/stageFraming.js';
import { STATE, beginLeg, briefWave, createWalk } from './walkIn.js';

export const STAGE = {
  homeBoost: 1.12, // Sadiq's height on Home as a multiple of his height in the call (a phone: photo 2's bust above the key)
  homeBoostWide: 0.8, // the same on a wide window: the cards sit in a side panel, so he stands whole and a little smaller than in the call
  homeTop: 0.2, // fraction of the stage height kept clear above his ears on Home (the greeting row)
  // cards-spec (05): the phone Home lift. The cards (the green key, the level card) cover the lower half of the stage, so at his
  // plain Home height the key cuts him at the chin. A vertical lens shift (the camera's view offset, applied to the 3D
  // only: the painting stays put) raises him until his ears sit at homeEarsKey of the way down to the key's top, so the
  // head and the chest stand above the key (photo 2: ears at 0.42 of the key's row). It is a phone-only offset that
  // fades out with the stroll and with the call.
  cardsPx: 351, // CSS px: the Home cards block under the stage (key + level card + quest card + tab bar), the same on every phone width
  homeEarsKey: 0.43, // where the ears should sit, as a fraction of the stage height above the key (H - cardsPx)
  liftMax: 0.14, // the largest lift, as a fraction of the stage height
  liftMaxWidth: 600, // CSS px: wider stages (tablet, desktop) are not lifted
  liftFade: 0.6, // world units of the walk away from his rest spot over which the lift fades to nothing
  easeSeconds: 1.3, // the one camera move into the call framing
  maxFar: 3.0, // world units: the longest walk (about 6.5 s at the relaxed pace)
  minRowV: 0.575, // painting row: his feet never go higher than this (the path table starts at 0.55)
  armFrames: 24, // frames drawn with the avatar before the walk may start
  idleBeat: { first: [9, 13], gap: [14, 22], away: 2.4, awayMin: 0.8, linger: 0.7, pivotRate: 3 }, // pivotRate: rad/s on the spot, never faster than the walk's turnRate of 3
};

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = (x) => {
  const c = clamp(x, 0, 1);
  return c * c * (3 - 2 * c);
};

/** The two end poses for a W x H stage (CSS px): numbers the camera and the walker read. */
export function isWide(W, H) {
  return W / H >= 1.15;
}

function endPoses(W, H) {
  const F = LOOKDEV.framing;
  const call = solveFraming(W, H);
  const halfTan = Math.tan((F.fov * Math.PI) / 360);
  const hfHome = isWide(W, H)
    ? Math.max(call.Hf * STAGE.homeBoostWide, 0.2)
    : clamp(Math.min(call.Hf * STAGE.homeBoost, (call.yH - STAGE.homeTop) / (1 - call.k)), call.Hf, 5);
  const distHome = F.charHeight / (hfHome * 2 * halfTan);
  return { call, halfTan, hfHome, distHome, aspect: W / H };
}

/**
 * The camera and the stage numbers at mix `m` (0 home, 1 call). Writes into `out` (allocated once by the caller).
 * { fov, dist, eye, cx, viewOffsetY, restX, yH, halfTan, aspect, yFeet, feetX, Hf, m, liftBase, lift }
 * `liftBase` is the phone Home lift at this mix (fraction of the stage height); `lift` is the part applied now, which
 * placeStage sets from the walker's depth (0 here, so a pose on its own is exactly the look-dev framing).
 */
export function poseAt(W, H, m, out = {}) {
  const F = LOOKDEV.framing;
  const e = endPoses(W, H);
  const { call } = e;
  const dist = lerp(e.distHome, call.dist, clamp(m, 0, 1));
  const yFeet = call.yH + call.eye / (dist * 2 * e.halfTan);
  const feetX = feetScreenX(yFeet, W, H);
  out.fov = F.fov;
  out.dist = dist;
  out.eye = call.eye;
  out.restX = call.avatarX;
  out.cx = call.avatarX - (feetX - 0.5) * 2 * dist * e.halfTan * e.aspect;
  out.viewOffsetY = call.viewOffsetY;
  out.baseViewOffsetY = call.viewOffsetY;
  out.liftBase = homeLift(W, H, e) * (1 - clamp(m, 0, 1));
  out.lift = 0;
  out.yH = call.yH;
  out.halfTan = e.halfTan;
  out.aspect = e.aspect;
  out.yFeet = yFeet;
  out.feetX = feetX;
  out.Hf = F.charHeight / (dist * 2 * e.halfTan);
  out.m = m;
  return out;
}

/** The phone Home lift (fraction of the stage height, 0 when not wanted) that puts his ears at STAGE.homeEarsKey of the stage above the key. */
export function homeLift(W, H, e = endPoses(W, H)) {
  if (isWide(W, H) || W > STAGE.liftMaxWidth) return 0;
  const yFeetHome = e.call.yH + e.call.eye / (e.distHome * 2 * e.halfTan);
  const earsHome = yFeetHome - e.hfHome;
  const earsGoal = Math.max(STAGE.homeTop, (STAGE.homeEarsKey * (H - STAGE.cardsPx)) / H);
  return clamp(earsHome - earsGoal, 0, STAGE.liftMax);
}

/** Screen x (fraction of the width) of the painted path's centre at the row of stage fraction `yFeet`. */
export function feetScreenX(yFeet, W, H) {
  const v = screenToPaintingV(yFeet * H, W, H);
  const [px] = paintingToScreen(pathCentreU(clamp(v, 0.55, 0.95)), v, W, H);
  const band = LOOKDEV.framing.pathScreenX;
  return clamp(px / W, band[0], band[1]);
}

/** World x that puts a walker at world z (z <= 0 is further up the path) on the painted path under `pose`. */
export function walkerX(pose, z, W, H) {
  const d = pose.dist - z;
  const yFeet = pose.yH + pose.eye / (d * 2 * pose.halfTan) - (pose.lift || 0); // cards-spec (05): the lift raises his feet on screen
  const fx = feetScreenX(yFeet, W, H);
  return pose.cx + (fx - 0.5) * 2 * d * pose.halfTan * pose.aspect;
}

/** How far up the path (world units) the arrival starts: his feet stay on a painted path row and the walk stays short. */
export function farDistance(W, H) {
  const e = endPoses(W, H);
  const yMin = paintingToScreen(0.5, STAGE.minRowV, W, H)[1] / H;
  const rho = (e.call.k * e.hfHome) / Math.max(yMin - e.call.yH, 1e-3);
  return clamp((rho - 1) * e.distHome, 0, STAGE.maxFar);
}

/** A fresh stage. `walk` is the shared walk state the avatar canvas steps (walkIn.js). */
export function createStage({ reduced = false, rng = Math.random } = {}) {
  const walk = createWalk('walk', 'default');
  walk.distanceLocked = true; // this stage plans every distance itself
  return {
    walk,
    rng,
    reduced,
    phase: 'home', // 'home' | 'call', set by the page
    hidden: false,
    ready: false, // the avatar has drawn STAGE.armFrames frames; the walk may start
    frames: 0,
    t: 0, // linear 0..1 progress of the camera move
    m: 0, // the eased mix
    W: 0,
    H: 0,
    pose: poseAt(390, 844, 0, {}),
    far: 0, // world units of the arrival, planned on the first sized frame
    mode: 'arrive', // arrive | rest | pivotAway | away | linger | pivotBack | return
    base: 0, // world z where the current leg began
    dir: 1, // +1 toward the camera, -1 away
    away: 0, // distance of the current wander
    facing: 0, // radians about the vertical: 0 faces the camera, PI turns his back
    facingGoal: 0,
    beats: 0, // idle beats so far: odd ones are a stroll up the path and back, even ones a wave
    wait: 0, // seconds until the next idle beat / linger left
    planned: false,
    // placed each frame for the avatar group
    px: 0,
    pz: 0,
  };
}

function rand(stage, [lo, hi]) {
  return lo + (hi - lo) * stage.rng();
}

/** The page's inputs for the next frame (phase 'home' | 'call', hidden, reduced motion). */
export function setStageInputs(stage, { phase, hidden, reduced }) {
  stage.phase = phase;
  stage.hidden = hidden;
  stage.reduced = reduced;
}

/** World position of the avatar (writes stage.px, stage.pz) from the walk's progress, and the lift that goes with it. */
export function placeStage(stage) {
  const w = stage.walk;
  const z = stage.base + stage.dir * w.traveled;
  stage.pz = z;
  // cards-spec (05): the phone Home lift is full at his rest spot and gone 'liftFade' world units up the path, so the
  // stroll blends it out (the arrival blends it in over the last stretch). Applied as the camera's lens shift.
  const pose = stage.pose;
  if (pose.liftBase > 0) {
    pose.lift = pose.liftBase * (1 - smooth(-z / STAGE.liftFade));
    pose.viewOffsetY = pose.baseViewOffsetY + pose.lift * stage.H;
  } else {
    pose.lift = 0;
    pose.viewOffsetY = pose.baseViewOffsetY;
  }
  stage.px = walkerX(stage.pose, z, stage.W, stage.H);
}

/** The camera and the idle beats for one frame. Call it once per frame before the avatar is placed. */
export function stepStage(stage, dt, W, H) {
  const w = stage.walk;
  const sized = W > 0 && H > 0;
  if (sized) {
    stage.W = W;
    stage.H = H;
  }
  if (!sized) return;

  // the one camera move: only ever toward the call framing, and back only when the talk is over (home)
  const goal = stage.phase === 'call' ? 1 : 0;
  if (stage.reduced) stage.t = goal;
  else if (stage.t < goal) stage.t = Math.min(goal, stage.t + dt / STAGE.easeSeconds);
  else if (stage.t > goal) stage.t = Math.max(goal, stage.t - dt / STAGE.easeSeconds);
  stage.m = smooth(stage.t);
  poseAt(W, H, stage.m, stage.pose);

  // plan the arrival once the size is known
  if (!stage.planned) {
    stage.planned = true;
    stage.far = farDistance(W, H);
    stage.base = -stage.far;
    stage.dir = 1;
    w.distance = stage.far;
  }
  w.rush = stage.phase === 'call';

  stage.frames += 1; // this runs from the avatar's own frame loop, so the model is mounted
  if (stage.frames >= STAGE.armFrames) stage.ready = true;
  if (!w.armed && stage.ready && !stage.hidden) w.armed = true;

  const idle = w.state === STATE.DONE;
  const B = STAGE.idleBeat;
  switch (stage.mode) {
    case 'arrive':
      if (idle) {
        stage.mode = 'rest';
        stage.wait = rand(stage, B.first);
      }
      break;
    case 'rest':
      if (idle && stage.phase === 'home' && !stage.reduced && !stage.hidden) {
        stage.wait -= dt;
        if (stage.wait <= 0) {
          stage.beats += 1;
          stage.away = clamp(Math.min(B.away, stage.far * 0.75), 0, B.away);
          if (stage.beats % 2 === 0 || stage.away < B.awayMin) {
            // every other beat he just waves at the child (the short idle wave), then waits again
            briefWave(w);
            stage.wait = rand(stage, B.gap);
          } else {
            stage.facingGoal = Math.PI;
            stage.mode = 'pivotAway';
          }
        }
      }
      break;
    case 'pivotAway':
      if (stage.phase === 'call') {
        stage.facingGoal = 0;
        stage.mode = 'rest';
      } else if (Math.abs(stage.facing - Math.PI) < 0.03 && idle) {
        stage.base = 0;
        stage.dir = -1;
        beginLeg(w, stage.away);
        stage.mode = 'away';
      }
      break;
    case 'away':
      if (idle) {
        stage.wait = B.linger;
        stage.mode = 'linger';
      }
      break;
    case 'linger':
      stage.wait -= dt;
      if (stage.wait <= 0) {
        stage.facingGoal = 0;
        stage.mode = 'pivotBack';
      }
      break;
    case 'pivotBack':
      if (Math.abs(stage.facing) < 0.03 && idle) {
        stage.base = -stage.away;
        stage.dir = 1;
        beginLeg(w, stage.away);
        stage.mode = 'return';
      }
      break;
    case 'return':
      if (idle) {
        stage.mode = 'rest';
        stage.wait = rand(stage, B.gap);
      }
      break;
    default:
      break;
  }

  // the pivot on the spot (an idle turn about the vertical), eased and rate limited
  const diff = stage.facingGoal - stage.facing;
  if (Math.abs(diff) > 1e-4) {
    const want = diff * (1 - Math.exp(-6 * dt));
    const max = B.pivotRate * dt;
    stage.facing += clamp(want, -max, max);
    if (Math.abs(stage.facingGoal - stage.facing) < 0.01) stage.facing = stage.facingGoal;
  }
  placeStage(stage);
}
