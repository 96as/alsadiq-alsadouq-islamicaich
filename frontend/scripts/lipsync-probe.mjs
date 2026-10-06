// Prints what the lip-sync engine sees in synthetic vowels, noise and silence. Used while tuning.
//   node scripts/lipsync-probe.mjs
import { analyseBuffer } from '../src/features/child/components/avatar/lipsync/lipsyncEngine.js';
import { VISEMES } from '../src/features/child/components/avatar/lipsync/visemes.js';
import {
  VOWEL_FORMANTS,
  concat,
  noise,
  seeded,
  silence,
  vowel,
} from '../src/features/child/components/avatar/lipsync/testSignals.js';

const SR = 48000;

function dominant(frames, from, to) {
  const sum = new Float32Array(VISEMES.length);
  let n = 0;
  for (const f of frames) {
    if (f.t < from || f.t > to) continue;
    n++;
    for (let i = 0; i < sum.length; i++) sum[i] += f.weights[i];
  }
  const avg = Array.from(sum, (v) => v / Math.max(1, n));
  const order = avg.map((v, i) => [VISEMES[i], v]).sort((a, b) => b[1] - a[1]);
  return order
    .slice(0, 3)
    .map(([k, v]) => `${k}:${v.toFixed(2)}`)
    .join(' ');
}

for (const [name, fm] of Object.entries(VOWEL_FORMANTS)) {
  const sig = concat(silence(0.3), vowel({ ...fm, dur: 0.5, sr: SR }), silence(0.4));
  const r = analyseBuffer(sig, SR);
  const mid = r.frames.filter((f) => f.t > 0.5 && f.t < 0.7);
  const f = mid[mid.length >> 1];
  console.log(
    name.padEnd(3),
    dominant(r.frames, 0.5, 0.7).padEnd(30),
    `f1=${f.f1.toFixed(0)} f2=${f.f2.toFixed(0)} f3=${f.f3.toFixed(0)} voicing=${f.voicing.toFixed(2)} level=${f.level.toFixed(2)}`,
  );
}

const rng = seeded(3);
for (const [name, centre, bw] of [
  ['s', 7000, 1500],
  ['sh', 3500, 1200],
  ['f', 5000, 5000],
]) {
  const sig = concat(silence(0.3), noise({ centre, bw, dur: 0.4, sr: SR, rng, rms: 0.03 }), silence(0.4));
  const r = analyseBuffer(sig, SR);
  const f = r.frames.find((x) => x.t > 0.5);
  console.log(
    name.padEnd(3),
    dominant(r.frames, 0.45, 0.65).padEnd(30),
    `centroid=${f.centroid.toFixed(0)} sib=${f.sib.toFixed(2)} voicing=${f.voicing.toFixed(2)}`,
  );
}

const quiet = analyseBuffer(silence(1, SR), SR);
console.log('silence', dominant(quiet.frames, 0, 1));
