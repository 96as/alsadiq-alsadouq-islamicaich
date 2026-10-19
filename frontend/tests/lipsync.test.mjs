// Run with: npm run test:lipsync   (node's built-in test runner, no extra dependency)
import assert from 'node:assert/strict';
import { test } from 'node:test';
import * as THREE from 'three';
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js';
import { BlinkScheduler } from '../src/features/child/components/avatar/lipsync/blinkScheduler.js';
import { analyseBuffer } from '../src/features/child/components/avatar/lipsync/lipsyncEngine.js';
import { LipsyncRig } from '../src/features/child/components/avatar/lipsync/lipsyncRig.js';
import { resumeOnGesture } from '../src/features/child/components/avatar/lipsync/visemeDriver.js';
import {
  applyBlink,
  applyVisemes,
  bindMorphTargets,
} from '../src/features/child/components/avatar/lipsync/morphTargets.js';
import { VISEMES, VI } from '../src/features/child/components/avatar/lipsync/visemes.js';
import {
  VOWEL_FORMANTS,
  concat,
  noise,
  seeded,
  silence,
  vowel,
} from '../src/features/child/components/avatar/lipsync/testSignals.js';

const SR = 48000;

/** Mean weights of every viseme over [from, to] seconds. */
function meanWeights(frames, from, to) {
  const sum = new Float32Array(VISEMES.length);
  let n = 0;
  for (const f of frames) {
    if (f.t < from || f.t > to) continue;
    n++;
    for (let i = 0; i < sum.length; i++) sum[i] += f.weights[i];
  }
  return Array.from(sum, (v) => v / Math.max(1, n));
}
const top = (w) => VISEMES[w.indexOf(Math.max(...w))];

test('silence gives sil and nothing else', () => {
  const r = analyseBuffer(silence(1, SR), SR);
  const w = meanWeights(r.frames, 0, 1);
  assert.ok(w[VI.sil] > 0.99);
});

test('weights always sum to at most 1 and stay in 0..1', () => {
  const sig = concat(
    silence(0.2),
    vowel({ ...VOWEL_FORMANTS.aa, dur: 0.3 }),
    noise({ centre: 7000, bw: 1500, dur: 0.2 }),
    vowel({ ...VOWEL_FORMANTS.U, dur: 0.3 }),
    silence(0.3),
  );
  const r = analyseBuffer(sig, SR);
  for (const f of r.frames) {
    let sum = 0;
    for (const v of f.weights) {
      assert.ok(v >= 0 && v <= 1.0001);
      sum += v;
    }
    assert.ok(sum < 1.001, `sum ${sum} at ${f.t}`);
  }
});

for (const [name, fm] of Object.entries(VOWEL_FORMANTS)) {
  test(`a sustained ${name} vowel is classified as ${name}`, () => {
    const sig = concat(silence(0.3), vowel({ ...fm, dur: 0.5 }), silence(0.4));
    const r = analyseBuffer(sig, SR);
    const w = meanWeights(r.frames, 0.5, 0.7);
    assert.equal(top(w), name, JSON.stringify(w.map((v) => +v.toFixed(2))));
  });
}

test('a hiss (s) is classified as SS and is not mistaken for a vowel', () => {
  const sig = concat(silence(0.3), noise({ centre: 7000, bw: 1500, dur: 0.4, rng: seeded(3) }), silence(0.3));
  const r = analyseBuffer(sig, SR);
  const w = meanWeights(r.frames, 0.45, 0.65);
  assert.equal(top(w), 'SS');
  assert.ok(w[VI.aa] + w[VI.E] + w[VI.I] + w[VI.O] + w[VI.U] < 0.2);
});

test('a short silence inside a phrase closes the lips (PP)', () => {
  const a = vowel({ ...VOWEL_FORMANTS.aa, dur: 0.25 });
  const sig = concat(silence(0.3), a, silence(0.09), a, silence(0.5));
  const r = analyseBuffer(sig, SR);
  const w = meanWeights(r.frames, 0.58, 0.66);
  assert.ok(w[VI.PP] > 0.2, `PP ${w[VI.PP]}`);
});

test('the mouth is open wider for a loud vowel than for a quiet one', () => {
  const loud = vowel({ ...VOWEL_FORMANTS.aa, dur: 0.4, rms: 0.2 });
  const quiet = vowel({ ...VOWEL_FORMANTS.aa, dur: 0.4, rms: 0.04 });
  const r = analyseBuffer(concat(silence(0.2), loud, silence(0.3), quiet, silence(0.4)), SR);
  const wl = meanWeights(r.frames, 0.35, 0.55)[VI.aa];
  const wq = meanWeights(r.frames, 1.05, 1.25)[VI.aa];
  assert.ok(wl > wq, `loud ${wl} quiet ${wq}`);
});

test('attack is quicker than release, with no jump between frames', () => {
  const r = analyseBuffer(concat(silence(0.2), vowel({ ...VOWEL_FORMANTS.aa, dur: 0.4 }), silence(0.5)), SR);
  let worst = 0;
  for (let i = 1; i < r.frames.length; i++) {
    worst = Math.max(worst, Math.abs(r.frames[i].weights[VI.aa] - r.frames[i - 1].weights[VI.aa]));
  }
  assert.ok(worst < 0.35, `largest step per frame ${worst}`);
});

test('the analysis does not depend on the sample rate', () => {
  for (const sr of [16000, 24000, 44100]) {
    const sig = concat(silence(0.3, sr), vowel({ ...VOWEL_FORMANTS.I, dur: 0.5, sr }), silence(0.3, sr));
    const w = meanWeights(analyseBuffer(sig, sr).frames, 0.5, 0.7);
    assert.equal(top(w), 'I', `sr ${sr}`);
  }
});

test('blinks come every 2 to 6 seconds, mostly', () => {
  const b = new BlinkScheduler({ rng: seeded(11) });
  const starts = [];
  let prev = 0;
  const dt = 1 / 60;
  for (let i = 0; i < 60 * 300; i++) {
    const w = b.update(dt);
    if (w > 0 && prev === 0) starts.push(i * dt);
    prev = w;
    assert.ok(w >= 0 && w <= 1);
  }
  const gaps = starts.slice(1).map((t, i) => t - starts[i]);
  const long = gaps.filter((g) => g >= 1.9 && g <= 6.2).length;
  assert.ok(long / gaps.length > 0.75, `gaps ${gaps.length}, in range ${long}`);
  const doubles = gaps.filter((g) => g < 1).length;
  assert.ok(doubles > 0, 'at least one double blink in 5 minutes');
  assert.ok(doubles / gaps.length < 0.35);
});

test('no blink starts during a stressed syllable, and none is dropped for ever', () => {
  const b = new BlinkScheduler({ rng: seeded(5) });
  const dt = 1 / 60;
  let started = 0;
  let prev = 0;
  for (let i = 0; i < 60 * 60; i++) {
    const t = i * dt;
    const stressed = t % 2 < 1; // stress on for the first second of every two
    const w = b.update(dt, { stress: stressed ? 1 : 0 });
    if (w > 0 && prev === 0) {
      started++;
      assert.ok(!stressed || b.deferred >= b.cfg.maxDefer, `blink started in stress at ${t.toFixed(2)}`);
    }
    prev = w;
  }
  assert.ok(started > 5);
});

test('reduced motion gives no double blinks', () => {
  const b = new BlinkScheduler({ rng: seeded(21) });
  const dt = 1 / 60;
  let prev = 0;
  const starts = [];
  for (let i = 0; i < 60 * 300; i++) {
    const w = b.update(dt, { reduced: true });
    if (w > 0 && prev === 0) starts.push(i * dt);
    prev = w;
  }
  const gaps = starts.slice(1).map((t, i) => t - starts[i]);
  assert.ok(gaps.every((g) => g > 1.5));
});

function fakeMesh(names) {
  const dict = {};
  names.forEach((n, i) => (dict[n] = i));
  return { morphTargetDictionary: dict, morphTargetInfluences: new Array(names.length).fill(0) };
}
const fakeScene = (...meshes) => ({ traverse: (fn) => meshes.forEach(fn) });

test('morph binding finds viseme_* names and blink, and drives several meshes together', () => {
  const head = fakeMesh([...VISEMES.map((v) => `viseme_${v}`), 'blink', 'browUp']);
  const teeth = fakeMesh(['viseme_aa', 'viseme_O']);
  const binding = bindMorphTargets(fakeScene(head, teeth));
  assert.ok(binding.hasVisemes);
  assert.ok(binding.hasBlink);
  assert.deepEqual(binding.missingVisemes, []);
  const w = new Float32Array(VISEMES.length);
  w[VI.aa] = 1;
  applyVisemes(binding, w, {});
  applyBlink(binding, 0.5);
  assert.equal(head.morphTargetInfluences[VI.aa], 1);
  assert.equal(teeth.morphTargetInfluences[0], 1);
  assert.equal(head.morphTargetInfluences[VISEMES.length], 0.5);
  assert.equal(head.morphTargetInfluences[VISEMES.length + 1], 0);
});

test('a scene without viseme morphs reports no visemes (the jaw path stays)', () => {
  const binding = bindMorphTargets(fakeScene(fakeMesh(['smile', 'frown']), { traverse: () => {} }));
  assert.equal(binding.hasVisemes, false);
  assert.equal(binding.hasBlink, false);
});

test('morphNames overrides the default names', () => {
  const head = fakeMesh(['Mouth_Ah', 'Mouth_Oh', 'x', 'y', 'z', 'a1', 'a2']);
  const binding = bindMorphTargets(fakeScene(head), { morphNames: { aa: 'Mouth_Ah', O: ['Mouth_Oh'] } });
  assert.equal(binding.visemes[VI.aa].length, 1);
  assert.equal(binding.visemes[VI.O].length, 1);
  assert.equal(binding.hasVisemes, false); // only two found, under the threshold of five
});

test('the mouth is half open within 60 ms of a vowel onset (lag)', () => {
  for (const name of ['aa', 'I', 'U']) {
    const onset = 0.3;
    const sig = concat(silence(onset), vowel({ ...VOWEL_FORMANTS[name], dur: 0.6 }), silence(0.4));
    const { frames } = analyseBuffer(sig, SR, { fps: 120 });
    const open = (f) => 1 - f.weights[VI.sil];
    const plateau = meanWeights(frames, onset + 0.4, onset + 0.55);
    const half = 0.5 * (1 - plateau[VI.sil]);
    const first = frames.find((f) => f.t > onset && open(f) >= half);
    assert.ok(first && first.t - onset <= 0.06, `${name}: half open after ${((first?.t ?? 99) - onset) * 1000} ms`);
  }
});

test('resumeOnGesture resumes a suspended or interrupted context, and stops when disposed', () => {
  const win = new EventTarget();
  const doc = new EventTarget();
  doc.visibilityState = 'visible';
  const saved = { window: globalThis.window, document: globalThis.document };
  globalThis.window = win;
  globalThis.document = doc;
  try {
    const ctx = {
      state: 'suspended',
      resume() {
        this.state = 'running';
        return Promise.resolve();
      },
    };
    const stop = resumeOnGesture(ctx);
    win.dispatchEvent(new Event('touchend')); // iOS unlocks audio on touchend, not touchstart
    assert.equal(ctx.state, 'running');
    ctx.state = 'interrupted'; // iOS: a phone call or the lock screen
    doc.dispatchEvent(new Event('visibilitychange'));
    assert.equal(ctx.state, 'running');
    stop();
    ctx.state = 'suspended';
    win.dispatchEvent(new Event('click'));
    assert.equal(ctx.state, 'suspended');
  } finally {
    globalThis.window = saved.window;
    globalThis.document = saved.document;
  }
});

/** A real three.js mesh with the 14 visemes as bare names, as planned for avatar-animated.glb. */
function threeAvatar(names) {
  const geometry = new THREE.BufferGeometry();
  const pos = new Float32Array(9);
  geometry.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geometry.morphAttributes.position = names.map((name) => {
    const attr = new THREE.BufferAttribute(pos.slice(), 3);
    attr.name = name;
    return attr;
  });
  const mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial());
  mesh.updateMorphTargets(); // builds morphTargetDictionary from the names, as GLTFLoader does
  const root = new THREE.Group();
  root.add(mesh);
  return root;
}

test('LipsyncRig drives real three.js morphs on a cloned scene, and leaves the jaw to visemes', () => {
  const source = threeAvatar([...VISEMES, 'blink']);
  const scene = SkeletonUtils.clone(source);
  const rig = new LipsyncRig(scene, { rng: seeded(2) });
  assert.ok(rig.hasVisemes);
  assert.ok(rig.hasBlink);
  assert.equal(rig.jawScale, 0);
  const weights = new Float32Array(VISEMES.length);
  weights[VI.O] = 0.8;
  weights[VI.sil] = 0.2;
  for (let i = 0; i < 60; i++) rig.update(1 / 60, { lipsync: { weights, stress: 0, phraseEnds: 0 }, open: 0, speaking: true });
  let clone = null;
  scene.traverse((o) => {
    if (o.isMesh) clone = o;
  });
  let original = null;
  source.traverse((o) => {
    if (o.isMesh) original = o;
  });
  assert.ok(Math.abs(clone.morphTargetInfluences[VI.O] - 0.8 * 0.9) < 0.01); // VISEME_GAIN.O = 0.9
  assert.ok(Math.abs(clone.morphTargetInfluences[VI.sil] - 0.2) < 0.01);
  assert.equal(original.morphTargetInfluences[VI.O], 0, 'the source scene is untouched');
});

test('LipsyncRig on a scene without morphs keeps the jaw and writes nothing', () => {
  const scene = threeAvatar(['smile']);
  const rig = new LipsyncRig(scene);
  assert.equal(rig.hasVisemes, false);
  assert.equal(rig.hasBlink, false);
  assert.equal(rig.jawScale, 1);
  rig.update(1 / 60, { lipsync: null, open: 1, speaking: true });
  let mesh = null;
  scene.traverse((o) => {
    if (o.isMesh) mesh = o;
  });
  assert.equal(mesh.morphTargetInfluences[0], 0);
});
