// WP4 acting layer: mouth shaping, stress detection, speech head, face accents, studio blinks.
// Pure modules only (no three.js, no audio). The fixture is three real Arabic ElevenLabs lines
// run through the lip-sync front end (viseme weights, level, stress per frame at about 60 fps).
// Run: npm run test:acting
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { MouthShaper } from '../src/features/child/components/avatar/acting/mouthShaping.js';
import { StressDetector } from '../src/features/child/components/avatar/acting/stressDetector.js';
import { SpeechHead, nodCurve } from '../src/features/child/components/avatar/acting/speechHead.js';
import { FaceAccents } from '../src/features/child/components/avatar/acting/faceAccents.js';
import { StudioBlinkScheduler, gammaSample } from '../src/features/child/components/avatar/acting/blinkTiming.js';
import { mulberry32, SecondOrder } from '../src/features/child/components/avatar/acting/dynamics.js';
import { HEAD, JAW_STUDIO, MORPH_GAIN, OPEN_BUDGET, BLINK_STUDIO } from '../src/features/child/components/avatar/acting/actingConfig.js';
import { VI } from '../src/features/child/components/avatar/lipsync/visemes.js';

const traces = JSON.parse(readFileSync(new URL('./fixtures/viseme-traces.json', import.meta.url), 'utf8'));
const clips = Object.entries(traces);
const pct = (arr, p) => {
  const s = [...arr].sort((a, b) => a - b);
  return s[Math.min(s.length - 1, Math.floor(p * s.length))];
};
const note = (t, msg) => t.diagnostic(msg);

/** Run a shaper over a clip and collect the jaw trace and the worst per-frame values. */
function runShaper(clip, opts = {}) {
  const shaper = new MouthShaper(opts);
  const jaws = [];
  const activeJaws = [];
  const frames = [];
  let prev = 0;
  for (const f of clip.frames) {
    const dt = Math.max(1 / 240, f.t - prev || 1 / 60);
    prev = f.t;
    const morph = shaper.update(dt, f.w, { level: f.level, stress: f.stress, speaking: true, active: !!f.active });
    jaws.push(shaper.jaw);
    if (f.active) activeJaws.push(shaper.jaw);
    frames.push({ f, jaw: shaper.jaw, morph: Float32Array.from(morph) });
  }
  return { jaws, activeJaws, frames, shaper };
}

test('fixture has real, non-trivial clips', () => {
  assert.ok(clips.length >= 3);
  for (const [, c] of clips) assert.ok(c.frames.length > 120);
});

test('jaw stays inside 0..max and never goes NaN', () => {
  for (const [, clip] of clips) {
    const { jaws } = runShaper(clip);
    for (const j of jaws) {
      assert.ok(Number.isFinite(j));
      assert.ok(j >= 0 && j <= JAW_STUDIO.max + 1e-9);
    }
  }
});

test('M1: opening distribution while voiced', (t) => {
  const all = [];
  for (const [name, clip] of clips) {
    const { activeJaws } = runShaper(clip);
    note(t, `${name}: p50 ${pct(activeJaws, 0.5).toFixed(3)} p90 ${pct(activeJaws, 0.9).toFixed(3)} max ${Math.max(...activeJaws).toFixed(3)} rad`);
    all.push(...activeJaws);
  }
  const p50 = pct(all, 0.5);
  const p90 = pct(all, 0.9);
  note(t, `all voiced: p50 ${p50.toFixed(3)} p90 ${p90.toFixed(3)} rad (cm of chin at 3.64 cm/rad: ${(p50 * 3.64).toFixed(2)} / ${(p90 * 3.64).toFixed(2)})`);
  assert.ok(p50 >= 0.07, 'median voiced jaw is at least the speech floor');
  // 0.15 before the fix pass. The quicker release (28/s, bible 6.4) lets the jaw dip between syllables,
  // which is the 3-6 Hz rhythm the reviewer asked for, and costs about 0.015 rad of the loudest peaks.
  assert.ok(p90 >= 0.13, 'loud syllables open the jaw clearly');
  assert.ok(p90 <= JAW_STUDIO.max);
});

test('M1b: the audio-path mass lift opens the jaw further on weak vowel poses', (t) => {
  const stats = (massLift) => {
    const all = [];
    for (const [, clip] of clips) all.push(...runShaper(clip, { audioPath: true, audio: { massLift } }).activeJaws);
    return { p50: pct(all, 0.5), p90: pct(all, 0.9) };
  };
  const off = stats(false);
  const on = stats(true);
  note(t, 'lift off p50 ' + off.p50.toFixed(3) + ' p90 ' + off.p90.toFixed(3) + ', on p50 ' + on.p50.toFixed(3) + ' p90 ' + on.p90.toFixed(3) + ' rad');
  // 1.4 before the fix pass; the quicker release (28/s) lets a lifted pose fall back sooner: 1.2 today.
  assert.ok(on.p50 > off.p50 * 1.2);
  assert.ok(on.p90 >= 0.22 && on.p90 <= JAW_STUDIO.max); // 0.25 before the fix pass, see above
});

test('M2: speech floor keeps the mouth alive inside a phrase', () => {
  const clip = clips[0][1];
  const { frames } = runShaper(clip);
  // After the first voiced frame and before the last, short gaps never close below the floor
  // unless PP is closing the lips.
  const first = frames.findIndex((x) => x.f.active);
  let lastActive = -1;
  frames.forEach((x, i) => {
    if (x.f.active) lastActive = i;
  });
  let sinceActive = 99;
  let checked = 0;
  for (let i = first; i <= lastActive; i++) {
    const x = frames[i];
    sinceActive = x.f.active ? 0 : sinceActive + 1 / 60;
    if (sinceActive < JAW_STUDIO.speechGap * 0.5 && x.f.w[VI.PP] < JAW_STUDIO.ppGateAt - JAW_STUDIO.ppGateLead && i > first + 6) {
      checked++;
      assert.ok(x.jaw >= JAW_STUDIO.speechFloor * 0.5, `frame ${i} jaw ${x.jaw}`);
    }
  }
  assert.ok(checked > 20);
});

test('M3: PP gate clamps the jaw so the lips can seal', () => {
  const shaper = new MouthShaper({ version: 1 });
  const open = new Float32Array(14);
  open[VI.aa] = 1;
  for (let i = 0; i < 30; i++) shaper.update(1 / 60, open, { level: 1, speaking: true, active: true });
  assert.ok(shaper.jaw > 0.4, `open jaw ${shaper.jaw}`);
  const pp = new Float32Array(14);
  pp[VI.PP] = 1;
  let frames = 0;
  while (shaper.jaw > shaper.ppJaw + 1e-6 && frames < 10) {
    shaper.update(1 / 60, pp, { level: 1, speaking: true, active: true });
    frames++;
  }
  assert.ok(frames <= 2, `jaw reaches the PP gate within two frames (took ${frames})`);
  assert.ok(shaper.jaw <= JAW_STUDIO.ppJawV1 + 1e-6);
  // V2 allows more.
  shaper.setVersion(2);
  assert.equal(shaper.ppJaw, JAW_STUDIO.ppJawV2);
});

test('M4: while PP >= ppGateAt the jaw is at most the V1 PP limit, at any PP weight', () => {
  // MOTION-BIBLE 6.1 and M4: any jaw with PP tears the V1 lower lip, so a partial PP (0.3-0.6, the
  // usual audio-path value) must clamp as hard as a full one.
  for (const ppw of [JAW_STUDIO.ppGateAt, 0.4, 0.5, 0.75, 1]) {
    const shaper = new MouthShaper({ version: 1, audioPath: true });
    const open = new Float32Array(14);
    open[VI.aa] = 1;
    for (let i = 0; i < 30; i++) shaper.update(1 / 60, open, { level: 1, speaking: true, active: true });
    const w = new Float32Array(14);
    w[VI.PP] = ppw;
    w[VI.aa] = 1 - ppw;
    shaper.update(1 / 60, w, { level: 1, speaking: true, active: true });
    assert.ok(shaper.jaw <= JAW_STUDIO.ppJawV1 + 1e-6, `PP ${ppw}: jaw ${shaper.jaw}`);
  }
});

test('M4: PP never exceeds the weight the lip-sync asked for, closures are not amplified', () => {
  for (const version of [1, 2]) {
    for (const [, clip] of clips) {
      const { frames } = runShaper(clip, { version });
      for (const { f, morph } of frames) {
        assert.ok(morph[VI.PP] <= f.w[VI.PP] + 1e-6);
        assert.ok(morph[VI.FF] <= f.w[VI.FF] + 1e-6);
        assert.ok(morph[VI.SS] <= f.w[VI.SS] + 1e-6);
      }
    }
  }
});

test('M5: gains and caps follow the mesh version table', () => {
  for (const version of [1, 2]) {
    for (const [, clip] of clips) {
      const { frames } = runShaper(clip, { version });
      const table = MORPH_GAIN[version];
      for (const { morph } of frames) {
        for (const [name, [, cap]] of Object.entries(table)) assert.ok(morph[VI[name]] <= cap + 1e-6, `${name} ${morph[VI[name]]} > ${cap}`);
      }
    }
  }
});

test('M6: open budget, a wide jaw and a wide aa never stack', () => {
  for (const version of [1, 2]) {
    const { frames } = runShaper(clips[1][1], { version });
    for (const { jaw, morph } of frames) {
      const allowed = OPEN_BUDGET[version].aa - jaw / JAW_STUDIO.budgetRef;
      assert.ok(morph[VI.aa] <= Math.max(0, allowed) + 1e-6, `aa ${morph[VI.aa]} > ${allowed} at jaw ${jaw}`);
    }
  }
});

test('M7: shaping output is smooth (no frame-to-frame pops)', (t) => {
  let worst = 0;
  for (const [, clip] of clips) {
    const { jaws } = runShaper(clip);
    for (let i = 1; i < jaws.length; i++) worst = Math.max(worst, Math.abs(jaws[i] - jaws[i - 1]));
  }
  note(t, `largest jaw step per frame ${worst.toFixed(4)} rad (${(worst * 60).toFixed(2)} rad/s)`);
  assert.ok(worst < 0.2, `jaw step ${worst}`);
});

test('audio path holds a PP seal for at least 70 ms', () => {
  const shaper = new MouthShaper({ audioPath: true });
  const pp = new Float32Array(14);
  const none = new Float32Array(14);
  pp[VI.PP] = 1;
  shaper.update(1 / 60, pp, { speaking: true, active: true });
  let held = 0;
  for (let i = 0; i < 12; i++) {
    shaper.update(1 / 60, none, { speaking: true, active: true });
    if (shaper.work[VI.PP] >= 0.89) held++;
  }
  assert.ok(held >= 3 && held <= 5, `held ${held} frames`);
});

test('audio path vowel hold keeps a floor after a vowel fades', () => {
  const shaper = new MouthShaper({ audioPath: true });
  const v = new Float32Array(14);
  v[VI.aa] = 0.8;
  shaper.update(1 / 60, v, { speaking: true, active: true });
  v[VI.aa] = 0;
  shaper.update(1 / 60, v, { speaking: true, active: true });
  assert.ok(shaper.work[VI.aa] >= 0.4);
});

test('stress detector: events on real clips are sparse, spaced and end with a phrase end', (t) => {
  for (const [name, clip] of clips) {
    const det = new StressDetector();
    const accents = [];
    let onsets = 0;
    let phraseEnds = 0;
    let prev = 0;
    for (const f of clip.frames) {
      const dt = Math.max(1 / 240, f.t - prev || 1 / 60);
      prev = f.t;
      const ev = det.update(dt, f.level, true);
      if (ev.onset) onsets++;
      if (ev.accent) accents.push(f.t);
      if (ev.phraseEnd) phraseEnds++;
    }
    for (let i = 1; i < accents.length; i++) assert.ok(accents[i] - accents[i - 1] >= STRESS_MIN_GAP - 0.02, `${name} accents too close`);
    const perSec = accents.length / clip.dur;
    note(t, `${name}: ${accents.length} accents in ${clip.dur.toFixed(1)} s (${perSec.toFixed(2)}/s), ${onsets} onsets, ${phraseEnds} phrase ends`);
    assert.ok(accents.length >= 1, `${name}: at least one accent`);
    assert.ok(perSec <= 1 / STRESS_MIN_GAP + 0.01);
  }
});
const STRESS_MIN_GAP = 0.6;

test('stress detector: flat loudness gives no accents, a gap gives a phrase end', () => {
  const det = new StressDetector();
  let accents = 0;
  for (let i = 0; i < 600; i++) if (det.update(1 / 60, 0.5, true).accent) accents++;
  assert.ok(accents <= 1, `flat input gave ${accents} accents`);
  let ended = false;
  for (let i = 0; i < 120; i++) if (det.update(1 / 60, 0, true).phraseEnd) ended = true;
  assert.ok(ended);
});

test('stress detector: announce() raises an early accent', () => {
  const det = new StressDetector();
  det.update(1 / 60, 0.5, true);
  det.announce(0.8);
  const ev = det.update(1 / 60, 0.5, true);
  assert.ok(ev.accent && ev.strength === 0.8);
});

test('nod curve goes down, overshoots slightly and returns to exactly zero', () => {
  const amp = 0.05;
  assert.equal(nodCurve(0, amp, 0.12, 0.26), 0);
  assert.ok(Math.abs(nodCurve(0.12, amp, 0.12, 0.26) - amp) < 1e-9);
  let min = 0;
  for (let t = 0; t < 1; t += 0.005) min = Math.min(min, nodCurve(t, amp, 0.12, 0.26));
  assert.ok(min < 0 && min > -amp * 0.2, `overshoot ${min}`);
  assert.equal(nodCurve(1, amp, 0.12, 0.26), 0);
});

test('speech head: bounded, smooth, only while speaking, and 0.4x when reduced', (t) => {
  const run = (reduced) => {
    const sh = new SpeechHead({ rng: mulberry32(7) });
    let peak = 0;
    let step = 0;
    let prev = 0;
    for (let i = 0; i < 60 * 20; i++) {
      sh.update(1 / 60, { speaking: true, level: 0.8, state: 'speaking', reduced });
      const p = sh.head.pitch + sh.neck.pitch;
      peak = Math.max(peak, Math.abs(p));
      if (i > 0) step = Math.max(step, Math.abs(p - prev));
      prev = p;
    }
    return { peak, step };
  };
  const full = run(false);
  const red = run(true);
  note(t, `speech pitch peak ${full.peak.toFixed(3)} rad (${((full.peak * 180) / Math.PI).toFixed(1)} deg), reduced ${red.peak.toFixed(3)}, max step ${full.step.toFixed(4)}`);
  assert.ok(full.peak > 0.01 && full.peak < 0.11);
  assert.ok(red.peak < full.peak * 0.6);
  assert.ok(full.step < 0.01);
  const idle = new SpeechHead({ rng: mulberry32(7) });
  for (let i = 0; i < 300; i++) idle.update(1 / 60, { speaking: false, state: 'oneshot' });
  assert.ok(Math.abs(idle.head.pitch) < 1e-9 && Math.abs(idle.head.yaw) < 1e-9);
});

test('accent nods respect the gap and the amplitude range', () => {
  const sh = new SpeechHead({ rng: mulberry32(3) });
  const starts = [];
  for (let i = 0; i < 60 * 10; i++) {
    const before = sh.nods;
    sh.update(1 / 60, { speaking: true, level: 0.8, accent: i % 20 === 0, accentStrength: 1, state: 'speaking' });
    if (sh.nods !== before) starts.push(sh.time);
  }
  assert.ok(starts.length >= 4);
  for (let i = 1; i < starts.length; i++) assert.ok(starts[i] - starts[i - 1] >= HEAD.nodGap[0] + 0.3);
  assert.ok(sh.nodAmp >= HEAD.nodMin && sh.nodAmp <= HEAD.nodMax + 1e-9);
});

test('drift is scaled by state: zero for one-shots and the walk', () => {
  for (const state of ['oneshot', 'walk']) {
    const sh = new SpeechHead({ rng: mulberry32(5) });
    let peak = 0;
    for (let i = 0; i < 600; i++) {
      sh.update(1 / 60, { speaking: false, state });
      peak = Math.max(peak, Math.abs(sh.head.yaw), Math.abs(sh.neck.yaw));
    }
    assert.equal(peak, 0);
  }
});

test('ear flicks happen every 4 to 9 s and the spring settles', () => {
  const sh = new SpeechHead({ rng: mulberry32(11) });
  for (let i = 0; i < 60 * 60; i++) sh.update(1 / 60, { speaking: false, state: 'idle' });
  assert.ok(sh.flicks >= 6 && sh.flicks <= 16, `flicks ${sh.flicks} in 60 s`);
  const spring = new SecondOrder(4, 0.35, 0);
  let peak = 0;
  for (let i = 0; i < 600; i++) peak = Math.max(peak, spring.update(1 / 60, i < 7 ? 0.07 : 0));
  assert.ok(Math.abs(spring.y) < 1e-3);
  assert.ok(peak > 0.02);
});

test('face accents: flash amplitude range, none when reduced, lids and cheeks bounded', () => {
  const fa = new FaceAccents({ rng: mulberry32(2), config: { browChance: 1 } });
  let peak = 0;
  for (let i = 0; i < 120; i++) {
    const o = fa.update(1 / 60, { accent: i === 0, accentStrength: 1, speaking: true });
    peak = Math.max(peak, o.browUp);
  }
  assert.ok(peak >= 0.35 && peak <= 0.6 + 1e-9, `peak ${peak}`);
  const quiet = new FaceAccents({ rng: mulberry32(2), config: { browChance: 1 } });
  let qp = 0;
  for (let i = 0; i < 120; i++) qp = Math.max(qp, quiet.update(1 / 60, { accent: i === 0, speaking: true, reduced: true }).browUp);
  assert.equal(qp, 0);
  const lid = new FaceAccents({ rng: mulberry32(2) });
  let l = 0;
  let c = 0;
  for (let i = 0; i < 120; i++) {
    const o = lid.update(1 / 60, { jaw: 0.5, lookDown: 1, pp: 1, aa: 1, level: 1, speaking: true });
    l = Math.max(l, o.lid);
    c = Math.max(c, o.cheek);
  }
  assert.ok(l > 0.05 && l <= 0.35 + 1e-9, `lid ${l}`);
  assert.ok(c > 0.1 && c <= 1);
});

test('face accents: question end and empathy lift the inner brow and release', () => {
  const fa = new FaceAccents({ rng: mulberry32(2) });
  let v = 0;
  for (let i = 0; i < 90; i++) v = fa.update(1 / 60, { questionEnd: 1, speaking: true }).browInnerUp;
  assert.ok(v > 0.25 && v <= 0.3 + 1e-6);
  for (let i = 0; i < 90; i++) v = fa.update(1 / 60, { speaking: false }).browInnerUp;
  assert.ok(v < 0.01);
});

test('blinks: gamma intervals have the right mean, spread and minimum gap', (t) => {
  const rng = mulberry32(42);
  const xs = [];
  for (let i = 0; i < 4000; i++) xs.push(gammaSample(2.5, 3.5 / 2.5, rng));
  const mean = xs.reduce((a, b) => a + b, 0) / xs.length;
  const sd = Math.sqrt(xs.reduce((a, b) => a + (b - mean) ** 2, 0) / xs.length);
  note(t, `gamma(2.5) mean ${mean.toFixed(2)} sd ${sd.toFixed(2)} (theory 3.50 / ${(3.5 / Math.sqrt(2.5)).toFixed(2)})`);
  assert.ok(Math.abs(mean - 3.5) < 0.2);
  assert.ok(Math.abs(sd - 3.5 / Math.sqrt(2.5)) < 0.3);
});

test('blinks: scheduler rate by state, 1.2 s minimum, about 10% doubles', (t) => {
  const sim = (state, seconds) => {
    const b = new StudioBlinkScheduler({ rng: mulberry32(9) });
    b.setState(state);
    const starts = [];
    let last = b.blinks;
    let time = 0;
    for (let i = 0; i < seconds * 60; i++) {
      time += 1 / 60;
      b.update(1 / 60, { stress: 0 });
      if (b.blinks !== last) {
        starts.push(time);
        last = b.blinks;
      }
    }
    return starts;
  };
  const idle = sim('idle', 1800);
  const talk = sim('speaking', 1800);
  const gaps = (s) => s.slice(1).map((x, i) => x - s[i]);
  const meanOf = (a) => a.reduce((x, y) => x + y, 0) / a.length;
  const doubleFrac = (s) => gaps(s).filter((g) => g < 1.0).length / gaps(s).length;
  note(t, `idle ${(1800 / idle.length).toFixed(2)} s/blink, speaking ${(1800 / talk.length).toFixed(2)} s/blink, doubles ${(doubleFrac(idle) * 100).toFixed(1)}%`);
  assert.ok(meanOf(gaps(talk)) < meanOf(gaps(idle)), 'speaking blinks more often');
  assert.ok(Math.abs(1800 / idle.length - 3.5 * 0.9) < 0.6, `idle mean ${1800 / idle.length}`);
  const nonDouble = gaps(idle).filter((g) => g >= 1.0);
  assert.ok(Math.min(...nonDouble) >= BLINK_STUDIO.minGap - 1e-6);
  const d = doubleFrac(idle);
  assert.ok(d > 0.05 && d < 0.17, `double fraction ${d}`);
  assert.ok(Math.min(...gaps(idle)) >= 0.36 - 0.02, 'double blinks start at least 0.36 s apart');
});

// --- WP4 fix pass: the timed path (closure snap) and the syllable chew --------------------------

/** Weights with a few visemes set, everything else 0. */
const weights = (o) => {
  const w = new Float32Array(14);
  for (const [k, v] of Object.entries(o)) w[VI[k]] = v;
  return w;
};

test('timed path: a PP at 0.6 or more is shown as a full closure and the jaw stays shut', () => {
  const shaper = new MouthShaper({ audioPath: false });
  const dt = 1 / 60;
  let morphPP = 0;
  for (let i = 0; i < 40; i++) shaper.update(dt, weights({ aa: 0.8 }), { level: 1, speaking: true, active: true });
  for (let i = 0; i < 12; i++) {
    const m = shaper.update(dt, weights({ PP: 0.65 }), { level: 1, speaking: true, active: true });
    morphPP = Math.max(morphPP, m[VI.PP]);
  }
  assert.ok(morphPP >= 0.95, `PP written ${morphPP}`);
  assert.ok(shaper.jaw <= 0.03 + 1e-9, `jaw ${shaper.jaw} rad while sealed`);
});

test('timed path: a one-frame PP is kept for at least minMs, a PP below snapAt is left alone', () => {
  const dt = 1 / 60;
  const shaper = new MouthShaper({ audioPath: false });
  shaper.update(dt, weights({ PP: 0.8 }), { speaking: true, active: true });
  let held = 1;
  for (let i = 0; i < 12; i++) {
    const m = shaper.update(dt, weights({ aa: 0.7 }), { speaking: true, active: true });
    if (m[VI.PP] >= 0.9) held++;
  }
  assert.ok(held * dt * 1000 >= 110 - dt * 1000, `seal lasted ${held} frames`);
  assert.ok(held <= 9, `seal released after ${held} frames`);

  const low = new MouthShaper({ audioPath: false });
  let peak = 0;
  for (let i = 0; i < 20; i++) peak = Math.max(peak, low.update(dt, weights({ PP: 0.4 }), { speaking: true, active: true })[VI.PP]);
  assert.ok(peak <= 0.4 + 1e-6, `weak PP shown as ${peak}`);
});

test('chew: a consonant that outweighs the vowel cuts the jaw, a vowel alone does not', () => {
  const run = (jaw, w) => {
    const s = new MouthShaper({ audioPath: false, jaw });
    for (let i = 0; i < 90; i++) s.update(1 / 60, w, { level: 1, speaking: true, active: true });
    return s.jaw;
  };
  const cons = weights({ SS: 0.8, aa: 0.4 });
  const withChew = run({}, cons);
  const noChew = run({ chewDepth: 0 }, cons);
  assert.ok(withChew < noChew * 0.75, `chew ${withChew} against ${noChew}`);
  const vowel = weights({ aa: 0.9 });
  assert.ok(Math.abs(run({}, vowel) - run({ chewDepth: 0 }, vowel)) < 1e-9, 'a vowel is not chewed');
});

test('V2: a snapped or held PP scales the other visemes so the sum stays at or under 1', () => {
  for (const audioPath of [false, true]) {
    for (const ppw of [0.6, 0.9, 1]) {
      const shaper = new MouthShaper({ version: 2, audioPath });
      const w = new Float32Array(14);
      w[VI.PP] = ppw;
      w[VI.aa] = 0.7;
      w[VI.E] = 0.4;
      w[VI.nn] = 0.3;
      for (let i = 0; i < 6; i++) shaper.update(1 / 60, w, { level: 1, speaking: true, active: true });
      let sum = 0;
      for (let i = 1; i < 14; i++) sum += shaper.work[i]; // work[] holds what was fitted
      assert.ok(sum <= 1 + 1e-5, `audioPath ${audioPath}, PP ${ppw}: viseme sum ${sum}`);
      assert.ok(shaper.work[VI.PP] >= ppw - 1e-6, 'PP itself is not reduced');
    }
  }
});

test('V2: a passing PP below the seal threshold is left alone', () => {
  const shaper = new MouthShaper({ version: 2 });
  const w = new Float32Array(14);
  w[VI.PP] = 0.3;
  w[VI.aa] = 0.9;
  shaper.update(1 / 60, w, { level: 1, speaking: true, active: true });
  assert.ok(Math.abs(shaper.work[VI.aa] - 0.9) < 1e-6);
});

test('V2: nn is gain 1.0, cap 1.2, and PP_jaw follows PP x min(jaw, 0.2) / 0.2', () => {
  assert.deepEqual(MORPH_GAIN[2].nn, [1.0, 1.2]);
  const shaper = new MouthShaper({ version: 2 });
  const open = new Float32Array(14);
  open[VI.aa] = 1;
  for (let i = 0; i < 30; i++) shaper.update(1 / 60, open, { level: 1, speaking: true, active: true });
  assert.equal(shaper.ppJawMorph, 0);
  const pp = new Float32Array(14);
  pp[VI.PP] = 1;
  shaper.update(1 / 60, pp, { level: 1, speaking: true, active: true });
  const expect = shaper.morph[VI.PP] * Math.min(shaper.jaw, 0.2) / 0.2;
  assert.ok(Math.abs(shaper.ppJawMorph - expect) < 1e-6);
  assert.ok(shaper.ppJawMorph > 0 && shaper.ppJawMorph <= 1);
});
