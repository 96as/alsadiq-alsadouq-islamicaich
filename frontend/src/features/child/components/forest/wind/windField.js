/**
 * The wind, as a field and not a clock (Motion Bible 7.1).
 *
 * One pure module (no three.js, no DOM) that holds the constants and a CPU mirror of the shader maths.
 * The grass and tree shaders, the flower springs, the particles, the butterflies, the foreground strip, the
 * painted-meadow layer (MeadowLife) and the tests all read it, so there is one wind in the whole scene.
 *
 * World axes: x is screen right, z points toward the camera, y is up. Lengths are metres; one scene unit
 * (u) is about one metre. Time is seconds. Angles are radians unless a name ends in Deg.
 *
 * How the field is built
 *   - A tileable 128 x 128 R8 noise (see makeWindNoise) is the only data. The GPU samples it with LINEAR +
 *     REPEAT, and sampleNoise() below does the same bilinear lookup, so both sides agree to 1/255.
 *   - The gust pattern is "frozen turbulence" that travels: two layers (32 m and 51 m wavelength) slide along
 *     the heading at 3.0 and 2.2 m/s with a sideways drift, so a point never sees the same sequence twice.
 *   - The heading (where the fronts go) wanders +-25 degrees with a 200 m noise and drifts slowly in time.
 *   - A global lull multiplier (0.6-1.0, about 23 s) makes the meadow breathe.
 *   - Per blade: clump sway (0.55-0.85 Hz, per 1.6 m clump), flutter (3.5-5.5 Hz, top of the blade only) and
 *     tip lag (the tip reads the gust 0.22 s x h^2 late, which is the follow-through).
 */

export const TAU = Math.PI * 2;
const DEG = Math.PI / 180;

export const WIND = {
  // Heading: fronts travel screen left to right and about 27 deg toward the camera.
  baseHeading: Math.atan2(0.5, 1), // radians in the (x, z) plane
  headingSwingDeg: 25,
  headingScale: 0.005, // 1 / 200 m
  headingDrift: 0.007, // noise cells per second
  // Gust
  gustScale: 1 / 32,
  gustScaleB: 1 / 51,
  gustSpeed: 3.0, // m/s along the heading
  gustSpeedB: 2.2,
  sideDriftA: 0.7, // m/s across the heading, so the pattern never realigns with itself
  sideDriftB: 1.0,
  gustMixB: 0.4,
  gustContrast: 2.6, // stretches the noise so there are real calms and real gusts
  gustBias: 0.46, // centre of the stretch (above 0.5 lifts the typical gust)
  gustFloor: 0.25, // never dead calm
  // Lull: multiplier 0.6-1.0, about 23 s
  lullLo: 0.6,
  lullPeriod: 23,
  // Per blade
  tipDeg: 32, // wind bend at the blade tip for s = 1, stiffness 1
  swayDeg: 5,
  swayHzLo: 0.55,
  swayHzHi: 0.85,
  clumpSize: 1.6,
  flutterDeg: 2,
  flutterHzLo: 3.5,
  flutterHzHi: 5.5,
  flutterFrom: 0.55, // flutter lives on the top 45% of the blade
  flutterFadeNear: 8, // metres from the camera
  flutterFadeFar: 14,
  tipLag: 0.22, // seconds x h^2
  restLeanDegLo: 4,
  restLeanDegHi: 10,
  // Clouds
  cloudScale: 1 / 80,
  cloudSpeed: 2.0,
  // Feet
  feetRadius: 0.42,
  feetLeanDeg: 50,
  feetDamp: 0.85,
};

/* ---------- the noise texture data ---------- */

export const NOISE_SIZE = 128;

function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** A seeded, tileable value noise: two octaves (lattice 3 and 6 cells over the tile). 16 KB, made at load. */
export function makeWindNoise(seed = 20261004) {
  const rnd = mulberry32(seed);
  const octaves = [
    { cells: 3, weight: 0.68 },
    { cells: 6, weight: 0.32 },
  ];
  const lattices = octaves.map((o) => {
    const g = new Float32Array(o.cells * o.cells);
    for (let i = 0; i < g.length; i++) g[i] = rnd();
    return g;
  });
  const out = new Uint8Array(NOISE_SIZE * NOISE_SIZE);
  const smooth = (t) => t * t * (3 - 2 * t);
  for (let y = 0; y < NOISE_SIZE; y++) {
    for (let x = 0; x < NOISE_SIZE; x++) {
      let v = 0;
      for (let k = 0; k < octaves.length; k++) {
        const n = octaves[k].cells;
        const gx = (x / NOISE_SIZE) * n;
        const gy = (y / NOISE_SIZE) * n;
        const x0 = Math.floor(gx);
        const y0 = Math.floor(gy);
        const fx = smooth(gx - x0);
        const fy = smooth(gy - y0);
        const g = lattices[k];
        const a = g[(y0 % n) * n + (x0 % n)];
        const b = g[(y0 % n) * n + ((x0 + 1) % n)];
        const c = g[(((y0 + 1) % n) * n) + (x0 % n)];
        const d = g[(((y0 + 1) % n) * n) + ((x0 + 1) % n)];
        v += octaves[k].weight * ((a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy);
      }
      out[y * NOISE_SIZE + x] = Math.max(0, Math.min(255, Math.round(v * 255)));
    }
  }
  return out;
}

let noiseData = null;
/** The shared noise (made on first use). The texture uploaded to the GPU is this same array. */
export function windNoiseData() {
  if (!noiseData) noiseData = makeWindNoise();
  return noiseData;
}

/** Bilinear, wrapping lookup in tile units, the same as LINEAR + REPEAT on the GPU. Returns 0..1. */
export function sampleNoise(u, v, data = windNoiseData()) {
  const N = NOISE_SIZE;
  const fx = u * N - 0.5;
  const fy = v * N - 0.5;
  const x0 = Math.floor(fx);
  const y0 = Math.floor(fy);
  const tx = fx - x0;
  const ty = fy - y0;
  const xa = ((x0 % N) + N) % N;
  const xb = (xa + 1) % N;
  const ya = ((y0 % N) + N) % N;
  const yb = (ya + 1) % N;
  const a = data[ya * N + xa];
  const b = data[ya * N + xb];
  const c = data[yb * N + xa];
  const d = data[yb * N + xb];
  return ((a + (b - a) * tx) * (1 - ty) + (c + (d - c) * tx) * ty) / 255;
}

/* ---------- integer hash (the same lowbias32 in GLSL, so per-blade values agree exactly) ---------- */

/** Hash of two integers and a salt to [0, 1). GLSL twin: hash21u in windGlsl.js. */
export function hash2(ix, iz, salt = 0) {
  let h = (Math.imul(ix | 0, 0x1b873593) ^ Math.imul(iz | 0, 0x2545f491) ^ Math.imul(salt | 0, 0x9e3779b1)) >>> 0;
  h ^= h >>> 16;
  h = Math.imul(h, 0x7feb352d) >>> 0;
  h ^= h >>> 15;
  h = Math.imul(h, 0x846ca68b) >>> 0;
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}

/* ---------- global (position free) signals: heading, advection offsets, lull ---------- */

/** Global heading wobble in radians (+-10 deg of the +-25): two slow sines, drifting at about 0.007 per second. */
function headingWobble(t) {
  return WIND.headingSwingDeg * 0.4 * DEG * (0.62 * Math.sin((TAU * t) / 143 + 0.7) + 0.38 * Math.sin((TAU * t) / 89 + 2.1));
}
/** Integral of the wobble (small-angle), so the pattern slides sideways smoothly instead of jumping. */
function headingWobbleIntegral(t) {
  const A = WIND.headingSwingDeg * 0.4 * DEG;
  return A * (-0.62 * (143 / TAU) * Math.cos((TAU * t) / 143 + 0.7) - 0.38 * (89 / TAU) * Math.cos((TAU * t) / 89 + 2.1));
}

/** Where the fronts go right now (radians in the x, z plane). */
export function globalHeading(t) {
  return WIND.baseHeading + headingWobble(t);
}

/** Lull multiplier 0.6-1.0 (about 23 s, with a slower beat so it is not a pure sine). */
export function lull(t) {
  const n = 0.5 + 0.5 * (0.7 * Math.sin((TAU * t) / WIND.lullPeriod + 0.4) + 0.3 * Math.sin((TAU * t) / 37.1 + 1.9));
  return WIND.lullLo + (1 - WIND.lullLo) * n;
}

/**
 * Advection offset of a gust layer in metres, wrapped to one tile so a uniform stays small and precise
 * (the tile is 1 / scale metres). out = [ox, oz].
 */
export function advectOffset(t, speed, side, tileMeters, out = [0, 0]) {
  const h0 = WIND.baseHeading;
  const dx = Math.cos(h0);
  const dz = Math.sin(h0);
  const along = speed * t;
  const across = side * t + speed * headingWobbleIntegral(t);
  // across direction = (-dz, dx)
  const ox = dx * along - dz * across;
  const oz = dz * along + dx * across;
  out[0] = ((ox % tileMeters) + tileMeters) % tileMeters;
  out[1] = ((oz % tileMeters) + tileMeters) % tileMeters;
  return out;
}

const _oa = [0, 0];
const _ob = [0, 0];

function contrast(n) {
  const v = WIND.gustBias + (n - 0.5) * WIND.gustContrast;
  return v < 0 ? 0 : v > 1 ? 1 : v;
}

/** Raw gust noise 0..1 at a point (before the floor and the square). */
export function gustNoise(x, z, t) {
  advectOffset(t, WIND.gustSpeed, WIND.sideDriftA, 1 / WIND.gustScale, _oa);
  advectOffset(t, WIND.gustSpeedB, WIND.sideDriftB, 1 / WIND.gustScaleB, _ob);
  const a = sampleNoise((x - _oa[0]) * WIND.gustScale, (z - _oa[1]) * WIND.gustScale);
  const b = sampleNoise((x - _ob[0]) * WIND.gustScaleB + 0.31, (z - _ob[1]) * WIND.gustScaleB + 0.57);
  return a * (1 - WIND.gustMixB) + b * WIND.gustMixB;
}

/**
 * Gust strength s at a point, 0.06 to 1.0: mix(0.25, 1, n)^2, times the lull.
 * `lag` reads the field in the past (the tip lag of tall blades).
 */
export function gust(x, z, t, lag = 0) {
  const tt = t - lag;
  const n = contrast(gustNoise(x, z, tt));
  const m = WIND.gustFloor + (1 - WIND.gustFloor) * n;
  return m * m * lull(tt);
}

/* ---------- per-frame state (no allocation): the same numbers the shaders get as uniforms ---------- */

/**
 * Everything about the wind that does not depend on position, for one instant. Compute it once per frame with
 * windState(t, out) and hand it to gustWith(); the shaders receive the same fields as uniforms, so a blade, a
 * flower, a strip stem and a painted pixel all read one field. Velocities let a lagged read be linear:
 * the gust at time t - lag is the gust now, sampled `vel * lag` metres along the advection.
 */
export function makeWindState() {
  return {
    t: 0,
    offA: [0, 0],
    offB: [0, 0],
    velA: [0, 0],
    velB: [0, 0],
    lull: 1,
    heading: WIND.baseHeading,
    cloudOff: [0, 0],
  };
}

function advectVelocity(t, speed, side, out) {
  const h0 = WIND.baseHeading;
  const dx = Math.cos(h0);
  const dz = Math.sin(h0);
  const across = side + speed * headingWobble(t);
  out[0] = dx * speed - dz * across;
  out[1] = dz * speed + dx * across;
  return out;
}

export function windState(t, out = makeWindState()) {
  out.t = t;
  advectOffset(t, WIND.gustSpeed, WIND.sideDriftA, 1 / WIND.gustScale, out.offA);
  advectOffset(t, WIND.gustSpeedB, WIND.sideDriftB, 1 / WIND.gustScaleB, out.offB);
  advectVelocity(t, WIND.gustSpeed, WIND.sideDriftA, out.velA);
  advectVelocity(t, WIND.gustSpeedB, WIND.sideDriftB, out.velB);
  out.lull = lull(t);
  out.heading = globalHeading(t);
  out.cloudOff[0] = Math.cos(out.heading) * WIND.cloudSpeed * t;
  out.cloudOff[1] = Math.sin(out.heading) * WIND.cloudSpeed * t;
  return out;
}

/**
 * Gust strength at (x, z) from a prepared state, with a linearised lag (the gust `lag` seconds ago).
 * Within 0.02 of gust(x, z, t, lag) for the lags used (<= 0.25 s); see the tests.
 */
export function gustWith(st, x, z, lag = 0) {
  const a = sampleNoise((x - st.offA[0] + st.velA[0] * lag) * WIND.gustScale, (z - st.offA[1] + st.velA[1] * lag) * WIND.gustScale);
  const b = sampleNoise(
    (x - st.offB[0] + st.velB[0] * lag) * WIND.gustScaleB + 0.31,
    (z - st.offB[1] + st.velB[1] * lag) * WIND.gustScaleB + 0.57,
  );
  const n = contrast(a * (1 - WIND.gustMixB) + b * WIND.gustMixB);
  const m = WIND.gustFloor + (1 - WIND.gustFloor) * n;
  return m * m * st.lull;
}

/** Cloud shadow from a prepared state (1 = lit). */
export function cloudWith(st, x, z) {
  const n = sampleNoise((x - st.cloudOff[0]) * WIND.cloudScale + 0.43, (z - st.cloudOff[1]) * WIND.cloudScale + 0.29);
  const s = (n - 0.35) / 0.3;
  const k = s < 0 ? 0 : s > 1 ? 1 : s * s * (3 - 2 * s);
  return 0.82 + 0.18 * k;
}

/** Local heading (radians in x, z): the global heading plus a 200 m spatial swing of +-25 deg. */
export function heading(x, z, t) {
  const n = sampleNoise(x * WIND.headingScale + 0.13, z * WIND.headingScale + t * WIND.headingDrift + 0.71);
  return globalHeading(t) + (n * 2 - 1) * 0.6 * WIND.headingSwingDeg * DEG;
}

/** Cloud shadow value 0..1 (1 = lit): 80 m noise drifting at 2 m/s along the heading. */
export function cloud(x, z, t) {
  const h = globalHeading(t);
  const ox = Math.cos(h) * WIND.cloudSpeed * t;
  const oz = Math.sin(h) * WIND.cloudSpeed * t;
  const n = sampleNoise((x - ox) * WIND.cloudScale + 0.43, (z - oz) * WIND.cloudScale + 0.29);
  const s = (n - 0.35) / 0.3;
  const k = s < 0 ? 0 : s > 1 ? 1 : s * s * (3 - 2 * s);
  return 0.82 + 0.18 * k;
}

/* ---------- per blade ---------- */

/** Per-blade constants from the blade's base position (all from the hash, so the shader derives the same). */
export function makeBlade(x, z, out = {}) {
  const cx = Math.floor(x / WIND.clumpSize);
  const cz = Math.floor(z / WIND.clumpSize);
  const bx = Math.floor(x * 97.3);
  const bz = Math.floor(z * 97.3);
  out.x = x;
  out.z = z;
  out.stiff = 0.8 + 0.4 * hash2(bx, bz, 1);
  out.leanDeg = WIND.restLeanDegLo + (WIND.restLeanDegHi - WIND.restLeanDegLo) * hash2(bx, bz, 2);
  out.swayHz = WIND.swayHzLo + (WIND.swayHzHi - WIND.swayHzLo) * hash2(cx, cz, 3);
  out.swayPh = TAU * hash2(cx, cz, 4);
  out.flutterHz = WIND.flutterHzLo + (WIND.flutterHzHi - WIND.flutterHzLo) * hash2(bx, bz, 5);
  out.flutterPh = TAU * hash2(bx, bz, 6);
  return out;
}

/**
 * The wind-driven bend of a blade at height h (0 base, 1 tip), in degrees, signed along the heading.
 * parts (optional) receives { gust, sway, flutter, s } in degrees (s is the lagged strength).
 * The rest lean is not included. `fade` (0..1) is the camera-distance fade of the flutter.
 */
export function tipAngle(blade, t, h = 1, fade = 1, parts = null) {
  const lag = WIND.tipLag * h * h;
  const s = gust(blade.x, blade.z, t, lag);
  const h2 = h * h;
  const g = (WIND.tipDeg * s * h2) / blade.stiff;
  const sway = WIND.swayDeg * (0.4 + 0.6 * s) * h2 * Math.sin(TAU * blade.swayHz * t + blade.swayPh);
  const fh = h <= WIND.flutterFrom ? 0 : (h - WIND.flutterFrom) / (1 - WIND.flutterFrom);
  const fs = fh * fh * (3 - 2 * fh);
  const flutter = WIND.flutterDeg * (0.3 + 0.7 * s) * fs * fade * Math.sin(TAU * blade.flutterHz * t + blade.flutterPh);
  if (parts) {
    parts.gust = g;
    parts.sway = sway;
    parts.flutter = flutter;
    parts.s = s;
  }
  return g + sway + flutter;
}

/**
 * Rotate a blade point about its base around the axis cross(up, windDir) (the world-space bend of 7.2). The
 * maths is a pure rotation, so tip-to-base distance never changes (gate N2). Returns [dx, dy, dz] of the point
 * relative to the base after bending by `theta` radians toward `headingRad`.
 */
export function bendPoint(px, py, pz, theta, headingRad, out = [0, 0, 0]) {
  // axis a = cross(up, w) with w = (cos, 0, sin) = (-sin... ) computed explicitly, then Rodrigues.
  const wx = Math.cos(headingRad);
  const wz = Math.sin(headingRad);
  // cross((0,1,0), (wx,0,wz)) = (1*wz - 0*0, 0*wx - 0*wz, 0*0 - 1*wx) = (wz, 0, -wx)
  const ax = wz;
  const az = -wx;
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  const dot = ax * px + az * pz; // axis.y = 0
  // axis x p = (ay*pz - az*py, az*px - ax*pz, ax*py - ay*px) with ay = 0
  const kx = -az * py;
  const ky = az * px - ax * pz;
  const kz = ax * py;
  out[0] = px * c + kx * s + ax * dot * (1 - c);
  out[1] = py * c + ky * s;
  out[2] = pz * c + kz * s + az * dot * (1 - c);
  return out;
}

/* ---------- second-order spring (t3ssel8r form), used by the flowers ---------- */

/**
 * One step of a second-order system with frequency f (Hz), damping z and response r (Motion Bible 2.2):
 *   y + k1 y' + k2 y'' = x + k3 x'
 * state = { y, yd, xp, init }. Semi-implicit Euler with a stable k2 clamp. Returns the new y.
 */
export function springStep(state, x, dt, f, z, r) {
  if (!state.init) {
    state.y = x;
    state.yd = 0;
    state.xp = x;
    state.init = true;
  }
  const k1 = z / (Math.PI * f);
  const k2 = 1 / ((TAU * f) * (TAU * f));
  const k3 = (r * z) / (TAU * f);
  const xd = (x - state.xp) / dt;
  state.xp = x;
  const k2s = Math.max(k2, (dt * dt) / 2 + (dt * k1) / 2, dt * k1);
  state.y += dt * state.yd;
  state.yd += (dt * (x + k3 * xd - state.y - k1 * state.yd)) / k2s;
  return state.y;
}

/** Spring presets for flowers (7.4). */
export const FLOWER_SPRING = {
  dandelion: { f: 1.4, z: 0.25, r: 1.2 },
  bloom: { f: 2.0, z: 0.38, r: 1.2 },
  small: { f: 2.8, z: 0.5, r: 1.0 },
};

/* ---------- trees (7.5) ---------- */

/**
 * Crown lean of a tree in degrees at world (x, z): 0.6 deg + 1.2 deg x s, a main bend of 0.25-0.4 Hz whose phase
 * is the gust sampled at the tree (so a front visibly moves through a row). `hz` is the tree's own frequency.
 */
export function treeBend(x, z, t, hz = 0.32, phase = 0, parts = null) {
  const s = gust(x, z, t, 0);
  const slow = Math.sin(TAU * hz * t + phase + s * 2.2);
  const lean = 0.6 + 1.2 * s;
  const deg = lean * (0.6 + 0.4 * slow);
  if (parts) parts.s = s;
  return deg;
}

/* ---------- screen space (painted meadow layer and foreground strip) ---------- */

/**
 * Map a screen position to a world point on the ground plane so the painted layers read the same field as the
 * forest. u in 0..1 across the screen, depth01 in 0..1 from the horizon (0) to the bottom edge (1). The mapping
 * only needs to be smooth and consistent: 1 screen width is about 24 m at the bottom edge and grows toward the
 * horizon (about 76 m), like a perspective camera, so far gusts look smaller and travel slower on screen than
 * near ones. (It used to shrink toward the horizon, which made the far meadow sweep faster than the foreground.)
 */
export function screenToWorld(u, depth01, out = [0, 0]) {
  const d = Math.max(0.02, depth01);
  const spread = 24 / (0.3 + 0.7 * d);
  out[0] = (u - 0.5) * spread;
  out[1] = 6 - 30 * (1 - d) * (1 - d); // the far field is at negative z, like the forest's blades
  return out;
}

/** Gust strength at a screen position (painted layers). */
export function screenGust(u, depth01, t, lag = 0) {
  screenToWorld(u, depth01, _sw);
  return gust(_sw[0], _sw[1], t, lag);
}
const _sw = [0, 0];

/** Same as screenGust, from a prepared windState (no allocation). */
export function screenGustWith(st, u, depth01, lag = 0) {
  screenToWorld(u, depth01, _sw);
  return gustWith(st, _sw[0], _sw[1], lag);
}

/* ---------- reduced motion ---------- */

/** Scale factors used when the child prefers reduced motion (Motion Bible 2.5 / gate N9). */
export const REDUCED = { flutter: 0, wind: 0.25, warp: 0.25, particles: 0, shafts: 0 };
