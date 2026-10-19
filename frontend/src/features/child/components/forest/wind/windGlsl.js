// The GLSL twin of windField.js. One chunk, used by the three.js materials and by MeadowLife's raw WebGL2
// shader, so a blade, a tree, a painted pixel and the CPU mirror (flowers, strip, particles, tests) read the
// same wind. Constants are written from WIND, never typed twice.
//
// The chunk declares its own uniforms. Feed them with packWindUniforms() every frame:
//   uWindNoise  sampler2D  the 128 x 128 R8 noise (LINEAR + REPEAT)
//   uWOff       vec4       advection offsets of layer A and B (metres, wrapped to a tile)
//   uWVel       vec4       advection velocities of layer A and B (m/s, for the linear lag)
//   uWMisc      vec4       lull, heading (rad), cloud offset x and z (metres)
//   uWHeadT     float      time x headingDrift (the slow drift of the 200 m heading noise)
//
// Needs GLSL ES 3.00 (WebGL2): texture(), uint.

import { WIND } from './windField';

const f = (v) => (Number.isInteger(v) ? `${v}.0` : String(Number(v.toPrecision(9))));

export const WIND_GLSL = /* glsl */ `
uniform sampler2D uWindNoise;
uniform vec4 uWOff;
uniform vec4 uWVel;
uniform vec4 uWMisc;
uniform float uWHeadT;

// Gust strength 0.06..1: mix(floor, 1, n)^2 x lull. lag (s) reads the field in the past (linear).
float windGust(vec2 p, float lag) {
  vec2 pa = (p - uWOff.xy + uWVel.xy * lag) * ${f(WIND.gustScale)};
  vec2 pb = (p - uWOff.zw + uWVel.zw * lag) * ${f(WIND.gustScaleB)} + vec2(0.31, 0.57);
  float n = texture(uWindNoise, pa).r * ${f(1 - WIND.gustMixB)} + texture(uWindNoise, pb).r * ${f(WIND.gustMixB)};
  n = clamp(${f(WIND.gustBias)} + (n - 0.5) * ${f(WIND.gustContrast)}, 0.0, 1.0);
  float m = ${f(WIND.gustFloor)} + ${f(1 - WIND.gustFloor)} * n;
  return m * m * uWMisc.x;
}

// Local heading (radians in x, z): global heading plus the 200 m spatial swing.
float windHeading(vec2 p) {
  float n = texture(uWindNoise, p * ${f(WIND.headingScale)} + vec2(0.13, 0.71 + uWHeadT)).r;
  return uWMisc.y + (n * 2.0 - 1.0) * ${f(0.6 * WIND.headingSwingDeg * (Math.PI / 180))};
}

// Cloud shadow, 1 = lit.
float windCloud(vec2 p) {
  float n = texture(uWindNoise, (p - uWMisc.zw) * ${f(WIND.cloudScale)} + vec2(0.43, 0.29)).r;
  float s = clamp((n - 0.35) / 0.3, 0.0, 1.0);
  return 0.82 + 0.18 * (s * s * (3.0 - 2.0 * s));
}

// lowbias32 of two integers and a salt, the twin of hash2() in windField.js. 0..1.
float windHash(int ix, int iz, int salt) {
  uint h = (uint(ix) * 0x1b873593u) ^ (uint(iz) * 0x2545f491u) ^ (uint(salt) * 0x9e3779b1u);
  h ^= h >> 16u;
  h *= 0x7feb352du;
  h ^= h >> 15u;
  h *= 0x846ca68bu;
  h ^= h >> 16u;
  return float(h) / 4294967296.0;
}
`;

/**
 * Copy a windState (windField.windState) into the uniform values. `u` holds Float32Array-like vec4s in
 * { uWOff, uWVel, uWMisc } and a number in uWHeadT (a three.js uniform bag, or plain arrays for raw GL).
 * No allocation.
 */
export function packWindUniforms(st, u) {
  const o = u.uWOff.value || u.uWOff;
  const v = u.uWVel.value || u.uWVel;
  const m = u.uWMisc.value || u.uWMisc;
  // three.js Vector4 has set(x, y, z, w); typed arrays are written by index (their set() takes an array)
  if (o.isVector4) {
    o.set(st.offA[0], st.offA[1], st.offB[0], st.offB[1]);
    v.set(st.velA[0], st.velA[1], st.velB[0], st.velB[1]);
    m.set(st.lull, st.heading, st.cloudOff[0], st.cloudOff[1]);
  } else {
    o[0] = st.offA[0]; o[1] = st.offA[1]; o[2] = st.offB[0]; o[3] = st.offB[1];
    v[0] = st.velA[0]; v[1] = st.velA[1]; v[2] = st.velB[0]; v[3] = st.velB[1];
    m[0] = st.lull; m[1] = st.heading; m[2] = st.cloudOff[0]; m[3] = st.cloudOff[1];
  }
  const ht = st.t * WIND.headingDrift;
  if (u.uWHeadT && typeof u.uWHeadT === 'object' && 'value' in u.uWHeadT) u.uWHeadT.value = ht;
  else u.uWHeadT = ht;
}

/** Names of the wind uniforms, for gl.getUniformLocation in raw GL. */
export const WIND_UNIFORM_NAMES = ['uWindNoise', 'uWOff', 'uWVel', 'uWMisc', 'uWHeadT'];
