// The grass, flower and tree vertex shaders on the shared wind field (Motion Bible 7.2-7.5).
// Every blade bends by a ROTATION about its own base (never a lateral push), so its length cannot change (gate N2).
// The gust, heading and cloud come from WIND_GLSL, the twin of windField.js, so the forest, the painted meadow
// and the foreground strip move with one wind.

import { WIND } from './wind/windField';
import { WIND_GLSL } from './wind/windGlsl';

const f = (v) => (Number.isInteger(v) ? `${v}.0` : String(Number(v.toPrecision(9))));

/** Shared by the vegetation and tree vertex shaders. */
export const BEND_GLSL = /* glsl */ `
${WIND_GLSL}
#define TAU 6.28318531
#define DEG 0.01745329

uniform float uTime;
uniform float uSway;       // 1, or 0.25 with reduced motion
uniform float uFlutterOn;  // 0 with reduced motion
uniform float uWindGain;   // dev: wind strength
uniform vec3 uWindMix;     // dev: gust, sway, flutter on/off

// Rotate rel about the base around axis cross(up, w) by theta (w = the wind direction on the ground plane).
vec3 bendAbout(vec3 rel, float theta, vec2 w) {
  vec3 a = vec3(w.y, 0.0, -w.x);
  float c = cos(theta);
  float s = sin(theta);
  return rel * c + cross(a, rel) * s + a * dot(a, rel) * (1.0 - c);
}
`;

const FEET_GLSL = /* glsl */ `
uniform vec4 uFeet[8];   // x, z, weight (1 = fresh print), unused
uniform vec2 uFeetC;     // newest print, for the early out
uniform float uFeetR;
uniform float uFeetLean; // radians at the centre
vec3 footPush(vec3 rel, vec3 pivot, float h) {
  if (dot(pivot.xz - uFeetC, pivot.xz - uFeetC) > 16.0) return rel;
  float k = 0.0;
  vec2 away = vec2(0.0);
  for (int i = 0; i < 8; i++) {
    vec4 fp = uFeet[i];
    vec2 d = pivot.xz - fp.xy;
    float r = length(d);
    float w = (1.0 - smoothstep(0.0, uFeetR, r)) * fp.z;
    if (w > k) { k = w; away = d / max(r, 0.001); }
  }
  if (k < 0.002) return rel;
  return bendAbout(rel, k * uFeetLean * (0.35 + 0.65 * h), away);
}
`;

export const GRASS_VERT = /* glsl */ `
  attribute float aH;
  attribute vec3 aTint;
  attribute vec3 aBase;   // this blade's root, in tuft space
  attribute vec3 aSide;   // half the blade width at this vertex, in tuft space (for the distance widening)
  uniform vec3 uRoot;
  uniform vec3 uTip;
  uniform vec3 uFar;
  varying vec3 vCol;
  ${BEND_GLSL}
  ${FEET_GLSL}
  #include <common>
  #include <fog_pars_vertex>
  void main() {
    mat4 m = modelMatrix * instanceMatrix;
    vec3 pw = (m * vec4(position, 1.0)).xyz;
    vec3 pivot = (m * vec4(aBase, 1.0)).xyz;
    float dist = distance(pivot, cameraPosition);
    float h = aH;
    float h2 = h * h;
    // far blades widen so the carpet still covers the ground
    float widen = smoothstep(14.0, 55.0, dist) * 1.7;
    vec3 rel = pw - pivot + (m * vec4(aSide, 0.0)).xyz * widen;

    int bx = int(floor(pivot.x * 97.3));
    int bz = int(floor(pivot.z * 97.3));
    int cx = int(floor(pivot.x / ${f(WIND.clumpSize)}));
    int cz = int(floor(pivot.z / ${f(WIND.clumpSize)}));
    float stiff = 0.8 + 0.4 * windHash(bx, bz, 1);
    float swayHz = ${f(WIND.swayHzLo)} + ${f(WIND.swayHzHi - WIND.swayHzLo)} * windHash(cx, cz, 3);
    float swayPh = TAU * windHash(cx, cz, 4);
    float flHz = ${f(WIND.flutterHzLo)} + ${f(WIND.flutterHzHi - WIND.flutterHzLo)} * windHash(bx, bz, 5);
    float flPh = TAU * windHash(bx, bz, 6);

    float s = windGust(pivot.xz, ${f(WIND.tipLag)} * h2) * uWindGain;
    float heading = windHeading(pivot.xz);
    vec2 w = vec2(cos(heading), sin(heading));
    float gust = ${f(WIND.tipDeg)} * s * h2 / stiff * uWindMix.x;
    float sway = ${f(WIND.swayDeg)} * (0.4 + 0.6 * s) * h2 * sin(TAU * swayHz * uTime + swayPh) * uWindMix.y;
    float fh = clamp((h - ${f(WIND.flutterFrom)}) / ${f(1 - WIND.flutterFrom)}, 0.0, 1.0);
    float fs = fh * fh * (3.0 - 2.0 * fh);
    float fade = 1.0 - smoothstep(${f(WIND.flutterFadeNear)}, ${f(WIND.flutterFadeFar)}, dist);
    float flutter = ${f(WIND.flutterDeg)} * (0.3 + 0.7 * s) * fs * fade * uFlutterOn * sin(TAU * flHz * uTime + flPh) * uWindMix.z;
    float theta = (gust + sway + flutter) * DEG * uSway;
    rel = bendAbout(rel, theta, w);
    rel = footPush(rel, pivot, h);

    vec4 mvPosition = viewMatrix * vec4(pivot + rel, 1.0);
    gl_Position = projectionMatrix * mvPosition;

    // colour: dark rooted base (ambient occlusion), a light wave riding the gust, bright translucent tips,
    // cloud shadow, and the lime of the painted horizon in the distance
    float far = smoothstep(4.0, 26.0, dist);
    vec3 stem = mix(uRoot, uTip, h);
    float ao = mix(0.5, 1.0, smoothstep(0.0, 0.5, h));
    float wave = 1.0 + 0.30 * (s - 0.35) * (0.3 + h);
    vec3 col = stem * aTint * ao * wave;
    col += uTip * 0.16 * h2 * (0.4 + s);
    float cl = windCloud(pivot.xz);
    col *= cl;
    vCol = mix(col, uFar * (0.78 + 0.3 * h) * cl, far * 0.8);
    #include <fog_vertex>
  }
`;

export const FLOWER_VERT = /* glsl */ `
  attribute float aH;
  attribute vec3 aTint;
  attribute float aHead;
  attribute vec2 aUv;
  attribute vec2 aLean;   // x: head lean in radians along the wind (a CPU spring), y: 1 when x is valid
  uniform vec3 uRoot;
  uniform vec3 uTip;
  uniform vec3 uFar;
  varying vec3 vCol;
  varying vec2 vUv;
  varying float vHead;
  varying float vSpin;
  varying vec3 vTint;
  ${BEND_GLSL}
  #include <common>
  #include <fog_pars_vertex>
  void main() {
    mat4 m = modelMatrix * instanceMatrix;
    vec3 pivot = (m * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
    vec3 rel = (m * vec4(position, 1.0)).xyz - pivot;
    float dist = distance(pivot, cameraPosition);
    float ph = fract(pivot.x * 7.31 + pivot.z * 3.17) * TAU;
    float s = windGust(pivot.xz, 0.12) * uWindGain;
    float heading = windHeading(pivot.xz);
    vec2 w = vec2(cos(heading), sin(heading));
    // the far flowers approximate the spring: a lean toward the target; the near ring uses the real spring
    float target = (28.0 * s + 4.0 * sin(TAU * 0.6 * uTime + ph)) * DEG * uWindMix.x;
    float lean = mix(target, aLean.x, aLean.y) * uSway;
    float h = clamp(aH, 0.0, 1.0);
    float theta = lean * pow(h, 1.35) + 0.05 * sin(TAU * 3.2 * uTime + ph) * s * h * h * uFlutterOn * uWindMix.z;
    rel = bendAbout(rel, theta, w);
    vec4 mvPosition = viewMatrix * vec4(pivot + rel, 1.0);
    gl_Position = projectionMatrix * mvPosition;
    float far = smoothstep(4.0, 26.0, dist);
    vec3 stem = mix(uRoot, uTip, h);
    float cl = windCloud(pivot.xz);
    vCol = mix(stem * cl, uFar * cl, far * 0.6);
    vUv = aUv;
    vHead = aHead;
    vSpin = ph;
    vTint = aTint * mix(1.0, cl, 0.9);
    #include <fog_vertex>
  }
`;

/** Tree and bush sway: a main crown bend plus a second tier of branch motion and leaf flutter. */
export const TREE_BEND_GLSL = /* glsl */ `
  attribute float aSway;  // 0 at the foot, 1 at the top of the crown (eased); small for bushes
  attribute float aLeaf;  // 1 on leaves, 0 on trunk
  vec3 treeSway(vec3 wp, mat4 m) {
    vec3 ip = (m * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
    float sc = length(m[1].xyz);
    float hh = windHash(int(floor(ip.x * 31.7)), int(floor(ip.z * 31.7)), 11);
    float hz = 0.25 + 0.15 * hh;
    float s = windGust(ip.xz, 0.0) * uWindGain;
    float heading = windHeading(ip.xz);
    vec2 w = vec2(cos(heading), sin(heading));
    float slow = sin(TAU * hz * uTime + hh * TAU + s * 2.2);
    float deg = (0.6 + 1.2 * s) * (0.6 + 0.4 * slow) * uWindMix.x;
    // second tier: each crown clump moves a little on its own, a little faster, riding the gust
    float ph2 = windHash(int(floor(wp.x * 3.0)), int(floor(wp.z * 3.0)), 12) * TAU;
    float branch = (0.5 + 0.8 * s) * sin(TAU * (0.7 + 0.5 * hh) * uTime + ph2 + s * 3.0) * aLeaf * uWindMix.y;
    vec3 rel = wp - ip;
    rel = bendAbout(rel, (deg + branch) * DEG * aSway * uSway * 1.4, w);
    // leaf flutter: tiny, fast, fading with distance
    float fade = 1.0 - smoothstep(10.0, 22.0, distance(ip, cameraPosition));
    vec3 jig = vec3(sin(TAU * 3.7 * uTime + ph2), sin(TAU * 4.3 * uTime + ph2 * 1.7) * 0.6, sin(TAU * 3.1 * uTime + ph2 * 2.3));
    rel += jig * 0.014 * sc * aLeaf * (0.3 + 0.7 * s) * fade * uFlutterOn * uWindMix.z * aSway;
    return ip + rel;
  }
`;
