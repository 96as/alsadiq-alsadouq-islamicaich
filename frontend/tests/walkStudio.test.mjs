// Run with: npm run test:walk   (node's built-in test runner, no extra dependency)
// Checks the studio walk-in (WP1): the embedded root_speed data against the sidecar, the whole-step plan,
// phase-synced stops, planted-foot root motion, the turn rules (Bible 3.3, W10), the clip hand-offs of the
// animator, and that frame rate and a late rush change nothing.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import * as THREE from 'three';
import { AvatarAnimator } from '../src/features/child/components/avatar/AvatarAnimator.js';
import {
  CLIP,
  MODEL_SCALE,
  WALK_CLIP,
  WALK_TRANSITIONS as T,
} from '../src/features/child/components/avatar/avatarConfig.js';
import {
  LEG,
  START_DIST,
  STOP_L_DIST,
  STOP_R_DIST,
  planWalk,
  rootDistance,
  turnToward,
} from '../src/features/child/components/avatar/studioWalk.js';
import { STATE, WALK, createWalk, replayWalk, stepWalk } from '../src/features/child/components/avatar/walkIn.js';
import {
  AVATAR_CAM,
  DEFAULT_ELEV,
  TURN_BLEND,
  avatarCamPose,
  bearingOver,
  elevationOver,
  walkCamAz,
  walkCamElev,
} from '../src/features/child/components/avatar/avatarCam.js';

const sidecar = JSON.parse(
  readFileSync(new URL('../public/models/avatar/avatar-animated.json', import.meta.url), 'utf8'),
);
const clipMeta = (name) => sidecar.clips.find((c) => c.name === name);
const PARAMS = { ...WALK_CLIP, modelScale: MODEL_SCALE, waveTime: 2.8, studio: true };
const HALF = WALK_CLIP.cycle / 2;

test('the embedded root_speed arrays and durations are the sidecar ones', () => {
  for (const [key, name] of [['start', 'Walk_Start'], ['stopR', 'Walk_Stop_R'], ['stopL', 'Walk_Stop_L']]) {
    const meta = clipMeta(name);
    assert.ok(meta, `${name} is in the sidecar`);
    assert.deepEqual(T[key].root, meta.root_speed_m_s, `${name} root_speed`);
    assert.ok(Math.abs(T[key].duration - meta.duration_s) < 1e-6, `${name} duration`);
    assert.equal(T[key].root.length, Math.round(meta.duration_s * 30) + 1, `${name} has N+1 entries`);
  }
  const walk = clipMeta('Walk');
  assert.equal(walk.frames, 16);
  assert.ok(Math.abs(walk.duration_s - WALK_CLIP.cycle) < 1e-5);
  assert.equal(sidecar.walk.speed_m_per_s, T.steadySpeed);
  assert.equal(sidecar.walk.stride_m_per_cycle, WALK_CLIP.stridePerCycle);
  assert.equal(WALK_CLIP.speedPerScale * WALK_CLIP.cycle, WALK_CLIP.stridePerCycle, '0.525 m/s x 0.5333 s = 0.28 m');
  assert.ok(Math.abs(T.halfStep * 2 - WALK_CLIP.stridePerCycle) < 1e-9);
  assert.equal(WALK_CLIP.cruiseScale, 1.0);
  assert.equal(WALK_CLIP.rushScale, 1.35);
});

test('root travel of the transitions is the integral of root_speed (piecewise constant per frame)', () => {
  const sum = (a, n) => a.slice(0, n).reduce((x, y) => x + y, 0) / 30;
  assert.ok(Math.abs(START_DIST - sum(T.start.root, 15)) < 1e-9);
  assert.ok(Math.abs(STOP_R_DIST - sum(T.stopR.root, 21)) < 1e-9);
  assert.ok(Math.abs(STOP_L_DIST - sum(T.stopL.root, 21)) < 1e-9);
  // splitting the integral anywhere gives the same total
  const cut = 0.2373;
  const split = rootDistance(T.stopL.root, 0, cut) + rootDistance(T.stopL.root, cut, T.stopL.duration);
  assert.ok(Math.abs(split - STOP_L_DIST) < 1e-12);
  assert.ok(START_DIST > 0.04 && START_DIST < 0.07);
});

test('the plan is whole half steps and lands within half a half step of the wanted path', () => {
  for (let m = 3; m < 7; m += 0.037) {
    const p = planWalk(m);
    assert.ok(p.err <= T.halfStep / 2 + 0.03, `error ${p.err} at ${m} m`);
    const stop = p.right ? STOP_R_DIST : STOP_L_DIST;
    assert.ok(Math.abs(p.total - (START_DIST + p.n * T.halfStep + stop)) < 1e-12);
    assert.equal(p.right, p.n % 2 === 0, 'even n stops from the right heel strike, odd n from the left');
  }
  const dm = WALK_CLIP.distance / MODEL_SCALE;
  assert.ok(planWalk(dm).err < 0.08);
});

test('turnToward never exceeds the rate and settles on the target', () => {
  let yaw = 0;
  let prev = 0;
  let worst = 0;
  for (let i = 0; i < 200; i++) {
    yaw = turnToward(yaw, 1.2, 3, 1 / 60);
    worst = Math.max(worst, Math.abs(yaw - prev) * 60);
    prev = yaw;
  }
  assert.ok(worst <= 3 + 1e-9, `peak turn rate ${worst}`);
  assert.ok(Math.abs(yaw - 1.2) < 1e-3);
});

/** Plays the walk-in on its own clock, like the avatar's frame loop does. */
function simulate({
  fps = 60,
  jitter = 0,
  rushAt = -1,
  travelYaw = () => 0,
  distance = WALK_CLIP.distance,
  lock = false,
  maxT = 60,
}) {
  const w = createWalk('walk');
  replayWalk(w);
  w.distance = distance;
  w.distanceLocked = lock;
  const frames = [];
  let t = 0;
  let seed = 7;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  while (t < maxT) {
    let dt = 1 / fps;
    if (jitter) dt = Math.min(0.1, dt * (1 + jitter * (rnd() * 2 - 1)));
    t += dt;
    if (rushAt >= 0 && t >= rushAt) w.rush = true;
    w.travelYaw = travelYaw(t, w);
    const before = w.traveled;
    stepWalk(w, dt, { reduced: false, clip: PARAMS });
    const sw = w.sw;
    frames.push({
      t,
      dt,
      state: w.state,
      leg: sw ? sw.leg : -1,
      legT: sw ? sw.legT : 0,
      walkClock: sw ? sw.walkClock : 0,
      traveled: w.traveled,
      advance: w.traveled - before,
      yaw: w.yaw,
      twist: sw ? sw.twist : 0,
      lead: sw ? sw.lead : 0,
      yawRate: sw ? sw.yawRate : 0,
      ts: w.timeScale,
      fade: w.fade,
    });
    if (w.state === STATE.WAVE || w.state === STATE.DONE) break;
  }
  return { w, frames };
}

test('the walk starts with Walk_Start, plays whole half steps, stops on a contact and lands on the spot', () => {
  const { w, frames } = simulate({});
  const sw = w.sw;
  assert.equal(frames[0].leg, LEG.START, 'the first frame is in Walk_Start');
  assert.ok(frames.some((f) => f.leg === LEG.CRUISE) || sw.n === 0);
  assert.ok(Math.abs(sw.stopAt - sw.n * HALF) < 1e-9, 'the stop begins exactly on a heel strike');
  const phase = Math.round(sw.stopPhase);
  assert.ok(phase === 0 || phase === 8, `stop phase ${sw.stopPhase} must be Walk f0 (R) or f8 (L)`);
  assert.equal(sw.side, phase === 0 ? 'R' : 'L');
  assert.ok(Math.abs(w.traveled - w.distance) < 1e-9, 'it ends exactly on the spot');
  assert.equal(w.state, STATE.WAVE);
});

test('root motion in every leg is exactly what the clips need (planted feet, W2 and W9 by construction)', () => {
  const { w, frames } = simulate({ fps: 120 });
  const ms = MODEL_SCALE;
  for (const f of frames) {
    if (f.leg === LEG.CRUISE && f.walkClock > 0 && f.state === STATE.WALK) {
      // a frame that stays inside the cruise leg moves at 0.525 m/s x timeScale (the first frame of a leg mixes)
    }
  }
  // total distance = Start + n half steps + stop, at any pace
  const sw = w.sw;
  const stop = sw.side === 'R' ? STOP_R_DIST : STOP_L_DIST;
  const expected = (START_DIST + sw.n * T.halfStep + stop) * ms;
  assert.ok(Math.abs(w.traveled - expected) < 1e-9);
  // cruise frames: speed matches the clip's ground speed
  const cruise = frames.filter((f, i) => i > 0 && f.leg === LEG.CRUISE && frames[i - 1].leg === LEG.CRUISE && f.state === STATE.WALK);
  assert.ok(cruise.length > 100);
  for (const f of cruise) {
    const want = T.steadySpeed * ms * f.ts; // units per second
    assert.ok(Math.abs(f.advance / f.dt - want) < 1e-6 * Math.max(1, want) + 1e-9, `cruise speed ${f.advance / f.dt} vs ${want}`);
  }
  // transition frames: speed is the sidecar root_speed (x timeScale x modelScale), frame by frame
  const inStart = frames.filter((f, i) => i > 0 && f.leg === LEG.START && frames[i - 1].leg === LEG.START);
  for (const f of inStart) {
    const t0 = f.legT - f.dt * f.ts;
    const want = rootDistance(T.start.root, Math.max(t0, 0), f.legT) * ms;
    assert.ok(Math.abs(f.advance - want) < 1e-9, 'Start root travel');
  }
  const stopFrames = frames.filter((f, i) => i > 0 && f.leg === LEG.STOP && frames[i - 1].leg === LEG.STOP && f.legT < 0.7);
  const rs = sw.side === 'R' ? T.stopR.root : T.stopL.root;
  for (const f of stopFrames) {
    const t0 = f.legT - f.dt * f.ts;
    const want = rootDistance(rs, Math.max(t0, 0), f.legT) * ms;
    assert.ok(Math.abs(f.advance - want) < 1e-9, 'Stop root travel');
  }
  // the root is still when Start begins and when the stop ends (no gliding while the feet are planted)
  assert.equal(T.start.root[0], 0);
  assert.ok(T.stopR.root[T.stopR.root.length - 1] === 0 && T.stopL.root[T.stopL.root.length - 1] === 0);
});

test('frame rate, jitter and a late rush change neither the plan nor where the stop begins', () => {
  const ref = simulate({ fps: 60 });
  for (const opts of [{ fps: 30 }, { fps: 144 }, { fps: 60, jitter: 0.6 }, { fps: 20, jitter: 0.5 }, { fps: 60, rushAt: 3.0 }, { fps: 60, rushAt: 0.2 }]) {
    const r = simulate(opts);
    assert.equal(r.w.sw.n, ref.w.sw.n, JSON.stringify(opts));
    assert.ok(Math.abs(r.w.sw.stopAt - r.w.sw.n * HALF) < 1e-9, `${JSON.stringify(opts)} stop on a contact`);
    assert.ok(Math.abs(r.w.traveled - r.w.distance) < 1e-9, `${JSON.stringify(opts)} lands on the spot`);
    assert.ok(Math.abs(r.w.distance - ref.w.distance) < 1e-12);
  }
});

test('a rush speeds the walk up to at most 1.35 and stops with the next contact', () => {
  const slow = simulate({ fps: 60 });
  const fast = simulate({ fps: 60, rushAt: 2.0 });
  const top = Math.max(...fast.frames.map((f) => f.ts));
  assert.ok(top <= WALK_CLIP.rushScale + 1e-9 && top > 1.3, `top timeScale ${top}`);
  assert.ok(Math.max(...slow.frames.map((f) => f.ts)) <= 1 + 1e-9);
  assert.ok(fast.frames.at(-1).t < slow.frames.at(-1).t - 0.5, 'a rush arrives sooner');
  // no frame jumps: the ground speed changes smoothly when the rush starts
  const speeds = fast.frames.filter((f) => f.leg === LEG.CRUISE).map((f) => f.advance / f.dt);
  for (let i = 2; i < speeds.length; i++) assert.ok(Math.abs(speeds[i] - speeds[i - 1]) < 0.02, 'smooth rush');
});

test('turn: at most 3 rad/s walking, head leads by 0.10 to 0.15 s, residual turn at the stop at most 15 deg', () => {
  // the path bends: travel direction swings from 0 to 0.5 rad then back to 0.12 rad (7 deg) at the end
  const travel = (t) => (t < 1 ? 0 : t < 3 ? 0.5 * Math.min((t - 1) / 0.5, 1) : 0.12);
  const { w, frames } = simulate({ fps: 60, travelYaw: travel });
  const walking = frames.filter((f) => f.state === STATE.WALK);
  const maxRate = Math.max(...walking.map((f) => Math.abs(f.yawRate)));
  assert.ok(maxRate <= WALK_CLIP.turnRate + 1e-9, `peak yaw rate ${maxRate}`);
  let leadChecked = 0;
  for (const f of walking) {
    if (Math.abs(f.yawRate) > 0.3) {
      const lead = f.lead / f.yawRate;
      assert.ok(lead >= 0.10 && lead <= 0.15, `head lead ${lead}`);
      leadChecked++;
    }
  }
  assert.ok(leadChecked > 5, 'a real turn was measured');
  const sw = w.sw;
  assert.ok(Math.abs(sw.stopYaw) <= WALK_CLIP.residualMax, `yaw at the stop ${sw.stopYaw}`);
  // chest and neck carry the turn: facing (root + twist) reaches the camera within 15 deg through the stop
  const afterStop = frames.filter((f) => f.leg === LEG.STOP);
  const lastStop = afterStop.at(-1);
  assert.ok(Math.abs(lastStop.yaw + lastStop.twist) <= WALK_CLIP.residualMax, 'facing at the end of the stop');
  assert.ok(Math.max(...afterStop.map((f) => Math.abs(f.twist))) <= WALK_CLIP.residualMax + 1e-9);
  // the root then turns at most 0.6 rad/s
  const turn = frames.filter((f) => f.state === STATE.TURN);
  let worst = 0;
  for (let i = 1; i < turn.length; i++) worst = Math.max(worst, Math.abs(turn[i].yaw - turn[i - 1].yaw) / turn[i].dt);
  assert.ok(worst <= WALK_CLIP.residualRate + 1e-9, `root turn after the stop ${worst}`);
  assert.equal(w.yaw, 0);
  // the chest and neck hand the turn back as the root catches up: facing stays put
  for (const f of turn) assert.ok(Math.abs(f.yaw + f.twist) <= 0.02 + Math.abs(f.yaw) * 0, 'facing stays on the camera');
});

test('a pinned distance keeps the preview distance and still stops on a contact', () => {
  const { w } = simulate({ fps: 60, distance: 3.9, lock: true });
  assert.equal(w.distance, 3.9);
  assert.ok(Math.abs(w.traveled - 3.9) < 1e-9);
  assert.ok(Math.abs(w.sw.stopAt - w.sw.n * HALF) < 1e-9);
  assert.ok(w.sw.k > 0.5 && w.sw.k < 1.5);
});

test('reduced motion goes straight to the spot', () => {
  const w = createWalk('walk');
  replayWalk(w);
  stepWalk(w, 1 / 60, { reduced: false, clip: PARAMS });
  assert.equal(w.state, STATE.WALK);
  stepWalk(w, 1 / 60, { reduced: true, clip: PARAMS });
  assert.equal(w.state, STATE.DONE);
});

test('the legacy gait is untouched when the GLB has no transitions', () => {
  const w = createWalk('walk');
  replayWalk(w);
  w.clipWeight = 1; // the avatar reports the Walk weight; the old gait moves by it
  const legacy = { speedPerScale: 0.525, modelScale: MODEL_SCALE, cruiseScale: 1.2, minScale: 0.55, rushScale: 2.0, rampUp: 0.8, stopTime: 0.9, turnTime: 0.8, waveTime: 2.8, fadeIn: 0.7, studio: false };
  let t = 0;
  while (t < 30 && w.state !== STATE.WAVE && w.state !== STATE.DONE) {
    stepWalk(w, 1 / 60, { reduced: false, clip: legacy });
    t += 1 / 60;
  }
  assert.equal(w.sw, null);
  assert.ok(t < 30);
});

// ---- the animator: transitions as a layer ---------------------------------------------------------

/** A clip that moves the model root's x from `from` to `to` over `duration`: stands in for a body clip. */
function pose(name, from, to, duration) {
  return new THREE.AnimationClip(name, duration, [new THREE.NumberKeyframeTrack('.position[x]', [0, duration], [from, to])]);
}
function rigClips() {
  return [
    pose('Idle', 0, 0, 8),
    pose('Walk', 10, 10, 16 / 30),
    pose('Walk_Start', 0, 10, 0.5),
    pose('Walk_Stop_R', 10, 0, 0.7),
    pose('Walk_Stop_L', 10, 0, 0.7),
    pose('Listen', 0, 0, 4),
    pose('Wave', 0, 0, 2),
    pose('Blink', 0, 0, 0.3),
  ];
}

test('animator: Walk_Start blends in over Idle, hands over to Walk f0 without a fade, a stop cuts in and ends on Idle', () => {
  const root = new THREE.Object3D();
  const a = new AvatarAnimator(root, rigClips(), { rng: () => 0.5 });
  assert.ok(a.hasStudioWalk);
  assert.ok(!a.loops.has('Walk_Start'), 'transitions are not body loops');
  a.update(0);
  // Start: 0.1 s blend-in
  a.startTransition(CLIP.walkStart, { blendIn: 0.1 });
  a.setTransitionTime(0);
  a.update(1 / 60);
  assert.ok(a.transitionName === CLIP.walkStart);
  let sum = a.loops.get('Idle').action.weight + a.trans.get('Walk_Start').action.weight;
  assert.ok(Math.abs(sum - 1) < 1e-9, 'weights add up to 1 during the blend');
  for (let i = 0; i < 12; i++) a.update(1 / 60);
  assert.equal(a.trans.get('Walk_Start').action.weight, 1);
  assert.equal(a.loops.get('Idle').action.weight, 0);
  a.setTransitionTime(0.5);
  a.update(0);
  assert.ok(Math.abs(root.position.x - 10) < 1e-6, 'Start ends on the Walk pose');
  // hand over to Walk at f0, no fade
  a.endTransition(CLIP.walk, 0);
  a.update(0);
  assert.equal(a.transitionName, '');
  assert.equal(a.loops.get('Walk').action.weight, 1);
  assert.equal(a.loops.get('Idle').action.weight, 0);
  assert.equal(a.baseName, 'Walk');
  // the timeline sets the Walk clock; the clip follows it
  a.setLoopTime(CLIP.walk, 0.2);
  a.update(1 / 60);
  assert.ok(Math.abs(a.loopTime(CLIP.walk) - 0.2) < 1e-9, 'the walk-in owns the Walk clock');
  a.update(1 / 60);
  assert.ok(a.loopTime(CLIP.walk) > 0.2, 'and it runs on by itself when not placed');
  // a stop cuts in at once (no blend) and ends on Idle f0
  a.startTransition(CLIP.walkStopL, { blendIn: 0 });
  a.setTransitionTime(0);
  a.update(1 / 60);
  assert.equal(a.trans.get('Walk_Stop_L').action.weight, 1);
  assert.equal(a.loops.get('Walk').action.weight, 0);
  a.setTransitionTime(0.7);
  a.update(0);
  assert.ok(Math.abs(root.position.x) < 1e-6, 'the stop ends on the Idle pose');
  a.endTransition(CLIP.idle, 0);
  a.update(0);
  assert.equal(a.loops.get('Idle').action.weight, 1);
  assert.equal(a.loops.get('Walk').action.weight, 0);
  assert.equal(a.loopTime(CLIP.idle), 0);
});

test('animator: no idle glance fires while a transition plays', () => {
  const root = new THREE.Object3D();
  const a = new AvatarAnimator(root, [...rigClips(), pose('LookAround', 0, 0, 6)], { rng: () => 0 });
  a.glanceTimer = 0.01;
  a.startTransition(CLIP.walkStart, { blendIn: 0.1 });
  a.update(0.05);
  assert.equal(a.shotName, '', 'no glance over Walk_Start');
  a.cancelTransition();
  a.update(0.05);
  assert.equal(a.shotName, 'LookAround', 'glances resume afterwards');
});

test('animator: a GLB without the transitions is not a studio walk', () => {
  const clips = rigClips().filter((c) => !c.name.startsWith('Walk_'));
  const a = new AvatarAnimator(new THREE.Object3D(), clips);
  assert.equal(a.hasStudioWalk, false);
  assert.equal(a.startTransition(CLIP.walkStart), false);
});

test('the avatar fades in standing on Idle f0 and Walk_Start is fully visible when it steps off (W9)', () => {
  assert.equal(WALK_CLIP.holdIn, WALK_CLIP.fadeIn, 'the hold lasts exactly as long as the fade');
  assert.ok(WALK_CLIP.fadeIn <= 0.35 && WALK_CLIP.fadeIn >= 0.25);
  const { frames } = simulate({});
  const held = frames.filter((f) => f.leg === LEG.START && f.legT === 0 && f.t <= WALK_CLIP.holdIn + 1 / 60);
  assert.ok(held.length >= Math.floor(WALK_CLIP.holdIn * 60) - 2, 'Walk_Start waits on f0 during the hold');
  assert.ok(held.every((f) => f.advance === 0), 'the root does not move during the hold');
  const firstMove = frames.find((f) => f.legT > 0);
  assert.ok(firstMove.fade >= 0.999, `the avatar is fully opaque when Walk_Start starts (fade ${firstMove.fade})`);
  assert.ok(firstMove.t >= WALK_CLIP.holdIn - 1 / 60, 'the first clip frame is after the hold');
});

test('avatarCamPose: the default elevation is the default camera exactly, an orbit keeps the feet pixel and the distance', () => {
  const d = avatarCamPose(DEFAULT_ELEV, -0.13);
  assert.deepEqual(d.pos, AVATAR_CAM.pos);
  assert.deepEqual(d.look, AVATAR_CAM.look);
  assert.deepEqual(avatarCamPose(null, -0.13).pos, AVATAR_CAM.pos);
  const feetX = -0.13;
  const lowElev = (9 * Math.PI) / 180;
  const p = avatarCamPose(lowElev, feetX);
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  const feet = [feetX, 0, 0];
  assert.ok(Math.abs(dist(p.pos, feet) - dist(AVATAR_CAM.pos, feet)) < 1e-9, 'the distance to the feet is kept');
  assert.ok(Math.abs(dist(p.look, feet) - dist(AVATAR_CAM.look, feet)) < 1e-9, 'the look point orbits too');
  // elevation of the camera over the feet is the asked one (relative to the default, same horizontal direction)
  const e0 = Math.atan2(AVATAR_CAM.pos[1], Math.hypot(AVATAR_CAM.pos[0] - feetX, AVATAR_CAM.pos[2]));
  const e1 = Math.atan2(p.pos[1], Math.hypot(p.pos[0] - feetX, p.pos[2]));
  assert.ok(Math.abs(e1 - e0 - (lowElev - DEFAULT_ELEV)) < 1e-9);
  // the feet stay in the same place of the view: the angle between the view axis and the feet direction is unchanged
  const ang = (cam) => {
    const ax = cam.look.map((v, i) => v - cam.pos[i]);
    const fx = feet.map((v, i) => v - cam.pos[i]);
    const dot = ax[0] * fx[0] + ax[1] * fx[1] + ax[2] * fx[2];
    return Math.acos(dot / Math.hypot(...ax) / Math.hypot(...fx));
  };
  assert.ok(Math.abs(ang(p) - ang(AVATAR_CAM)) < 1e-9, 'the feet keep their screen position');
  // a lower camera sees the ground more edge-on: a 0.1 m step back covers less of the screen's vertical
  assert.ok(p.pos[1] < AVATAR_CAM.pos[1]);
});

test('walkCamElev: the forest elevation while it walks, a blend back in TURN, the default camera afterwards', () => {
  const w = createWalk('walk');
  replayWalk(w);
  w.distance = 4;
  const raw = (9 * Math.PI) / 180;
  assert.equal(walkCamElev(w, raw), raw, 'waiting at the far end');
  w.state = STATE.WALK;
  w.traveled = 1;
  assert.equal(walkCamElev(w, raw), raw, 'walking');
  w.state = STATE.TURN;
  w.traveled = w.distance;
  w.t = 0;
  assert.ok(Math.abs(walkCamElev(w, raw) - raw) < 1e-12, 'TURN starts where the walk ended');
  w.t = TURN_BLEND / 2;
  const mid = walkCamElev(w, raw);
  assert.ok(mid > raw && mid < DEFAULT_ELEV, 'half way back');
  w.t = TURN_BLEND;
  assert.ok(Math.abs(walkCamElev(w, raw) - DEFAULT_ELEV) < 1e-12, 'TURN ends on the default camera');
  w.state = STATE.WAVE;
  assert.equal(walkCamElev(w, raw), null, 'the talk shot is the default camera');
  w.state = STATE.DONE;
  assert.equal(walkCamElev(w, raw), null);
  assert.ok(Math.abs(elevationOver(0, 0.9, 3.2, 0, 0, 0) - DEFAULT_ELEV) < 1e-12);
});

test('avatarCamPose azimuth: a turn about the vertical through the feet keeps distance, elevation and the feet pixel', () => {
  const feetX = -0.13;
  const feet = [feetX, 0, 0];
  assert.deepEqual(avatarCamPose(null, feetX, undefined, 0).pos, AVATAR_CAM.pos, 'zero azimuth is the default camera');
  const az = 0.2;
  const p = avatarCamPose(null, feetX, undefined, az);
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  assert.ok(Math.abs(dist(p.pos, feet) - dist(AVATAR_CAM.pos, feet)) < 1e-9);
  assert.ok(Math.abs(p.pos[1] - AVATAR_CAM.pos[1]) < 1e-12, 'the height does not change');
  assert.ok(Math.abs(p.look[1] - AVATAR_CAM.look[1]) < 1e-12);
  // the camera swings by the asked azimuth about the vertical through the feet (toward -x for a positive azimuth:
  // the avatar's yaw is measured the other way round from the forest's bearing)
  const bearing = Math.atan2(p.pos[0] - feetX, p.pos[2]);
  assert.ok(Math.abs(bearing - (Math.atan2(AVATAR_CAM.pos[0] - feetX, AVATAR_CAM.pos[2]) - az)) < 1e-9);
  // both together stay rigid about the feet: the feet keep their view-space coordinates
  const q = avatarCamPose((9 * Math.PI) / 180, feetX, undefined, az);
  assert.ok(Math.abs(dist(q.pos, feet) - dist(AVATAR_CAM.pos, feet)) < 1e-9);
  assert.ok(Math.abs(dist(q.look, feet) - dist(AVATAR_CAM.look, feet)) < 1e-9);
});

test('walkCamAz: follows the forest camera bearing while it walks, blends to zero in TURN, none afterwards', () => {
  const w = createWalk('walk');
  replayWalk(w);
  w.distance = 4;
  const raw = bearingOver(0.5, 4, 0, 0);
  assert.ok(raw > 0 && raw < 0.2);
  w.state = STATE.WALK;
  w.traveled = 1;
  assert.equal(walkCamAz(w, raw), raw);
  w.state = STATE.TURN;
  w.traveled = w.distance;
  w.t = TURN_BLEND;
  assert.ok(Math.abs(walkCamAz(w, raw)) < 1e-12);
  w.state = STATE.WAVE;
  assert.equal(walkCamAz(w, raw), null);
});
