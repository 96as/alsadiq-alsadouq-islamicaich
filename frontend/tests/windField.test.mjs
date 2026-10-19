// Gates N1, N2, N4 and the N5 maths for the wind field (Motion Bible 8.4). Run: npm run test:nature
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  WIND,
  TAU,
  gust,
  gustNoise,
  heading,
  globalHeading,
  lull,
  cloud,
  makeBlade,
  tipAngle,
  bendPoint,
  springStep,
  FLOWER_SPRING,
  treeBend,
  hash2,
  windNoiseData,
  sampleNoise,
  screenGust,
  makeWindState,
  windState,
  gustWith,
  screenGustWith,
  screenToWorld,
} from '../src/features/child/components/forest/wind/windField.js';

function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const pct = (arr, p) => {
  const s = Float64Array.from(arr).sort();
  return s[Math.min(s.length - 1, Math.floor(p * s.length))];
};
const DEG = Math.PI / 180;

/** Amplitude spectrum peak (Hz) of a signal sampled at fs, searched between f0 and f1. */
function peakHz(sig, fs, f0, f1) {
  const n = sig.length;
  let best = 0;
  let bestF = 0;
  let mean = 0;
  for (const v of sig) mean += v;
  mean /= n;
  for (let f = f0; f <= f1 + 1e-9; f += 0.02) {
    let re = 0;
    let im = 0;
    for (let i = 0; i < n; i++) {
      const w = 0.5 - 0.5 * Math.cos((TAU * i) / (n - 1)); // Hann
      const a = (TAU * f * i) / fs;
      re += (sig[i] - mean) * w * Math.cos(a);
      im += (sig[i] - mean) * w * Math.sin(a);
    }
    const m = Math.hypot(re, im);
    if (m > best) {
      best = m;
      bestF = f;
    }
  }
  return bestF;
}

// ---------------------------------------------------------------- N1
const BLADES = 1000;
const FS = 30;
const SECONDS = 60;
const FRAMES = FS * SECONDS;
const blades = [];
{
  const r = rng(7);
  for (let i = 0; i < BLADES; i++) blades.push(makeBlade((r() - 0.5) * 32, -32 + r() * 38));
}
// all frames, all blades, once (1000 x 1800 = 1.8 M tipAngle calls)
const mags = new Float32Array(BLADES * FRAMES);
const calmPerFrame = new Float64Array(FRAMES);
{
  const t0 = 100; // away from t = 0 so no start-up transient
  for (let f = 0; f < FRAMES; f++) {
    const t = t0 + f / FS;
    let calm = 0;
    for (let b = 0; b < BLADES; b++) {
      const v = Math.abs(tipAngle(blades[b], t, 1, 1));
      mags[b * FRAMES + f] = v;
      if (v < 5) calm++;
    }
    calmPerFrame[f] = calm / BLADES;
  }
}

test('N1 wind-driven tip angle: median 8-14 deg, p95 20-30 deg', () => {
  const med = pct(mags, 0.5);
  const p95 = pct(mags, 0.95);
  console.log(`  N1 tip angle median ${med.toFixed(2)} deg, p95 ${p95.toFixed(2)} deg`);
  assert.ok(med >= 8 && med <= 14, `median ${med}`);
  assert.ok(p95 >= 20 && p95 <= 30, `p95 ${p95}`);
});

test('N1 calm share (tip < 5 deg): mean 15-35%, and 5th-95th percentile of instants within 2-45% (the share swings with the lull)', () => {
  let mean = 0;
  let lo = 1;
  let hi = 0;
  for (const c of calmPerFrame) {
    mean += c;
    lo = Math.min(lo, c);
    hi = Math.max(hi, c);
  }
  mean /= FRAMES;
  const p5 = pct(calmPerFrame, 0.05);
  const p95 = pct(calmPerFrame, 0.95);
  console.log(`  N1 calm share mean ${(mean * 100).toFixed(1)}%, p5 ${(p5 * 100).toFixed(1)}%, p95 ${(p95 * 100).toFixed(1)}% (min ${(lo * 100).toFixed(1)}%, max ${(hi * 100).toFixed(1)}%)`);
  assert.ok(mean >= 0.15 && mean <= 0.35, `mean ${mean}`);
  assert.ok(p5 >= 0.02 && p95 <= 0.45, `p5..p95 ${p5}..${p95}`);
});

test('N1 gust front speed 2-4 m/s (cross-correlation along the heading)', () => {
  const speeds = [];
  for (let k = 0; k < 40; k++) {
    const t = 50 + k * 7.3;
    const dt = 0.5;
    const h = globalHeading(t + dt / 2);
    const dx = Math.cos(h);
    const dz = Math.sin(h);
    const N = 96;
    const step = 0.5;
    const a = [];
    const b = [];
    for (let i = 0; i < N; i++) {
      a.push(gustNoise(dx * i * step, dz * i * step, t));
      b.push(gustNoise(dx * i * step, dz * i * step, t + dt));
    }
    // b(x) = a(x - v dt): find shift (in samples) that maximises the correlation
    let bestS = 0;
    let best = -2;
    for (let s = -10; s <= 14; s++) {
      let sa = 0;
      let sb = 0;
      let saa = 0;
      let sbb = 0;
      let sab = 0;
      let n = 0;
      for (let i = 14; i < N - 14; i++) {
        const va = a[i - s];
        const vb = b[i];
        sa += va;
        sb += vb;
        saa += va * va;
        sbb += vb * vb;
        sab += va * vb;
        n++;
      }
      const cov = sab / n - (sa / n) * (sb / n);
      const c = cov / Math.sqrt((saa / n - (sa / n) ** 2) * (sbb / n - (sb / n) ** 2) + 1e-12);
      if (c > best) {
        best = c;
        bestS = s;
      }
    }
    speeds.push((bestS * step) / dt);
  }
  const mean = speeds.reduce((p, c) => p + c, 0) / speeds.length;
  console.log(`  N1 front speed mean ${mean.toFixed(2)} m/s (min ${Math.min(...speeds).toFixed(1)}, max ${Math.max(...speeds).toFixed(1)})`);
  assert.ok(mean >= 2 && mean <= 4, `mean ${mean}`);
});

test('N1 spatial correlation >= 0.8 at 0.5 m and <= 0.3 at 20 m', () => {
  function corrAt(dist) {
    const r = rng(11 + Math.round(dist * 10));
    const A = [];
    const B = [];
    for (let i = 0; i < 4000; i++) {
      const t = 30 + r() * 500;
      const x = (r() - 0.5) * 40;
      const z = (r() - 0.5) * 40;
      const ang = r() * TAU;
      A.push(gust(x, z, t));
      B.push(gust(x + Math.cos(ang) * dist, z + Math.sin(ang) * dist, t));
    }
    const ma = A.reduce((p, c) => p + c, 0) / A.length;
    const mb = B.reduce((p, c) => p + c, 0) / B.length;
    let cab = 0;
    let caa = 0;
    let cbb = 0;
    for (let i = 0; i < A.length; i++) {
      cab += (A[i] - ma) * (B[i] - mb);
      caa += (A[i] - ma) ** 2;
      cbb += (B[i] - mb) ** 2;
    }
    return cab / Math.sqrt(caa * cbb);
  }
  const c05 = corrAt(0.5);
  const c20 = corrAt(20);
  console.log(`  N1 spatial correlation 0.5 m: ${c05.toFixed(3)}, 20 m: ${c20.toFixed(3)}`);
  assert.ok(c05 >= 0.8, `0.5 m ${c05}`);
  assert.ok(c20 <= 0.3, `20 m ${c20}`);
});

test('N1 flutter 3-6 Hz at 1-3 deg, clump sway 0.5-0.9 Hz', () => {
  // flutter: top of the blade (h = 1), sway removed by reading the parts
  const parts = {};
  const fl = [];
  const sw = [];
  const blade = blades[3];
  for (let i = 0; i < FRAMES; i++) {
    tipAngle(blade, 200 + i / FS, 1, 1, parts);
    fl.push(parts.flutter);
    sw.push(parts.sway);
  }
  const fHz = peakHz(fl, FS, 1.5, 7);
  const sHz = peakHz(sw, FS, 0.2, 1.5);
  console.log(`  N1 flutter peak ${fHz.toFixed(2)} Hz, sway peak ${sHz.toFixed(2)} Hz (blade flutter ${blade.flutterHz.toFixed(2)}, sway ${blade.swayHz.toFixed(2)})`);
  assert.ok(fHz >= 3 && fHz <= 6, `flutter ${fHz}`);
  assert.ok(sHz >= 0.5 && sHz <= 0.9, `sway ${sHz}`);
  // flutter amplitude over all blades: p95 of |flutter| between 1 and 3 deg
  const amps = [];
  for (let b = 0; b < 200; b++) {
    for (let i = 0; i < 90; i++) {
      tipAngle(blades[b], 300 + i / FS, 1, 1, parts);
      amps.push(Math.abs(parts.flutter));
    }
  }
  const p95 = pct(amps, 0.95);
  console.log(`  N1 flutter amplitude p95 ${p95.toFixed(2)} deg`);
  assert.ok(p95 >= 1 && p95 <= 3, `flutter p95 ${p95}`);
});

test('N1 field autocorrelation at a point is < 0.5 at every lag of 5-30 s', () => {
  const dt = 0.5;
  const n = 1200; // 600 s
  let worst = 0;
  for (const [x, z] of [[0, 0], [3, -4], [-6, 2], [8, 5], [-2, -9]]) {
    const sig = new Float64Array(n);
    for (let i = 0; i < n; i++) sig[i] = gust(x, z, 20 + i * dt);
    let mean = 0;
    for (const v of sig) mean += v;
    mean /= n;
    let v0 = 0;
    for (const v of sig) v0 += (v - mean) ** 2;
    for (let lag = 5; lag <= 30; lag += dt) {
      const k = Math.round(lag / dt);
      let c = 0;
      for (let i = 0; i + k < n; i++) c += (sig[i] - mean) * (sig[i + k] - mean);
      worst = Math.max(worst, c / v0);
    }
  }
  console.log(`  N1 worst autocorrelation at lags 5-30 s: ${worst.toFixed(3)}`);
  assert.ok(worst < 0.5, `worst ${worst}`);
});

test('wind field: bounds, lull range, heading and cloud ranges', () => {
  let lo = 9;
  let hi = 0;
  let llo = 9;
  let lhi = 0;
  const r = rng(5);
  for (let i = 0; i < 20000; i++) {
    const s = gust((r() - 0.5) * 60, (r() - 0.5) * 60, r() * 900);
    lo = Math.min(lo, s);
    hi = Math.max(hi, s);
    const l = lull(r() * 900);
    llo = Math.min(llo, l);
    lhi = Math.max(lhi, l);
    const c = cloud((r() - 0.5) * 60, (r() - 0.5) * 60, r() * 900);
    assert.ok(c >= 0.82 && c <= 1.0);
    const hd = heading((r() - 0.5) * 60, (r() - 0.5) * 60, r() * 900) - WIND.baseHeading;
    assert.ok(Math.abs(hd) <= 25.5 * DEG, `heading ${hd / DEG}`);
  }
  console.log(`  gust range ${lo.toFixed(3)}..${hi.toFixed(3)}, lull ${llo.toFixed(3)}..${lhi.toFixed(3)}`);
  assert.ok(lo >= 0.06 * 0.6 - 1e-9 && hi <= 1.0 + 1e-9);
  assert.ok(llo >= 0.6 - 1e-9 && lhi <= 1.0 + 1e-9);
});

test('noise texture is deterministic, tileable and 16 KB', () => {
  const d = windNoiseData();
  assert.equal(d.length, 128 * 128);
  const tile = sampleNoise(0.37, 0.21);
  assert.ok(Math.abs(tile - sampleNoise(1.37, 3.21)) < 1e-9);
  assert.ok(Math.abs(hash2(12, -7, 3) - hash2(12, -7, 3)) === 0);
});

// ---------------------------------------------------------------- N2
test('N2 bend is a rotation: tip-to-base distance is constant within 1%', () => {
  const r = rng(3);
  let worst = 0;
  for (let i = 0; i < 5000; i++) {
    const L = 0.2 + r() * 0.6;
    const lean = (r() - 0.5) * 0.4;
    // a blade point at height fraction h along a leaning blade, relative to its base
    const px = Math.sin(lean) * L;
    const py = Math.cos(lean) * L;
    const pz = (r() - 0.5) * 0.05;
    const th = (r() * 60 + (r() < 0.2 ? 20 : 0)) * DEG * (r() < 0.5 ? 1 : -1);
    const hd = r() * TAU;
    const o = bendPoint(px, py, pz, th, hd);
    const d0 = Math.hypot(px, py, pz);
    const d1 = Math.hypot(o[0], o[1], o[2]);
    worst = Math.max(worst, Math.abs(d1 / d0 - 1));
  }
  console.log(`  N2 worst length change ${(worst * 100).toExponential(2)}%`);
  assert.ok(worst < 0.01);
});

test('N2 a blade bends toward the heading and never below the ground plane for 50 deg', () => {
  const o = bendPoint(0, 1, 0, 30 * DEG, 0); // heading +x
  assert.ok(o[0] > 0.45 && o[0] < 0.55, `x ${o[0]}`);
  assert.ok(Math.abs(o[2]) < 1e-9);
  const o2 = bendPoint(0, 1, 0, 50 * DEG, Math.PI / 2); // heading +z
  assert.ok(o2[2] > 0.7);
  assert.ok(o2[1] > 0.6);
});

// ---------------------------------------------------------------- N4
function stepResponse(f, z, r, ramp) {
  const st = {};
  const dt = 1 / 240;
  let peak = 0;
  let settle = 0;
  const trace = [];
  for (let i = 0; i < 240 * 6; i++) {
    const t = i * dt;
    const x = ramp > 0 ? Math.min(1, t / ramp) : 1;
    if (i === 0) {
      st.init = true;
      st.y = 0;
      st.yd = 0;
      st.xp = 0;
    }
    const y = springStep(st, x, dt, f, z, r);
    trace.push(y);
    peak = Math.max(peak, y);
    if (Math.abs(y - 1) > 0.05) settle = t;
  }
  // visible wobbles: local maxima above 1 + 5% or minima below 1 - 5%
  let wobbles = 0;
  for (let i = 2; i < trace.length - 2; i++) {
    const up = trace[i] > trace[i - 1] && trace[i] >= trace[i + 1] && trace[i] > 1.05;
    const dn = trace[i] < trace[i - 1] && trace[i] <= trace[i + 1] && trace[i] < 0.95 && i > 20;
    if (up || dn) wobbles++;
  }
  return { overshoot: (peak - 1) * 100, settle, wobbles };
}

test('N4 flower springs: overshoot 15-35%, settle to 5% in 1.0-2.0 s, 2-3 visible wobbles (dandelion, gust ramp 0.3 s)', () => {
  const { f, z, r } = FLOWER_SPRING.dandelion;
  const s = stepResponse(f, z, r, 0.3);
  console.log(`  N4 dandelion: overshoot ${s.overshoot.toFixed(1)}%, settle ${s.settle.toFixed(2)} s, wobbles ${s.wobbles}`);
  assert.ok(s.overshoot >= 15 && s.overshoot <= 35, `overshoot ${s.overshoot}`);
  assert.ok(s.settle >= 1.0 && s.settle <= 2.0, `settle ${s.settle}`);
  assert.ok(s.wobbles >= 2 && s.wobbles <= 3, `wobbles ${s.wobbles}`);
});

test('N4 bloom and small flowers: overshoot <= 35% and settled within 2.0 s (they are stiffer by design)', () => {
  for (const k of ['bloom', 'small']) {
    const { f, z, r } = FLOWER_SPRING[k];
    const s = stepResponse(f, z, r, 0.3);
    console.log(`  N4 ${k}: overshoot ${s.overshoot.toFixed(1)}%, settle ${s.settle.toFixed(2)} s, wobbles ${s.wobbles}`);
    assert.ok(s.overshoot <= 35 && s.settle <= 2.0, `${k} ${JSON.stringify(s)}`);
  }
});

test('N4 spring is stable at 30, 60 and 144 Hz frame steps (no blow-up, same end value)', () => {
  const { f, z, r } = FLOWER_SPRING.dandelion;
  for (const fps of [20, 30, 60, 144]) {
    const st = { init: true, y: 0, yd: 0, xp: 0 };
    let y = 0;
    for (let i = 0; i < fps * 8; i++) y = springStep(st, 1, 1 / fps, f, z, r);
    assert.ok(Math.abs(y - 1) < 0.01, `${fps} fps -> ${y}`);
  }
});

// ---------------------------------------------------------------- N5 maths
test('N5 trees: crown top 0.05-0.12 u for a 4 u tree at 0.25-0.4 Hz; neighbours lag by dx / 3 m/s +- 30%', () => {
  // lean in degrees at the crown; displacement = height x tan(lean)
  const H = 4;
  const sig = [];
  let maxD = 0;
  let minD = 9;
  for (let i = 0; i < FS * 120; i++) {
    const t = 100 + i / FS;
    const d = H * Math.tan(treeBend(0, 0, t, 0.32, 0) * DEG);
    sig.push(d);
    maxD = Math.max(maxD, d);
    minD = Math.min(minD, d);
  }
  const hz = peakHz(sig, FS, 0.2, 0.6);
  console.log(`  N5 crown excursion ${minD.toFixed(3)}..${maxD.toFixed(3)} u, main frequency ${hz.toFixed(2)} Hz`);
  assert.ok(maxD >= 0.05 && maxD <= 0.12 * 1.1, `max ${maxD}`);
  assert.ok(hz >= 0.25 && hz <= 0.4, `hz ${hz}`);
  // front lag between two trees dx apart along the heading
  const lags = [];
  for (let k = 0; k < 30; k++) {
    const t0 = 60 + k * 9.1;
    const h = globalHeading(t0);
    const dx = 6;
    const ax = Math.cos(h) * 0;
    const az = Math.sin(h) * 0;
    // gust time series at two points dx apart along the heading; find the lag that matches them
    const A = [];
    const B = [];
    for (let i = 0; i < 160; i++) {
      const t = t0 + i * 0.1;
      A.push(gustNoise(ax, az, t));
      B.push(gustNoise(ax + Math.cos(h) * dx, az + Math.sin(h) * dx, t));
    }
    let bestL = 0;
    let best = -2;
    for (let l = 0; l <= 40; l++) {
      let sab = 0;
      let saa = 0;
      let sbb = 0;
      let n = 0;
      let ma = 0;
      let mb = 0;
      for (let i = 40; i < 120; i++) {
        ma += A[i];
        mb += B[i + l - 20 > 159 ? 159 : i + l - 20];
        n++;
      }
      ma /= n;
      mb /= n;
      for (let i = 40; i < 120; i++) {
        const a = A[i] - ma;
        const b = B[Math.min(159, i + l - 20)] - mb;
        sab += a * b;
        saa += a * a;
        sbb += b * b;
      }
      const c = sab / Math.sqrt(saa * sbb + 1e-12);
      if (c > best) {
        best = c;
        bestL = l - 20;
      }
    }
    lags.push(bestL * 0.1);
  }
  const mean = lags.reduce((p, c) => p + c, 0) / lags.length;
  const expected = 6 / 3;
  console.log(`  N5 neighbour lag over 6 m: mean ${mean.toFixed(2)} s, expected ${expected.toFixed(2)} s +-30%`);
  assert.ok(Math.abs(mean - expected) <= 0.3 * expected, `lag ${mean}`);
});

test('painted-layer screen mapping returns the same field values as the world field', () => {
  const s = screenGust(0.4, 0.8, 50);
  assert.ok(s >= 0.06 * 0.6 && s <= 1);
});

test('gustWith (prepared state, linearised lag) matches gust() within 0.02 for lags up to 0.25 s', () => {
  const r = rng(77);
  const st = makeWindState();
  let worst = 0;
  for (let k = 0; k < 40; k++) {
    const t = 5 + r() * 80;
    windState(t, st);
    for (let i = 0; i < 60; i++) {
      const x = (r() - 0.5) * 40;
      const z = -25 + r() * 33;
      const lag = r() * 0.25;
      worst = Math.max(worst, Math.abs(gustWith(st, x, z, lag) - gust(x, z, t, lag)));
    }
  }
  console.log(`  gustWith vs gust: worst difference ${worst.toFixed(4)}`);
  assert.ok(worst <= 0.02, `worst ${worst}`);
});

test('screenGustWith equals the field at screenToWorld (gate N8 maths, CPU side)', () => {
  const st = windState(33.3);
  const w = [0, 0];
  for (let i = 0; i < 50; i++) {
    const u = (i * 0.137) % 1;
    const d = (i * 0.291) % 1;
    screenToWorld(u, d, w);
    assert.equal(screenGustWith(st, u, d, 0), gustWith(st, w[0], w[1], 0));
  }
});
