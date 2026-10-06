// The meadow stage of the child's page (src/.../avatar/meadowStage.js). Run with `npm run test:meadowstage`.
// The camera maths are measured on a real three.js PerspectiveCamera with the same setViewOffset call the app makes
// (AvatarLookdev StagedCamera), so the feet are checked on the projection, not re-derived from the formulas under test.
import test from 'node:test';
import assert from 'node:assert/strict';
import { PerspectiveCamera, Vector3 } from 'three';
import { LOOKDEV } from '../src/features/child/components/avatar/lookdev/lookdevConfig.js';
import {
  paintingToScreen,
  pathCentreU,
  screenToPaintingV,
  solveFraming,
} from '../src/features/child/components/avatar/lookdev/stageFraming.js';
import {
  STAGE,
  createStage,
  farDistance,
  homeLift,
  isWide,
  poseAt,
  placeStage,
  setStageInputs,
  stepStage,
  walkerX,
} from '../src/features/child/components/avatar/meadowStage.js';
import { STATE } from '../src/features/child/components/avatar/walkIn.js';

const SIZES = [
  { name: 'phone 390x844', W: 390, H: 844 },
  { name: 'small phone 360x640', W: 360, H: 640 },
  { name: 'tablet 820x1180', W: 820, H: 1180 },
  { name: '16:9 1280x720', W: 1280, H: 720 },
];

function camera(pose, W, H) {
  const cam = new PerspectiveCamera(pose.fov, W / H, 0.1, 50);
  cam.position.set(pose.cx, pose.eye, pose.dist);
  cam.setViewOffset(W, H, 0, pose.viewOffsetY, W, H);
  cam.updateProjectionMatrix();
  cam.updateMatrixWorld(true);
  return (x, y, z) => {
    const p = new Vector3(x, y, z).project(cam);
    return { x: (p.x * 0.5 + 0.5) * W, y: (0.5 - p.y * 0.5) * H };
  };
}

/** The painted path's centre column (px) at screen row y (px). */
function pathX(y, W, H) {
  const v = Math.min(0.95, Math.max(0.55, screenToPaintingV(y, W, H)));
  return paintingToScreen(pathCentreU(v), v, W, H)[0];
}

for (const s of SIZES) {
  test(`call pose is the look-dev framing at ${s.name}`, () => {
    const fr = solveFraming(s.W, s.H);
    const p = poseAt(s.W, s.H, 1, {});
    assert.ok(Math.abs(p.dist - fr.dist) < 1e-9, 'same distance as solveFraming');
    assert.ok(Math.abs(p.yFeet - fr.yFeet) < 1e-6 || Math.abs(p.yFeet - (fr.yH + fr.eye / (fr.dist * 2 * p.halfTan))) < 1e-9);
    assert.equal(p.viewOffsetY, fr.viewOffsetY);
    assert.equal(p.eye, fr.eye, 'eye height never changes');
  });

  test(`the horizon and eye stay fixed across the ease at ${s.name}`, () => {
    const horizon = [];
    for (const m of [0, 0.25, 0.5, 0.75, 1]) {
      const p = poseAt(s.W, s.H, m, {});
      const project = camera(p, s.W, s.H);
      horizon.push(project(0, 0, -1e5).y);
      assert.equal(p.eye, solveFraming(s.W, s.H).eye);
    }
    for (const y of horizon) assert.ok(Math.abs(y - horizon[0]) < 0.5, `horizon drifted: ${horizon.join(', ')}`);
  });

  test(`the home pose is bigger than the call pose on a phone, smaller on a wide window at ${s.name}`, () => {
    const home = poseAt(s.W, s.H, 0, {});
    const call = poseAt(s.W, s.H, 1, {});
    if (isWide(s.W, s.H)) {
      // a wide window keeps the cards in a side panel: he stands whole, a little smaller than in the call
      assert.ok(home.Hf < call.Hf && home.dist > call.dist);
    } else {
      assert.ok(home.Hf >= call.Hf - 1e-9);
      assert.ok(home.dist <= call.dist + 1e-9);
    }
  });

  test(`his feet land on the painted path for every depth at ${s.name}`, () => {
    for (const m of [0, 0.5, 1]) {
      const pose = poseAt(s.W, s.H, m, {});
      const project = camera(pose, s.W, s.H);
      const far = farDistance(s.W, s.H);
      for (const f of [0, 0.25, 0.5, 0.75, 1]) {
        const z = -far * f;
        const x = walkerX(pose, z, s.W, s.H);
        const feet = project(x, 0, z);
        const band = LOOKDEV.framing.pathScreenX;
        const want = Math.min(band[1] * s.W, Math.max(band[0] * s.W, pathX(feet.y, s.W, s.H)));
        assert.ok(
          Math.abs(feet.x - want) < s.W * 0.012,
          `m ${m} z ${z.toFixed(2)}: feet x ${feet.x.toFixed(1)} vs path ${want.toFixed(1)}`,
        );
      }
    }
  });

  test(`the rest spot is the same world point in both poses at ${s.name}`, () => {
    const home = poseAt(s.W, s.H, 0, {});
    const call = poseAt(s.W, s.H, 1, {});
    const hx = walkerX(home, 0, s.W, s.H);
    const cx = walkerX(call, 0, s.W, s.H);
    const fr = solveFraming(s.W, s.H);
    assert.ok(Math.abs(hx - fr.avatarX) < 1e-6 && Math.abs(cx - fr.avatarX) < 1e-6, `${hx} ${cx} ${fr.avatarX}`);
    const rowHome = camera(home, s.W, s.H)(hx, 0, 0).y / s.H;
    assert.ok(Math.abs(rowHome - home.yFeet) < 0.002, `feet row ${rowHome} vs ${home.yFeet}`);
  });

  test(`farDistance stays inside its bounds at ${s.name}`, () => {
    const d = farDistance(s.W, s.H);
    assert.ok(d >= 0 && d <= STAGE.maxFar + 1e-9, String(d));
  });
}

/** Steps a stage with a deterministic walk that finishes legs the moment they are asked for (the scheduler only). */
function simulate(stage, seconds, { W = 390, H = 844, dt = 1 / 60, onFrame = null } = {}) {
  const modes = [stage.mode];
  for (let t = 0; t < seconds; t += dt) {
    stepStage(stage, dt, W, H);
    const w = stage.walk;
    // a stand-in for the avatar canvas: walk the leg at a fixed pace
    if (w.armed && w.state !== STATE.DONE && w.state !== STATE.WAIT0) {
      w.traveled = Math.min(w.distance, w.traveled + 0.5 * dt);
      if (w.traveled >= w.distance) w.state = STATE.DONE;
    } else if (w.armed && w.state === STATE.WAIT0) {
      w.state = STATE.WALK1;
    }
    if (modes[modes.length - 1] !== stage.mode) modes.push(stage.mode);
    if (onFrame) onFrame(stage);
  }
  return modes;
}

test('the camera eases once into the call pose and stays', () => {
  let n = 0;
  const rng = () => ((n += 1) % 10) / 10;
  const stage = createStage({ rng });
  stepStage(stage, 1 / 60, 390, 844);
  assert.equal(stage.m, 0);
  setStageInputs(stage, { phase: 'call', hidden: false, reduced: false });
  const seen = [];
  for (let i = 0; i < 300; i += 1) {
    stepStage(stage, 1 / 60, 390, 844);
    seen.push(stage.m);
  }
  for (let i = 1; i < seen.length; i += 1) assert.ok(seen[i] >= seen[i - 1] - 1e-12, 'monotonic, no overshoot');
  assert.equal(seen[seen.length - 1], 1);
  const steady = seen.slice(-60);
  assert.ok(steady.every((v) => v === 1), 'steady for the rest of the session');
  const reached = seen.findIndex((v) => v >= 1);
  assert.ok(Math.abs(reached / 60 - STAGE.easeSeconds) < 0.1, `eased in ${reached / 60}s`);
});

test('reduced motion jumps straight to the goal pose', () => {
  const stage = createStage({ reduced: true });
  setStageInputs(stage, { phase: 'call', hidden: false, reduced: true });
  stepStage(stage, 1 / 60, 390, 844);
  assert.equal(stage.m, 1);
  setStageInputs(stage, { phase: 'home', hidden: false, reduced: true });
  stepStage(stage, 1 / 60, 390, 844);
  assert.equal(stage.m, 0);
});

test('the call rushes the walk', () => {
  const stage = createStage();
  stepStage(stage, 1 / 60, 390, 844);
  assert.equal(stage.walk.rush, false);
  setStageInputs(stage, { phase: 'call', hidden: false, reduced: false });
  stepStage(stage, 1 / 60, 390, 844);
  assert.equal(stage.walk.rush, true);
});

test('the idle beat goes arrive, rest, away and back, ending at his rest spot', () => {
  const rng = () => 0; // the shortest waits
  const stage = createStage({ rng });
  const modes = simulate(stage, 90);
  assert.deepEqual(modes.slice(0, 8), ['arrive', 'rest', 'pivotAway', 'away', 'linger', 'pivotBack', 'return', 'rest']);
  // wait until a return finishes: z must be exactly the rest spot
  let rested = null;
  simulate(stage, 60, { onFrame: (s) => { if (s.mode === 'rest' && s.wait > 0) rested = s.pz; } });
  assert.ok(rested !== null && Math.abs(rested) < 1e-6, `rest z ${rested}`);
});

test('the pivot never overshoots and never wraps', () => {
  const stage = createStage({ rng: () => 0 });
  let min = 0;
  let max = 0;
  simulate(stage, 120, { onFrame: (s) => { min = Math.min(min, s.facing); max = Math.max(max, s.facing); } });
  assert.ok(min >= -1e-9 && max <= Math.PI + 1e-9, `facing range ${min}..${max}`);
});

test('a call during the idle beat comes back to facing the camera', () => {
  const stage = createStage({ rng: () => 0 });
  simulate(stage, 30, { onFrame: null });
  setStageInputs(stage, { phase: 'call', hidden: false, reduced: false });
  simulate(stage, 20);
  assert.ok(Math.abs(stage.facing) < 0.05 || stage.mode !== 'pivotAway', `mode ${stage.mode} facing ${stage.facing}`);
});

test('nothing walks while the avatar is hidden (chat open)', () => {
  const stage = createStage({ rng: () => 0 });
  setStageInputs(stage, { phase: 'call', hidden: true, reduced: false });
  for (let i = 0; i < 200; i += 1) stepStage(stage, 1 / 60, 390, 844);
  assert.equal(stage.walk.armed, false);
});

// cards-spec (05): the phone Home lift (a vertical lens shift on a phone Home only, faded out by the stroll and the call).
for (const s of SIZES) {
  test(`the Home lift is phone-only, within its bounds, and keeps the head above the key at ${s.name}`, () => {
    const lift = homeLift(s.W, s.H);
    const phone = !isWide(s.W, s.H) && s.W <= STAGE.liftMaxWidth;
    if (!phone) {
      assert.equal(lift, 0);
      return;
    }
    assert.ok(lift > 0 && lift <= STAGE.liftMax + 1e-9, String(lift));
    const p = poseAt(s.W, s.H, 0, {});
    const ears = p.yFeet - p.Hf - lift;
    assert.ok(ears >= STAGE.homeTop - 1e-9, `ears ${ears} stay below the greeting row`);
    // the head clears the key: the ears sit in the upper half of the stage above the cards
    assert.ok(ears * s.H < (s.H - STAGE.cardsPx) * 0.6, `ears at ${ears * s.H}px`);
  });
}

test('the Home lift is full at rest, fades with the stroll, and is gone in the call', () => {
  const W = 390;
  const H = 844;
  const stage = createStage({ rng: () => 0 });
  stepStage(stage, 1 / 60, W, H);
  const full = stage.pose.liftBase;
  assert.ok(full > 0);
  // arrival: far up the path there is no lift, at the rest spot all of it
  stage.base = -stage.far;
  stage.walk.traveled = 0;
  placeStage(stage);
  assert.equal(stage.pose.lift, 0);
  assert.equal(stage.pose.viewOffsetY, stage.pose.baseViewOffsetY);
  const seen = [];
  for (let z = -STAGE.liftFade; z <= 1e-9; z += 0.05) {
    stage.base = z;
    stage.walk.traveled = 0;
    placeStage(stage);
    seen.push(stage.pose.lift);
    assert.ok(Math.abs(stage.pose.viewOffsetY - (stage.pose.baseViewOffsetY + stage.pose.lift * H)) < 1e-9);
  }
  for (let i = 1; i < seen.length; i += 1) assert.ok(seen[i] >= seen[i - 1] - 1e-12, 'blends in monotonically');
  stage.base = 0;
  placeStage(stage);
  assert.ok(Math.abs(stage.pose.lift - full) < 1e-12);
  // the call: liftBase eases to nothing, so the framing is the look-dev one again
  setStageInputs(stage, { phase: 'call', hidden: false, reduced: true });
  stepStage(stage, 1 / 60, W, H);
  assert.equal(stage.pose.lift, 0);
  assert.equal(stage.pose.viewOffsetY, solveFraming(W, H).viewOffsetY);
});

test('with the lift his feet stay on the painted path at every depth (measured on the projection)', () => {
  for (const [W, H] of [[390, 844], [360, 640], [430, 932]]) {
    const stage = createStage({ rng: () => 0 });
    stepStage(stage, 1 / 60, W, H);
    const far = farDistance(W, H);
    for (const f of [0, 0.05, 0.1, 0.25, 0.5, 1]) {
      stage.base = -far * f;
      stage.walk.traveled = 0;
      placeStage(stage);
      const feet = camera(stage.pose, W, H)(stage.px, 0, stage.pz);
      const band = LOOKDEV.framing.pathScreenX;
      const want = Math.min(band[1] * W, Math.max(band[0] * W, pathX(feet.y, W, H)));
      assert.ok(Math.abs(feet.x - want) < W * 0.012, `${W}x${H} z ${stage.pz.toFixed(2)}: feet ${feet.x.toFixed(1)} vs path ${want.toFixed(1)}`);
    }
  }
});
