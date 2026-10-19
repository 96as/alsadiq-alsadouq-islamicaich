// Ground-truth evaluation of the lip-sync driver on the cached Arabic test set.
//
//   node scripts/lipsync-eval/eval.mjs --mode audio|hybrid --split tune|test|all
//        [--stress none|late|stall|stale] [--lang ar|en] [--tag name] [--quiet]
//        [--sr 48000]   run the pipeline at this sample rate (clips are cached at 22.05 kHz)
//        [--set ARABIC.f2i=1900,TIMELINE.leadMs=30]   override config numbers for a tuning sweep
//        [--mesh anim3|r1]      the mesh the weights are shown on (default anim3, the GLB the app loads)
//        [--divisor on|off]     on anim3: divide the web gains by the gain the mesh bakes in (default on).
//                               off reproduces the double gain (E, I, kk, DD, nn drawn 1.5x too hard).
//
// It scores what the morphs would show: the engine's weights go through the rig's follow stage
// (LIVE_RATE) and VISEME_GAIN. Labels come from gt.mjs (built from the ElevenLabs alignment, and
// deliberately not from the browser's own text rules). Writes dev-audio/eval-ar/report-<tag>.json.
// See PLAN.md section 7 for the metric definitions and section 8 for the bars.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { JAW, MESH_VISEME_GAIN } from '../../src/features/child/components/avatar/avatarConfig.js';
import * as CONFIG from '../../src/features/child/components/avatar/lipsync/lipsyncConfig.js';
import { analyseBuffer } from '../../src/features/child/components/avatar/lipsync/lipsyncEngine.js';
import { jawOpenTable, jawTarget } from '../../src/features/child/components/avatar/lipsync/jaw.js';
import { makeTimeline } from './timelines.mjs';
import { resample } from './resample.mjs';
import { LIVE_RATE } from '../../src/features/child/components/avatar/lipsync/lipsyncRig.js';
import { VI, VISEMES, VISEME_COUNT, VISEME_GAIN } from '../../src/features/child/components/avatar/lipsync/visemes.js';
import {
  EVAL_DIR, FPS, G, GROUPS, GROUP_OPENNESS, biasFor, buildSpans, labelFrames, loadClip, loadTestset, nearestVowelGroup,
  shiftSpans, validate,
} from './gt.mjs';

// ---------------------------------------------------------------------------------------------
// Arguments

function parseArgs(argv) {
  const a = { mode: 'audio', split: 'all', stress: 'none', lang: 'ar', tag: '', quiet: false };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === '--quiet') a.quiet = true;
    else if (k.startsWith('--')) a[k.slice(2)] = argv[++i];
  }
  if (a.set) {
    for (const kv of a.set.split(',')) {
      const [key, val] = kv.split('=');
      const [group, name] = key.split('.');
      if (!CONFIG[group] || !(name in CONFIG[group])) throw new Error(`unknown config ${key}`);
      CONFIG[group][name] = Number(val);
    }
  }
  return a;
}

// ---------------------------------------------------------------------------------------------
// What the avatar shows

// integrate-1: the gain the mesh really shows. The R2 mesh (anim3) bakes MESH_VISEME_GAIN into five shapes, so
// what is drawn is web gain x baked gain. The rig divides the baked part out of the web gain (LipsyncRig meshGain),
// which gives back the round-1 look; --divisor off is the double gain it replaced.
let GAINS = Float32Array.from(VISEMES, (n) => VISEME_GAIN[n] ?? 1);
export function setMeshGains({ mesh = 'anim3', divisor = true } = {}) {
  GAINS = Float32Array.from(VISEMES, (n) => {
    const baked = mesh === 'anim3' ? MESH_VISEME_GAIN[n] ?? 1 : 1;
    const web = (VISEME_GAIN[n] ?? 1) / (mesh === 'anim3' && divisor ? MESH_VISEME_GAIN[n] ?? 1 : 1);
    return web * baked;
  });
}
const JAW_TABLE = jawOpenTable(JAW.open);
const dampTo = (a, b, rate, dt) => b + (a - b) * Math.exp(-rate * dt);

/**
 * Per-frame shown weights (after the rig's follow stage and the gain) and the jaw (0..1 of
 * JAW.max, after attack and release) for a list of engine frames.
 */
export function shownFromFrames(frames, fps = FPS) {
  const dt = 1 / fps;
  const shown = new Float32Array(VISEME_COUNT);
  shown[VI.sil] = 1;
  const out = new Array(frames.length);
  const jawOut = new Float32Array(frames.length);
  let jaw = 0;
  // The same coupling the avatar uses (ClipAvatar.jsx): loudness scales the jaw, a closure holds it up.
  const jawOpts = { level: 1, couple: JAW.levelCouple, ppMax: JAW.ppMax, ppAt: JAW.ppAt };
  for (let n = 0; n < frames.length; n++) {
    const w = frames[n].weights;
    for (let i = 0; i < VISEME_COUNT; i++) shown[i] = dampTo(shown[i], w[i], LIVE_RATE, dt);
    const g = new Float32Array(VISEME_COUNT);
    for (let i = 0; i < VISEME_COUNT; i++) g[i] = shown[i] * GAINS[i];
    out[n] = g;
    jawOpts.level = frames[n].level ?? 1;
    const want = jawTarget(shown, JAW_TABLE, jawOpts);
    jaw = dampTo(jaw, want, want > jaw ? JAW.attack : JAW.release, dt);
    jawOut[n] = jaw;
  }
  return { shown: out, jaw: jawOut };
}

// ---------------------------------------------------------------------------------------------
// Small helpers

const median = (a) => {
  if (!a.length) return NaN;
  const b = [...a].sort((x, y) => x - y);
  const m = b.length >> 1;
  return b.length % 2 ? b[m] : 0.5 * (b[m - 1] + b[m]);
};
const percentile = (a, p) => {
  if (!a.length) return NaN;
  const b = [...a].sort((x, y) => x - y);
  return b[Math.min(b.length - 1, Math.max(0, Math.round(p * (b.length - 1))))];
};
const sum = (a) => a.reduce((x, y) => x + y, 0);

/** Frames of [t0, t1] (seconds) at the analyseBuffer time convention t = (n + 1) / fps. */
function frameRange(t0, t1, nFrames, fps = FPS) {
  const a = Math.max(0, Math.ceil(t0 * fps - 1));
  const b = Math.min(nFrames - 1, Math.floor(t1 * fps - 1));
  return [a, b];
}

/** True when `pred(n)` holds for `need` consecutive frames inside [a, b]; returns the first such frame or -1. */
function firstRun(a, b, need, pred) {
  let run = 0;
  for (let n = a; n <= b; n++) {
    if (pred(n)) {
      run++;
      if (run >= need) return n - need + 1;
    } else run = 0;
  }
  return -1;
}

// viseme index -> visual group
const VISEME_GROUP = new Int8Array(VISEME_COUNT).fill(G.SIL);
Object.assign(VISEME_GROUP, {
  [VI.PP]: G.CLOSED, [VI.FF]: G.LABIODENT, [VI.DD]: G.TONGUE, [VI.kk]: G.TONGUE, [VI.CH]: G.SIBIL, [VI.SS]: G.SIBIL,
  [VI.nn]: G.TONGUE, [VI.RR]: G.TONGUE, [VI.aa]: G.OPEN, [VI.E]: G.OPEN, [VI.I]: G.SPREAD, [VI.O]: G.ROUND, [VI.U]: G.ROUND,
});

function predictedGroup(w) {
  let nonSil = 0;
  for (let i = 1; i < VISEME_COUNT; i++) nonSil += w[i];
  if (nonSil < 0.15) return G.SIL;
  const gs = new Float32Array(GROUPS.length);
  for (let i = 1; i < VISEME_COUNT; i++) gs[VISEME_GROUP[i]] += w[i];
  let best = 0;
  for (let g = 1; g < gs.length; g++) if (gs[g] > gs[best]) best = g;
  return best;
}

// ---------------------------------------------------------------------------------------------
// Engine runs

/** Run the engine (or the hybrid) on a clip. The hybrid hook is added with the timeline (Part C). */
function runClip(clip, args, ctx) {
  const opts = { fps: FPS, lang: args.lang };
  if (args.mode === 'hybrid') {
    if (!ctx.makeTimeline) throw new Error('hybrid mode needs the timeline replay (not available in this build)');
    opts.timeline = ctx.makeTimeline(clip, args);
  }
  // --sr N: run the pipeline at another sample rate (a live session hears the voice at 48 kHz).
  const sr = args.sr ? Number(args.sr) : clip.sr;
  const pcm = sr === clip.sr ? clip.pcm : resample(clip.pcm, clip.sr, sr);
  return analyseBuffer(pcm, sr, opts);
}

// ---------------------------------------------------------------------------------------------
// Scoring one clip

const CLASS_NAMES = ['a', 'i', 'u'];

function scoreClip(clip, run, biasSec, stats) {
  const variant = clip.variant;
  const frames = run.frames;
  const nF = frames.length;
  const built = shiftSpans(buildSpans(clip, variant), biasSec);
  const lab = labelFrames(built, nF);
  const { shown, jaw } = shownFromFrames(frames);
  const nearest = nearestVowelGroup(built, nF);
  const key = variant;
  const st = (stats[key] ??= newStats());

  // Vowel identity, mid 60 % of each vowel span.
  for (let n = 0; n < nF; n++) {
    if (!lab.isVowelFrame[n]) continue;
    const gtc = lab.vclass[n] - 1; // 0 a, 1 i, 2 u
    const w = shown[n];
    const pa = w[VI.aa] + w[VI.E];
    const pi = w[VI.I];
    const pu = w[VI.U] + w[VI.O];
    let pred = 3;
    if (pa + pi + pu >= 0.1) pred = pa >= pi && pa >= pu ? 0 : pi >= pu ? 1 : 2;
    st.vowel.conf[gtc][pred]++;
    const longKey = lab.vlong[n] ? 'long' : 'short';
    st.vowel[longKey][gtc === pred ? 'hit' : 'miss']++;
    st.vowel.perLongClass[`${longKey}-${CLASS_NAMES[gtc]}`] ??= [0, 0];
    st.vowel.perLongClass[`${longKey}-${CLASS_NAMES[gtc]}`][gtc === pred ? 0 : 1]++;
    // K1: the aa weight on open-vowel frames.
    if (gtc === 0) st.k1.push(w[VI.aa]);
  }

  // Frame-level group accuracy and the matrices.
  for (let n = 0; n < nF; n++) {
    const g = lab.group[n];
    if (g < 0) continue;
    const pg = predictedGroup(shown[n]);
    st.groupConf[g][pg]++;
    if (g === G.SIL) {
      st.sil.n++;
      if (pg === G.SIL) st.sil.hit++;
      continue;
    }
    st.frames.n++;
    if (pg === g) st.frames.strict++;
    if (pg === g || ((g === G.TONGUE || g === G.THROAT) && nearest[n] >= 0 && pg === nearest[n])) st.frames.lenient++;
    // 14 x 14 raw (argmax of the shown weights)
    let best = 0;
    for (let i = 1; i < VISEME_COUNT; i++) if (shown[n][i] > shown[n][best]) best = i;
    st.matrix14[lab.v14[n]][best]++;
    st.speechFrames++;
  }

  // Closures.
  const closureWindows = [];
  for (const b of built.bilabials) {
    const end = variant === 'plain' ? b.t0 + Math.min(b.t1 - b.t0, 0.12) + 0.02 : b.t1 + 0.02;
    closureWindows.push([b.t0 - 0.08, end]);
  }
  let lineHit = 0;
  for (let k = 0; k < built.bilabials.length; k++) {
    const b = built.bilabials[k];
    const [a, e] = frameRange(closureWindows[k][0], closureWindows[k][1], nF);
    const first = firstRun(a, e, 2, (n) => shown[n][VI.PP] >= 0.5);
    const hit = first >= 0;
    if (hit) lineHit++;
    const pos = b.geminate ? 'geminate' : b.pos;
    for (const key2 of [`letter:${b.ch}`, `pos:${pos}`, 'all']) {
      st.closure[key2] ??= [0, 0];
      st.closure[key2][hit ? 0 : 1]++;
    }
    if (hit) st.closureOnset.push(((first + 1) / FPS - b.t0) * 1000);
    // K3: PP >= 0.9 held for >= 50 ms (3 frames at 60 fps).
    const held = firstRun(a, e, 3, (n) => shown[n][VI.PP] >= 0.9) >= 0;
    st.k3[held ? 0 : 1]++;
  }
  // False closures.
  let inRun = 0;
  let runStart = 0;
  const flushRun = (endN) => {
    if (inRun >= 2) {
      const t0 = (runStart + 1) / FPS;
      const t1 = (endN + 1) / FPS;
      const overlaps = closureWindows.some(([wa, wb]) => t0 <= wb && t1 >= wa);
      if (!overlaps) st.falseClosures++;
    }
    inRun = 0;
  };
  for (let n = 0; n < nF; n++) {
    if (shown[n][VI.PP] >= 0.5) {
      if (inRun === 0) runStart = n;
      inRun++;
    } else flushRun(n - 1);
  }
  flushRun(nF - 1);
  let pauseTime = 0;
  for (const sp of built.spans) if (sp.kind === 'pause') pauseTime += sp.t1 - sp.t0;
  st.speechSeconds += Math.max(0.1, run.duration - pauseTime);

  // Lag: GT openness against shown openness.
  const gt = new Float32Array(nF);
  let last = 0;
  for (let n = 0; n < nF; n++) {
    if (lab.group[n] >= 0) last = GROUP_OPENNESS[lab.group[n]];
    gt[n] = last;
  }
  const sigma = 0.03 * FPS;
  const half = Math.ceil(3 * sigma);
  const gts = new Float32Array(nF);
  for (let n = 0; n < nF; n++) {
    let s = 0;
    let wsum = 0;
    for (let k = -half; k <= half; k++) {
      const m = n + k;
      if (m < 0 || m >= nF) continue;
      const wk = Math.exp(-0.5 * (k / sigma) ** 2);
      s += wk * gt[m];
      wsum += wk;
    }
    gts[n] = s / wsum;
  }
  const open = new Float32Array(nF);
  for (let n = 0; n < nF; n++) open[n] = jawTarget(shown[n], JAW_TABLE);
  const lag = crossLag(gts, open, Math.round(0.25 * FPS));
  if (Number.isFinite(lag)) st.lags.push(lag * 1000);
  st.perLine.push({ name: clip.name, closureHit: lineHit, closureN: built.bilabials.length, lagMs: Number.isFinite(lag) ? lag * 1000 : NaN });
  // The same on the open vowel alone (an easier, sharper signal): GT OPEN against the aa and E weights.
  const gtOpen = new Float32Array(nF);
  const shOpen = new Float32Array(nF);
  for (let n = 0; n < nF; n++) {
    gtOpen[n] = lab.group[n] === G.OPEN ? 1 : 0;
    shOpen[n] = shown[n][VI.aa] + shown[n][VI.E];
  }
  const lagV = crossLag(smoothSeries(gtOpen, sigma), shOpen, Math.round(0.25 * FPS));
  if (Number.isFinite(lagV)) st.lagsVowel.push(lagV * 1000);

  // K2: jaw opening during speech.
  for (let n = 0; n < nF; n++) if (lab.group[n] > G.SIL && lab.group[n] >= 0) st.jaw.push(jaw[n]);

  // Smoothness: share of motion energy above 10 Hz.
  const sm = highShare(shown, 10);
  st.smooth.high += sm.high;
  st.smooth.total += sm.total;
}

function smoothSeries(x, sigma) {
  const n = x.length;
  const half = Math.ceil(3 * sigma);
  const out = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    let s = 0;
    let wsum = 0;
    for (let k = -half; k <= half; k++) {
      const m = i + k;
      if (m < 0 || m >= n) continue;
      const wk = Math.exp(-0.5 * (k / sigma) ** 2);
      s += wk * x[m];
      wsum += wk;
    }
    out[i] = s / wsum;
  }
  return out;
}

/** Lag (seconds) at which `b` best matches `a`; positive = b is late. Parabolic refinement. */
function crossLag(a, b, maxLag) {
  const n = a.length;
  const ma = sum(a) / n;
  const mb = sum(b) / n;
  const c = [];
  for (let L = -maxLag; L <= maxLag; L++) {
    let s = 0;
    let na = 0;
    let nb = 0;
    for (let i = 0; i < n; i++) {
      const j = i + L;
      if (j < 0 || j >= n) continue;
      const x = a[i] - ma;
      const y = b[j] - mb;
      s += x * y;
      na += x * x;
      nb += y * y;
    }
    c.push(na > 0 && nb > 0 ? s / Math.sqrt(na * nb) : -1);
  }
  let k = 0;
  for (let i = 1; i < c.length; i++) if (c[i] > c[k]) k = i;
  let off = 0;
  if (k > 0 && k < c.length - 1) {
    const d = c[k - 1] - 2 * c[k] + c[k + 1];
    if (d < 0) off = (0.5 * (c[k - 1] - c[k + 1])) / d;
  }
  return (k - maxLag + off) / FPS;
}

/** Motion energy above `hz` against all motion energy (DC excluded), summed over the 13 non-sil weights. */
function highShare(shown, hz) {
  const n = shown.length;
  let high = 0;
  let total = 0;
  const cut = hz / FPS; // cycles per frame
  const re = new Float64Array(n);
  for (let v = 1; v < VISEME_COUNT; v++) {
    let mean = 0;
    for (let i = 0; i < n; i++) mean += shown[i][v];
    mean /= n;
    for (let i = 0; i < n; i++) re[i] = shown[i][v] - mean;
    for (let k = 1; k <= n / 2; k++) {
      let r = 0;
      let im = 0;
      const w = (2 * Math.PI * k) / n;
      for (let i = 0; i < n; i++) {
        r += re[i] * Math.cos(w * i);
        im -= re[i] * Math.sin(w * i);
      }
      const e = r * r + im * im;
      total += e;
      if (k / n > cut) high += e;
    }
  }
  return { high, total };
}

function newStats() {
  return {
    vowel: { conf: [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], long: { hit: 0, miss: 0 }, short: { hit: 0, miss: 0 }, perLongClass: {} },
    k1: [],
    groupConf: GROUPS.map(() => GROUPS.map(() => 0)),
    sil: { n: 0, hit: 0 },
    frames: { n: 0, strict: 0, lenient: 0 },
    matrix14: VISEMES.map(() => VISEMES.map(() => 0)),
    speechFrames: 0,
    closure: {},
    closureOnset: [],
    k3: [0, 0],
    falseClosures: 0,
    speechSeconds: 0,
    lags: [],
    lagsVowel: [],
    perLine: [],
    jaw: [],
    smooth: { high: 0, total: 0 },
  };
}

// ---------------------------------------------------------------------------------------------
// Summary

function summarise(st) {
  const conf = st.vowel.conf;
  const rows = conf.map((r) => sum(r));
  const total = sum(rows);
  const correct = conf[0][0] + conf[1][1] + conf[2][2];
  const recall = conf.map((r, i) => (rows[i] ? r[i] / rows[i] : NaN));
  const rate = (hm) => (hm.hit + hm.miss ? hm.hit / (hm.hit + hm.miss) : NaN);
  const closure = {};
  for (const [k, [h, m]] of Object.entries(st.closure)) closure[k] = { hit: h, n: h + m, rate: h / (h + m) };
  const sumMs = (a) => median(a);
  return {
    vowelIdentity: {
      accuracy: total ? correct / total : NaN,
      alwaysA: total ? rows[0] / total : NaN,
      n: total,
      recall: { a: recall[0], i: recall[1], u: recall[2] },
      confusion_rows_gt_a_i_u_cols_pred_a_i_u_none: conf,
      long: rate(st.vowel.long),
      short: rate(st.vowel.short),
      nLong: st.vowel.long.hit + st.vowel.long.miss,
      nShort: st.vowel.short.hit + st.vowel.short.miss,
    },
    frameAccuracy: {
      strict: st.frames.n ? st.frames.strict / st.frames.n : NaN,
      lenient: st.frames.n ? st.frames.lenient / st.frames.n : NaN,
      n: st.frames.n,
      silenceHit: st.sil.n ? st.sil.hit / st.sil.n : NaN,
    },
    closure,
    falseClosuresPerSecond: st.speechSeconds ? st.falseClosures / st.speechSeconds : NaN,
    lagMs: { median: median(st.lags), p10: percentile(st.lags, 0.1), p90: percentile(st.lags, 0.9), n: st.lags.length },
    lagVowelMs: { median: median(st.lagsVowel), p10: percentile(st.lagsVowel, 0.1), p90: percentile(st.lagsVowel, 0.9) },
    closureOnsetMs: { median: sumMs(st.closureOnset), n: st.closureOnset.length },
    smoothHighShare: st.smooth.total ? st.smooth.high / st.smooth.total : NaN,
    k1_aaP75: percentile(st.k1, 0.75),
    k2_jawP90: percentile(st.jaw, 0.9),
    r1: perLineVerdict(st.perLine),
    k3_pp90Held: st.k3[0] + st.k3[1] ? st.k3[0] / (st.k3[0] + st.k3[1]) : NaN,
    matrices: { groupConfusion: st.groupConf, groups: GROUPS, viseme14: st.matrix14, visemes: VISEMES },
  };
}

/** R1: a line passes when its closure hit rate is at least 0.85 and its openness lag is in [-80, +20] ms. */
function perLineVerdict(perLine) {
  const lines = perLine.map((p) => {
    const rate = p.closureN ? p.closureHit / p.closureN : 1;
    return { name: p.name, closureRate: rate, lagMs: p.lagMs, pass: rate >= 0.85 && p.lagMs >= -80 && p.lagMs <= 20 };
  });
  return { pass: lines.filter((l) => l.pass).length, n: lines.length, lines };
}

const f2 = (x) => (Number.isFinite(x) ? x.toFixed(2) : 'n/a');
const f0 = (x) => (Number.isFinite(x) ? x.toFixed(0) : 'n/a');
const pct = (x) => (Number.isFinite(x) ? `${(100 * x).toFixed(1)}%` : 'n/a');

function printSummary(name, s) {
  const v = s.vowelIdentity;
  const cl = s.closure.all;
  console.log(`\n== ${name} ==`);
  console.log(
    `vowel identity  ${f2(v.accuracy)} (always-a ${f2(v.alwaysA)}, n=${v.n})  recall a ${f2(v.recall.a)} i ${f2(v.recall.i)} u ${f2(v.recall.u)}  long ${f2(v.long)} (${v.nLong})  short ${f2(v.short)} (${v.nShort})`,
  );
  console.log(`frame accuracy  strict ${pct(s.frameAccuracy.strict)}  lenient ${pct(s.frameAccuracy.lenient)}  silence ${pct(s.frameAccuracy.silenceHit)}  (n=${s.frameAccuracy.n})`);
  if (cl) {
    const letters = Object.entries(s.closure)
      .filter(([k]) => k.startsWith('letter:'))
      .map(([k, c]) => `${k.slice(7)} ${c.hit}/${c.n}`)
      .join('  ');
    const poss = Object.entries(s.closure)
      .filter(([k]) => k.startsWith('pos:'))
      .map(([k, c]) => `${k.slice(4)} ${c.hit}/${c.n}`)
      .join('  ');
    console.log(`closure hit     ${pct(cl.rate)} (${cl.hit}/${cl.n})  ${letters}  |  ${poss}`);
  }
  console.log(`false closures  ${f2(s.falseClosuresPerSecond)} per second`);
  console.log(`lag (openness)  median ${f0(s.lagMs.median)} ms  p10 ${f0(s.lagMs.p10)}  p90 ${f0(s.lagMs.p90)}  (n=${s.lagMs.n})`);
  console.log(`lag (open vowel) median ${f0(s.lagVowelMs.median)} ms  p10 ${f0(s.lagVowelMs.p10)}  p90 ${f0(s.lagVowelMs.p90)}`);
  console.log(`closure onset   median ${f0(s.closureOnsetMs.median)} ms (n=${s.closureOnsetMs.n})`);
  console.log(`lines passing R1 (closure >= .85 and lag in [-80, +20])  ${s.r1.pass}/${s.r1.n}`);
  console.log(`>10 Hz share    ${pct(s.smoothHighShare)}`);
  console.log(`K1 aa p75       ${f2(s.k1_aaP75)}   K2 jaw p90 ${f2(s.k2_jawP90)} of JAW.max   K3 PP>=0.9 held 50 ms ${pct(s.k3_pp90Held)}`);
}

// ---------------------------------------------------------------------------------------------
// Main

export async function main(argv = process.argv.slice(2), ctx = {}) {
  const args = parseArgs(argv);
  setMeshGains({ mesh: args.mesh ?? 'anim3', divisor: args.divisor !== 'off' });
  const ts = loadTestset();
  const lines = ts.lines.filter((l) => args.split === 'all' || l.split === args.split);
  if (!lines.length) throw new Error(`no lines for split ${args.split}`);
  const variants = ['diac', 'plain'];

  // Load clips and run the engine once per clip.
  const clips = [];
  const t0 = Date.now();
  for (const l of lines) {
    for (const variant of variants) {
      const clip = loadClip(l.id, variant);
      clip.split = l.split;
      clip.run = runClip(clip, args, ctx);
      clips.push(clip);
    }
  }
  const msPerFrame = (Date.now() - t0) / clips.reduce((s, c) => s + c.run.frames.length, 0);

  // G0: validity of the labels (diac clips of the same split, plus the bias per variant).
  const diac = clips.filter((c) => c.variant === 'diac');
  const engineFrames = new Map(diac.map((c) => [c.name, c.run.frames]));
  const g0 = validate(diac, engineFrames);
  const bias = { diac: g0.bias, plain: biasFor(clips.filter((c) => c.variant === 'plain')).bias };
  if (!args.quiet) {
    console.log(`split ${args.split}, mode ${args.mode}, lang ${args.lang}, stress ${args.stress}, ${lines.length} lines`);
    console.log('\nG0 ground-truth validity');
    for (const c of g0.checks) console.log(`  ${c.ok ? 'PASS' : 'FAIL'}  ${c.text}`);
    console.log(`  plain-variant alignment bias ${f0(bias.plain * 1000)} ms`);
  }

  const stats = {};
  for (const clip of clips) scoreClip(clip, clip.run, Number.isFinite(bias[clip.variant]) ? bias[clip.variant] : 0, stats);
  const report = {
    args,
    when: new Date().toISOString(),
    g0: { pass: g0.pass, checks: g0.checks.map((c) => ({ id: c.id, ok: c.ok, text: c.text })), bias },
    msPerFrame,
    results: {},
  };
  for (const variant of variants) {
    const s = summarise(stats[variant] ?? newStats());
    report.results[variant] = s;
    if (!args.quiet) printSummary(`${variant} audio (${args.mode}, ${args.split})`, s);
  }
  if (!args.quiet) console.log(`\nengine cost ${msPerFrame.toFixed(3)} ms per frame (includes loading and the offline FFT)`);
  const tag = args.tag || `${args.mode}-${args.split}-${args.stress}-${args.lang}`;
  fs.writeFileSync(path.join(EVAL_DIR, `report-${tag}.json`), JSON.stringify(report, null, 1));
  return report;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2), { makeTimeline }).then(
    (r) => {
      process.exitCode = r.g0.pass ? 0 : 3;
    },
    (e) => {
      console.error(e);
      process.exitCode = 1;
    },
  );
}
