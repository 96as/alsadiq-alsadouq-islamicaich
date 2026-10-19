// Offline tuning aid: runs the lip-sync pipeline over the decoded dev clips and prints statistics.
// The clips are exported once from the dev page (frontend/dev-audio/pcm/, gitignored).
//   node scripts/lipsync-clips.mjs                 summary per clip
//   node scripts/lipsync-clips.mjs <clip> <from> <to>   frame trace for a time window (seconds)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { analyseBuffer } from '../src/features/child/components/avatar/lipsync/lipsyncEngine.js';
import { VISEMES } from '../src/features/child/components/avatar/lipsync/visemes.js';

const dir = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'dev-audio', 'pcm');
const meta = JSON.parse(fs.readFileSync(path.join(dir, 'meta.json'), 'utf8'));
const [, , only, from, to] = process.argv;

function load(name) {
  const buf = fs.readFileSync(path.join(dir, `${name}.f32`));
  return new Float32Array(buf.buffer, buf.byteOffset, buf.byteLength / 4);
}

const names = only ? [only] : Object.keys(meta);
const total = new Float32Array(VISEMES.length);
let totalActive = 0;
let openSum = 0;
let flips = 0;
let frames = 0;

for (const name of names) {
  const r = analyseBuffer(load(name), meta[name]);
  if (from !== undefined) {
    for (const f of r.frames) {
      if (f.t < +from || f.t > +to) continue;
      const top = [...f.weights]
        .map((v, i) => [VISEMES[i], v])
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([k, v]) => `${k}:${v.toFixed(2)}`)
        .join(' ');
      console.log(
        `${f.t.toFixed(2)} rms=${f.rms.toFixed(3)} lv=${f.level.toFixed(2)} v=${f.voicing.toFixed(2)} f1=${Math.round(f.f1)} f2=${Math.round(f.f2)} low=${f.low.toFixed(2)} sib=${f.sib.toFixed(2)} c=${Math.round(f.centroid)}  ${top}`,
      );
    }
    continue;
  }
  const mix = new Float32Array(VISEMES.length);
  let active = 0;
  let prev = null;
  for (const f of r.frames) {
    frames++;
    if (prev) {
      let d = 0;
      for (let i = 0; i < f.weights.length; i++) d += Math.abs(f.weights[i] - prev.weights[i]);
      if (d > 0.6) flips++;
    }
    prev = f;
    if (!f.speaking || f.weights[0] > 0.9) continue;
    active++;
    openSum += 1 - f.weights[0];
    for (let i = 0; i < mix.length; i++) mix[i] += f.weights[i];
  }
  for (let i = 0; i < mix.length; i++) total[i] += mix[i];
  totalActive += active;
  const pct = Array.from(mix, (v) => v / Math.max(1, active));
  console.log(
    name.slice(0, 40).padEnd(40),
    `speech ${((active / r.frames.length) * 100).toFixed(0)}%`,
    VISEMES.map((v, i) => `${v}:${(pct[i] * 100).toFixed(0)}`).join(' '),
  );
}
if (from === undefined) {
  console.log(
    'ALL'.padEnd(40),
    `mean opening ${(openSum / Math.max(1, totalActive)).toFixed(2)} | big jumps per second ${((flips / frames) * 60).toFixed(2)} |`,
    VISEMES.map((v, i) => `${v}:${((total[i] / Math.max(1, totalActive)) * 100).toFixed(0)}`).join(' '),
  );
}
