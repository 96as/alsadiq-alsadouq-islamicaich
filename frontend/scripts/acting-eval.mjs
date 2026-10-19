// Offline numbers for the WP4 mouth shaping on the cached Arabic test set (dev-audio/eval-ar,
// gitignored). It runs the lip-sync engine in Arabic mode, the rig's follow stage and the
// MouthShaper, and reports the jaw distribution, the jaw on ground-truth open vowels, the shown
// aa after gain, the jaw rhythm (spectrum) and the PP clamp. The real chin-drop (M1, M2) needs
// the mesh and is measured in the browser (window.__mouthMetrics, scripts/mouth-metrics.py).
//
//   node scripts/acting-eval.mjs [--split tune|test|all] [--lift] [--version 1|2] [--json out.json]

import fs from 'node:fs';
import { analyseBuffer } from '../src/features/child/components/avatar/lipsync/lipsyncEngine.js';
import { LIVE_RATE } from '../src/features/child/components/avatar/lipsync/lipsyncRig.js';
import { VI, VISEME_COUNT } from '../src/features/child/components/avatar/lipsync/visemes.js';
import { JAW_STUDIO, MORPH_GAIN } from '../src/features/child/components/avatar/acting/actingConfig.js';
import { MouthShaper } from '../src/features/child/components/avatar/acting/mouthShaping.js';
import { buildSpans, labelFrames, loadClip, loadTestset, shiftSpans } from './lipsync-eval/gt.mjs';

const args = { split: 'all', lift: false, version: 1, json: '' };
for (let i = 2; i < process.argv.length; i++) {
  const k = process.argv[i];
  if (k === '--lift') args.lift = true;
  else if (k.startsWith('--')) args[k.slice(2)] = process.argv[++i];
}
args.version = Number(args.version) === 2 ? 2 : 1;

const FPS = 60;
const DT = 1 / FPS;
// Chin travel per radian of jaw at the MOTION-BIBLE 6.6 chin vertex (largest aa dy), as the browser
// metrics measure it. M-mouth-acting.md quotes 4.5 for a lower chin vertex; the browser numbers use 3.64.
const CM_PER_RAD = 3.64;
const damp = (a, b, rate, dt) => b + (a - b) * Math.exp(-rate * dt);
const pct = (a, p) => {
  if (!a.length) return NaN;
  const s = [...a].sort((x, y) => x - y);
  return s[Math.min(s.length - 1, Math.max(0, Math.round(p * (s.length - 1))))];
};

/** Share of spectral energy per band and the peak frequency of a trace sampled at FPS. */
function spectrum(trace) {
  const n = trace.length;
  const mean = trace.reduce((x, y) => x + y, 0) / n;
  const x = trace.map((v) => v - mean);
  let total = 0;
  let above10 = 0;
  let b13 = 0;
  let b36 = 0;
  let b610 = 0;
  let peakF = 0;
  let peakE = 0;
  let peakAny = 0; // the true peak (from 1 Hz): phrase-level motion often wins over syllables
  let peakAnyE = 0;
  for (let f = 0.5; f <= 25; f += 0.1) {
    let re = 0;
    let im = 0;
    for (let i = 0; i < n; i++) {
      const ph = (2 * Math.PI * f * i) / FPS;
      re += x[i] * Math.cos(ph);
      im += x[i] * Math.sin(ph);
    }
    const e = re * re + im * im;
    total += e;
    if (f > 10) above10 += e;
    else if (f > 6) b610 += e;
    else if (f > 3) b36 += e;
    else if (f > 1) b13 += e;
    if (f >= 2.5 && e > peakE) {
      peakE = e;
      peakF = f;
    }
    if (f >= 1 && e > peakAnyE) {
      peakAnyE = e;
      peakAny = f;
    }
  }
  const share = (v) => (total ? v / total : 0);
  return { peakF, peakAny, above10: share(above10), bands: [share(b13), share(b36), share(b610), share(above10)] };
}

const set = loadTestset();
const ids = set.lines.filter((l) => args.split === 'all' || l.split === args.split).map((l) => l.id);
const jawVoiced = [];
const jawOpenVowel = [];
const aaShown = [];
const peaks = [];
const peaksAny = [];
const above10 = [];
const bandSum = [0, 0, 0, 0];
let satFrames = 0;
let voicedFrames = 0;
let underFloor = 0;
let ppFrames = 0;
let ppClamped = 0;
const gain = MORPH_GAIN[args.version].aa;

for (const id of ids) {
  const clip = loadClip(id, 'diac');
  const run = analyseBuffer(clip.pcm, clip.sr, { fps: FPS, lang: 'ar' });
  const nF = run.frames.length;
  const lab = labelFrames(shiftSpans(buildSpans(clip, 'diac'), 0.023), nF);
  const shaper = new MouthShaper({ version: args.version, audioPath: true, audio: { massLift: args.lift } });
  const shown = new Float32Array(VISEME_COUNT);
  shown[VI.sil] = 1;
  const jaws = new Float32Array(nF);
  for (let n = 0; n < nF; n++) {
    const f = run.frames[n];
    for (let i = 0; i < VISEME_COUNT; i++) shown[i] = damp(shown[i], f.weights[i], LIVE_RATE, DT);
    const morph = shaper.update(DT, shown, { level: f.level ?? 1, stress: f.stress ?? 0, speaking: true, active: Boolean(f.active) });
    jaws[n] = shaper.jaw;
    if (f.active) {
      voicedFrames++;
      jawVoiced.push(shaper.jaw);
      if (shaper.jaw >= 0.95 * JAW_STUDIO.max) satFrames++;
      if (shaper.jaw * CM_PER_RAD < 0.5) underFloor++;
    }
    if (lab.vclass[n] === 1 && lab.isVowelFrame[n]) {
      jawOpenVowel.push(shaper.jaw);
      aaShown.push(morph[VI.aa]);
    }
    if (shown[VI.PP] >= JAW_STUDIO.ppGateAt) {
      ppFrames++;
      if (shaper.jaw <= shaper.ppJaw + 1e-3) ppClamped++;
    }
  }
  const sp = spectrum(Array.from(jaws));
  peaks.push(sp.peakF);
  peaksAny.push(sp.peakAny);
  above10.push(sp.above10);
  sp.bands.forEach((v, i) => (bandSum[i] += v / ids.length));
}

const head = 0.375; // m, chin to crown
const r = (v, d = 3) => (Number.isFinite(v) ? Number(v.toFixed(d)) : null);
const result = {
  lines: ids.length,
  version: args.version,
  massLift: args.lift,
  voicedFrames,
  jawRad: { p50: r(pct(jawVoiced, 0.5)), p90: r(pct(jawVoiced, 0.9)), max: r(Math.max(...jawVoiced)) },
  jawChinCmOnly: { p50: r(pct(jawVoiced, 0.5) * CM_PER_RAD, 2), p90: r(pct(jawVoiced, 0.9) * CM_PER_RAD, 2) },
  saturationShare: r(satFrames / voicedFrames, 3),
  underHalfCmShare: r(underFloor / voicedFrames, 3),
  openVowelFrames: jawOpenVowel.length,
  openVowelJawRad: { p50: r(pct(jawOpenVowel, 0.5)), p90: r(pct(jawOpenVowel, 0.9)) },
  openVowelJawRatio: { p50: r((pct(jawOpenVowel, 0.5) * CM_PER_RAD) / 100 / head, 4), p90: r((pct(jawOpenVowel, 0.9) * CM_PER_RAD) / 100 / head, 4) },
  aaShownAfterGain: { p25: r(pct(aaShown, 0.25)), p50: r(pct(aaShown, 0.5)), p75: r(pct(aaShown, 0.75)), gain },
  rhythm: { peakHzMedian: r(pct(peaks, 0.5), 1), peakFrom2p5Hz: true, truePeakHzMedian: r(pct(peaksAny, 0.5), 1), above10Median: r(pct(above10, 0.5), 4), above10Max: r(Math.max(...above10), 4), bandShare_1to3_3to6_6to10_over10: bandSum.map((v) => r(v, 3)) },
  ppGate: { frames: ppFrames, clamped: ppClamped },
};
console.log(JSON.stringify(result, null, 1));
if (args.json) fs.writeFileSync(args.json, JSON.stringify(result, null, 1));
