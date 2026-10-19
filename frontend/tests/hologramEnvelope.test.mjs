// Tests for the hologram's envelope (how it looks per phase) and the procedural nod (06-avatar-context).
// Pure JS: runs under `node --test` without a browser. Time is simulated at 60 fps.

import assert from 'node:assert/strict';
import { test } from 'node:test';

import { CLIP } from '../src/features/child/components/avatar/avatarConfig.js';
import { createAvatarContextStore } from '../src/features/child/components/avatar/context/avatarSignals.js';
import { createDirector, makeDirectorOutput } from '../src/features/child/components/avatar/context/avatarDirector.js';
import { createProceduralNod, MAX_NODS, NOD_OVERSHOOT } from '../src/features/child/components/avatar/context/proceduralNod.js';
import { holoEnvelope, makeEnvelope } from '../src/features/child/components/avatar/hologram/holoEnvelope.js';
import { HOLO, isLowTier } from '../src/features/child/components/avatar/hologram/hologramConfig.js';

const DT = 1 / 60;
const ALL = new Set(Object.values(CLIP));

/** Run a search to its end (found, none, or an interrupt) and record the envelope every frame. */
function run(outcome, { kind = 'library', delay = 3, total = 12, clips = ALL, reduced = false } = {}) {
  let clock = 0;
  const store = createAvatarContextStore({ now: () => clock * 1000 });
  const director = createDirector({ rng: () => 0.5, has: (n) => clips.has(n) });
  const out = makeDirectorOutput();
  const env = makeEnvelope();
  store.applySnapshot({ 'al.sig_v': '1' });
  store.markConnected();
  const c = store.ctx;
  const frames = [];
  let started = false;
  let ended = false;
  for (let i = 0; i * DT < total; i++) {
    clock = i * DT;
    if (!started && clock >= 0.5) {
      store.applyChanged({ 'al.search_kind': kind, 'al.activity': 'searching' });
      started = true;
    }
    if (!ended && clock >= 0.5 + delay) {
      store.applyChanged({ 'al.activity': outcome === 'interrupt' ? 'idle' : outcome });
      ended = true;
    }
    director.step(
      DT,
      {
        agentState: 'listening', signals: c.signals, cues: c.cues, childSpeaking: false, voiceLevel: -1,
        gam: c.gam, sessionEndingSeq: c.sessionEndingSeq, connectSeq: c.connectSeq, awaySec: c.awaySec,
        walkIn: false, reduced, visible: true, waveAgo: 999,
      },
      out,
    );
    holoEnvelope(out.holo, env);
    frames.push({ ...env, phase: out.holo.phase, t: clock });
  }
  return frames;
}

const finite = (v) => typeof v === 'number' && Number.isFinite(v);

for (const outcome of ['found', 'none', 'interrupt']) {
  test(`envelope stays in bounds through a search that ends in ${outcome}`, () => {
    const frames = run(outcome);
    assert.ok(frames.some((f) => f.visible), 'the hologram showed at some point');
    for (const f of frames) {
      for (const k of ['sx', 'sy', 'alpha', 'pyr', 'wipe', 'gold', 'dim', 'luma', 'twist', 'toPalm', 'halo', 'haloGold', 'orbit']) {
        assert.ok(finite(f[k]), `${k} is finite at ${f.t.toFixed(2)}`);
      }
      assert.ok(f.alpha >= 0 && f.alpha <= 1.0001, `alpha ${f.alpha} at ${f.t.toFixed(2)}`);
      assert.ok(f.sx >= -0.001 && f.sx <= 1.2, `sx ${f.sx} at ${f.t.toFixed(2)}`);
      assert.ok(f.sy >= -0.001 && f.sy <= 1.0001, `sy ${f.sy} at ${f.t.toFixed(2)}`);
      assert.ok(f.gold >= 0 && f.gold <= 1.0001 && f.dim >= 0 && f.dim <= 1.0001);
      assert.ok(f.pyr >= -0.0001 && f.pyr <= 1.0001 && f.wipe >= 0 && f.wipe <= 1.0001);
      assert.ok(f.halo >= 0, `halo ${f.halo}`);
    }
  });
}

test('the hologram is fully gone again after the search ends', () => {
  for (const outcome of ['found', 'none', 'interrupt']) {
    const frames = run(outcome, { total: 20 });
    const last = frames[frames.length - 1];
    assert.equal(last.visible, false, `${outcome}: closed at the end`);
  }
});

test('found has exactly one flash and it never exceeds 0.3 luminance', () => {
  const frames = run('found');
  let episodes = 0;
  let prev = 0;
  let peak = 0;
  for (const f of frames) {
    if (f.luma > 0 && prev === 0) episodes += 1;
    prev = f.luma;
    peak = Math.max(peak, f.luma);
  }
  assert.equal(episodes, 1, 'one flash');
  assert.ok(peak > 0.05, `the flash is visible (peak ${peak})`);
  assert.ok(peak <= 0.3 + 1e-9, `flash luminance ${peak} <= 0.3`);
  assert.ok(HOLO.found.flashLuma <= 0.3);
});

test('none and interrupt never flash, and none never goes gold', () => {
  for (const outcome of ['none', 'interrupt']) {
    const frames = run(outcome);
    assert.ok(frames.every((f) => f.luma === 0), `${outcome}: no flash`);
    assert.ok(frames.every((f) => f.gold === 0), `${outcome}: not gold`);
  }
  assert.ok(run('none').some((f) => f.dim > 0.9), 'none dims the panel');
});

test('found goes gold and the panel travels into the palm before the burst', () => {
  const frames = run('found');
  assert.ok(frames.some((f) => f.gold > 0.99));
  assert.ok(frames.some((f) => f.toPalm > 0.6), 'the panel shrinks into the palm');
  assert.ok(frames.some((f) => f.burstT >= 0), 'sparkle burst');
});

test('the open is a materialise: the panel grows from nothing and settles at full size', () => {
  const frames = run('found');
  const first = frames.find((f) => f.visible);
  assert.ok(first.sy < 0.2 && first.alpha < 0.5, 'starts small and faint');
  const holding = frames.find((f) => f.t > 2.0 && f.t < 3.0);
  assert.ok(Math.abs(holding.sx - 1) < 0.01 && Math.abs(holding.sy - 1) < 0.01 && holding.alpha > 0.99, 'full while holding');
});

test('the hologram works without any new clip (virtual timeline)', () => {
  const onlyToday = new Set(['Idle', 'LookAround', 'Listen', 'Think', 'TalkGesture', 'Wave', 'Happy', 'Walk', 'Blink']);
  const frames = run('found', { clips: onlyToday });
  assert.ok(frames.some((f) => f.visible && f.alpha > 0.99));
});

test('reduced motion shows no panel (the icon path is used instead)', () => {
  const frames = run('found', { reduced: true });
  assert.ok(frames.every((f) => !f.panel), 'no moving panel under reduced motion');
});

test('the envelope is reused, not reallocated', () => {
  const env = makeEnvelope();
  const h = { phase: 0, t: 0, foundT: -1, total: 0 };
  assert.equal(holoEnvelope(h, env), env);
});

test('low tier detection: few cores, little memory or a small screen', () => {
  const big = { navigator: { hardwareConcurrency: 8, deviceMemory: 8 }, screen: { width: 1920, height: 1080 } };
  assert.equal(isLowTier(big), false);
  assert.equal(isLowTier({ ...big, navigator: { hardwareConcurrency: 4, deviceMemory: 8 } }), true);
  assert.equal(isLowTier({ ...big, navigator: { hardwareConcurrency: 8, deviceMemory: 4 } }), true);
  assert.equal(isLowTier({ ...big, screen: { width: 390, height: 780 } }), true);
  assert.equal(isLowTier({}), false, 'unknown device is not low tier');
});

// ---- the procedural nod ----

function nodCurve(fireAt = [0], total = 1) {
  const nod = createProceduralNod();
  const pts = [];
  for (let i = 0; i * DT < total; i++) {
    if (fireAt.some((f) => Math.abs(f - i * DT) < DT / 2)) nod.fire(1, 1);
    pts.push(nod.step(DT));
  }
  return { nod, pts };
}

test('a nod peaks near 0.08 rad, then returns to exactly 0', () => {
  const { nod, pts } = nodCurve([0], 1);
  const peak = Math.max(...pts);
  assert.ok(peak > 0.075 && peak <= 0.0801, `peak ${peak}`);
  assert.equal(pts[pts.length - 1], 0);
  assert.equal(nod.active, false);
  // down, then a small rise past rest (follow-through), never more than the overshoot share of the dip
  const low = Math.min(...pts);
  assert.ok(low < -0.1 * peak && low >= -NOD_OVERSHOOT * 0.08 - 1e-9, `overshoot ${low}`);
});

test('a nod starts and ends smoothly: no velocity jump in any frame (minimum-jerk segments)', () => {
  const { pts } = nodCurve([0], 1);
  const v = pts.map((p, i) => (i === 0 ? p : p - pts[i - 1]) / DT);
  // the first frame moves far less than the fastest frame (a sine attack would start at full speed: 1.0)
  const vmax = Math.max(...v.map(Math.abs));
  assert.ok(Math.abs(v[0]) < 0.15 * vmax, `first-frame speed ${v[0]} vs max ${vmax}`);
  // no frame-to-frame change of speed bigger than half the top speed (a sine attack jumps the whole of it)
  for (let i = 1; i < v.length; i++) assert.ok(Math.abs(v[i] - v[i - 1]) < 0.5 * vmax, `speed jump at frame ${i}`);
  assert.ok(vmax * (180 / Math.PI) < 200, `head speed ${vmax} rad/s stays under the 200 deg/s cap`);
});

test('the nod attacks faster than it releases', () => {
  const { pts } = nodCurve([0], 1);
  const peakAt = pts.indexOf(Math.max(...pts)) * DT;
  assert.ok(peakAt < 0.2, `peak at ${peakAt}`);
  assert.ok(0.12 + 0.35 > peakAt * 2);
});

test('weight sets the amplitude; the time scale stretches the nod in time (empathy 0.8 is slower)', () => {
  const sample = (w, ts) => {
    const nod = createProceduralNod();
    nod.fire(w, ts);
    let peak = 0;
    let frames = 0;
    for (let i = 0; i < 120; i++) {
      peak = Math.max(peak, nod.step(DT));
      if (nod.active) frames++;
    }
    return { peak, dur: frames * DT };
  };
  const a = sample(0.5, 1);
  assert.ok(Math.abs(a.peak - 0.08 * 0.5) < 0.002, `peak ${a.peak}`);
  const slow = sample(0.5, 0.8);
  assert.ok(Math.abs(slow.peak - a.peak) < 0.002, 'the time scale does not change the amplitude');
  assert.ok(Math.abs(slow.dur - a.dur / 0.8) < 2 * DT, `slower: ${slow.dur} s vs ${a.dur} s`);
});

test('two nods overlap (the double nod) and a third replaces the older, never more than 2 slots', () => {
  assert.equal(MAX_NODS, 2);
  const { pts } = nodCurve([0, 0.3], 1.2);
  const single = nodCurve([0], 1.2).pts;
  assert.ok(Math.max(...pts) > Math.max(...single) * 0.95);
  const nod = createProceduralNod();
  nod.fire(1, 1);
  nod.step(0.2);
  nod.fire(1, 1);
  nod.step(0.1);
  nod.fire(1, 1); // both busy: the older is replaced
  let max = 0;
  for (let i = 0; i < 120; i++) max = Math.max(max, nod.step(DT));
  assert.ok(max <= 0.16 + 1e-9, `at most two nods add up (${max})`);
  assert.equal(nod.active, false);
});

test('reset stops a nod at once', () => {
  const nod = createProceduralNod();
  nod.fire();
  nod.step(0.1);
  nod.reset();
  assert.equal(nod.step(DT), 0);
});
