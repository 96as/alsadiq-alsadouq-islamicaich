// Shaders for MeadowLife, the living layer over the lead's painted meadow (Motion Bible 7.8). Raw WebGL2.
//
// Three passes in one canvas:
//   1. BASE      the painting, drawn through a masked warp, with the gust colour wave, cloud shadows, cloud
//                wisps in the sky, light shafts and the contact shadow under the avatar's feet.
//   2. BLADES    instanced painted blades in the foreground, coloured from the painting itself, bent by the
//                same wind (rotation about the base, tip lag, flutter).
//   3. PARTICLES a handful of pollen motes and dandelion seeds.
//
// All of it reads the one wind field (windGlsl.js), mapped from the screen with the same function the foreground
// strip uses on the CPU (windField.screenToWorld), so a gust crosses the painting and the strip together.

import { WIND_GLSL } from '../forest/wind/windGlsl';
import { WIND } from '../forest/wind/windField';

const HORIZON_V = 0.455;

const COMMON = /* glsl */ `#version 300 es
precision highp float;
precision highp int;
precision highp sampler2D;

uniform vec4 uRect;      // the painting's rectangle on screen: left, top, width, height (css px)
uniform vec2 uSize;      // canvas size in css px
uniform float uDpr;
uniform float uHorizon;  // screen y (css px) of the painting's horizon row
uniform float uTime;     // seconds
uniform vec4 uMotion;    // wind scale (1, or 0.25 reduced), flutter (1 or 0), warp scale, breathing and particles (1 or 0)

${WIND_GLSL}

const float TAU = 6.28318530718;

// The same mapping as screenToWorld() in windField.js, from a screen position in css px.
vec2 screenWorld(vec2 p) {
  float u = p.x / uSize.x;
  float d = clamp((p.y - uHorizon) / max(1.0, uSize.y - uHorizon), 0.0, 1.0);
  d = max(0.02, d);
  float spread = 24.0 / (0.3 + 0.7 * d);
  return vec2((u - 0.5) * spread, 6.0 - 30.0 * (1.0 - d) * (1.0 - d));
}

float depth01(vec2 p) {
  return clamp((p.y - uHorizon) / max(1.0, uSize.y - uHorizon), 0.0, 1.0);
}

// Cloud shadow, 1 = lit. Screen space, drifting about 2% of the width per second.
float cloudLit(vec2 p) {
  float d = depth01(p);
  float su = p.x / uSize.x;
  float persp = 1.0 / (0.22 + d);
  vec2 q = vec2(su * 0.9 - uTime * 0.02, persp * 0.27 + su * 0.12 + uTime * 0.004);
  float n = texture(uWindNoise, q).r * 0.65 + texture(uWindNoise, q * 2.1 + vec2(0.37, 0.11)).r * 0.35;
  return smoothstep(0.36, 0.60, n);
}

vec3 cloudTint(vec2 p, float amount) {
  float lit = cloudLit(p);
  float d = depth01(p);
  float k = amount * (0.3 + 0.7 * smoothstep(0.0, 0.3, d));
  return mix(vec3(1.0), mix(vec3(0.83, 0.88, 0.98), vec3(1.0), lit), k);
}
`;

export const VERT_FULL = /* glsl */ `#version 300 es
void main() {
  vec2 v = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));
  gl_Position = vec4(v * 2.0 - 1.0, 0.0, 1.0);
}
`;

export const FRAG_BASE = `${COMMON}
uniform sampler2D uImg;
uniform sampler2D uMask;   // R grass, G trees, B path, A sky
uniform vec4 uShadow;      // contact shadow ellipse: centre x, centre y, radius x, radius y (css px); 0 radius = off
uniform float uSharp;
uniform float uDebug;      // 1 = write the gust strength as grey (used by the sync test)
out vec4 outColor;

float hash11(float n) { return fract(sin(n * 91.3458) * 47453.5453); }

void main() {
  vec2 p = vec2(gl_FragCoord.x, uSize.y * uDpr - gl_FragCoord.y) / uDpr;
  vec2 uv = (p - uRect.xy) / uRect.zw;
  float sc = uRect.z / 1100.0;
  float depth = depth01(p);
  vec2 wp = screenWorld(p);
  float g0 = windGust(wp, 0.0);

  if (uDebug > 0.5) {
    outColor = vec4(vec3(g0), 1.0);
    return;
  }

  vec4 mk = texture(uMask, uv);
  float gl = windGust(wp, 0.12);

  // ---- masked warp (css px). Grass 0.5 px at the horizon rising to 3.5 px at the bottom, trees 1.5 px.
  float below = (p.y - uHorizon);
  float ramp = clamp((below - 10.0 * sc) / (22.0 * sc), 0.0, 1.0);
  ramp = ramp * ramp * (3.0 - 2.0 * ramp);
  float ampG = mix(0.5, 3.4, pow(depth, 1.15)) * sc * uMotion.z;
  float nz = texture(uWindNoise, uv * vec2(2.0, 3.0) + vec2(0.13, 0.57)).r;
  float clump = sin(TAU * (0.7 * uTime + 3.0 * uv.x + 1.7 * uv.y) + 2.5 * nz);
  float flutter = sin(TAU * 4.3 * uTime + 38.0 * uv.x + 21.0 * uv.y);
  // bounded: sway in -0.2..0.88 plus flutter 0.12, so the displacement never exceeds ampG (3.5 px x sc at the bottom)
  float sway = clamp(gl * 0.95 + 0.28 * clump * (0.35 + gl), -0.2, 0.88) + 0.12 * uMotion.y * flutter;
  vec2 dir = vec2(0.96, 0.27);
  vec2 disp = dir * (ampG * ramp * mk.r * sway);

  float crown = clamp((${HORIZON_V.toFixed(3)} - uv.y) / 0.25, 0.0, 1.0);
  float tsway = gl * 0.6 + 0.4 * sin(TAU * 0.33 * uTime + 9.0 * uv.x);
  float tflut = 0.3 * uMotion.y * sin(TAU * 6.5 * uTime + 80.0 * uv.x + 55.0 * uv.y);
  disp.x += 1.5 * sc * uMotion.z * mk.g * crown * (tsway + tflut);
  disp.y += 0.35 * sc * uMotion.z * mk.g * crown * sin(TAU * 0.27 * uTime + 7.0 * uv.x);

  vec2 uvw = uv + disp / uRect.zw;
  vec3 col = texture(uImg, uvw).rgb;
  if (uSharp > 0.0) {
    vec2 px = 0.6 / (uRect.zw);
    vec3 b = 0.25 * (texture(uImg, uvw + vec2(px.x, 0.0)).rgb + texture(uImg, uvw - vec2(px.x, 0.0)).rgb
                    + texture(uImg, uvw + vec2(0.0, px.y)).rgb + texture(uImg, uvw - vec2(0.0, px.y)).rgb);
    col += (col - b) * uSharp;
  }

  // ---- gust colour wave on the grass: the bright wave rolls across with the front
  float W = uMotion.x;
  // plus the silver ripple: fine light and dark combs that ride the front (the grass turning its pale side up)
  float rip = texture(uWindNoise, (wp - uWOff.xy) * 0.24 + vec2(0.7, 0.2)).r
            + 0.5 * (texture(uWindNoise, (wp - uWOff.xy) * 0.61 + vec2(0.2, 0.9)).r - 0.5);
  // aerial perspective: the ripple keeps 65% of its contrast at the horizon, so the far field is calmer than the near
  float wave = 0.34 * (g0 - 0.35) + 0.48 * (rip - 0.5) * (0.35 + g0) * mix(0.65, 1.0, smoothstep(0.0, 0.35, depth));
  col *= 1.0 + mk.r * W * wave;
  col += vec3(0.022, 0.034, -0.004) * mk.r * W * max(g0 - 0.40, 0.0) * (0.6 + rip);

  // ---- cloud shadows on the grass and the path
  float shadeMask = max(mk.r, mk.b);
  col *= cloudTint(p, shadeMask);

  // ---- cloud wisps in the sky: additive white, 12-20%, drifting 1-3 px/s
  float wx = 1.3 * (uv.x - 2.0 * uTime / uRect.z);
  float w1 = texture(uWindNoise, vec2(wx, uv.y * 4.0)).r;
  float w2 = texture(uWindNoise, vec2(2.9 * (uv.x - 2.7 * uTime / uRect.z) + 0.21, uv.y * 9.0 + 0.4)).r;
  float wisp = smoothstep(0.50, 0.80, w1 * 0.6 + w2 * 0.4);
  float wa = 0.17 * wisp * mk.a * smoothstep(0.0, 0.12, uv.y);
  col = 1.0 - (1.0 - col) * (1.0 - wa * vec3(1.0, 0.97, 0.95));

  // ---- light shafts from the bright cloud: 3 soft wedges, opacity <= 0.08, breathing at 0.12 Hz
  vec2 dv = uv - vec2(0.50, -0.10);
  dv.x *= uRect.z / uRect.w;
  float ang = atan(dv.x, dv.y);
  float len = length(dv);
  float shaft = 0.0;
  for (int i = 0; i < 3; i++) {
    float fi = float(i);
    float a0 = -0.62 + fi * 0.40 + 0.18 * sin(uTime * 0.05 * (1.0 + 0.4 * fi) + fi * 2.0);
    float wdt = 0.07 + 0.03 * fi;
    float da = (ang - a0) / wdt;
    float breathe = 0.65 + 0.35 * uMotion.w * sin(TAU * 0.12 * uTime + fi * 2.1);
    shaft += exp(-da * da) * breathe;
  }
  float shaftFade = smoothstep(0.05, 0.35, len) * (1.0 - smoothstep(0.9, 1.5, len));
  col += vec3(1.0, 0.93, 0.78) * (0.075 * shaft * shaftFade);

  // ---- contact shadow under the avatar's feet (the CSS shadow of MeadowImage, drawn here)
  if (uShadow.z > 0.0) {
    vec2 e = (p - uShadow.xy) / uShadow.zw;
    float r = length(e);
    float a = r < 0.55 ? mix(0.5, 0.22, r / 0.55) : mix(0.22, 0.0, clamp((r - 0.55) / 0.45, 0.0, 1.0));
    col = mix(col, vec3(0.094, 0.133, 0.039), a * step(r, 1.0));
  }

  outColor = vec4(col, 1.0);
}
`;

export const BLADE_SEGMENTS = 6;

export const VERT_BLADE = `${COMMON}
uniform sampler2D uImg;
uniform sampler2D uMask;
layout(location = 0) in vec4 aInst;   // x, y, size, tilt (random 0..1)
out vec3 vCol;
out vec2 vEdge;   // x: -1..1 across the blade, y: 0..1 up the blade

const int NSEG = ${BLADE_SEGMENTS};

// Wind bend of a blade at height h (0 base, 1 tip), degrees: the gust with tip lag, the clump sway, the flutter.
float bendDeg(float h, vec2 wp, float stiff, float swayHz, float swayPh, float fHz, float fPh) {
  float s = windGust(wp, ${WIND.tipLag.toFixed(2)} * h * h);
  float hh = h * h;
  float fl = smoothstep(${WIND.flutterFrom.toFixed(2)}, 1.0, h);
  return ${WIND.tipDeg.toFixed(1)} * 0.85 * s * hh / stiff
       + ${WIND.swayDeg.toFixed(1)} * (0.4 + 0.6 * s) * hh * sin(TAU * swayHz * uTime + swayPh)
       + ${WIND.flutterDeg.toFixed(1)} * uMotion.y * (0.3 + 0.7 * s) * fl * sin(TAU * fHz * uTime + fPh);
}

void main() {
  int vid = gl_VertexID;
  bool tip = vid >= 2 * NSEG;
  int level = tip ? NSEG : vid / 2;
  float side = tip ? 0.0 : float((vid & 1) * 2 - 1);
  float sc = uRect.z / 1100.0;

  float yTop = max(uHorizon + 12.0 * sc, 0.0);
  float yy = mix(yTop, uSize.y * 1.01, pow(aInst.y, 0.8));
  vec2 base = vec2(aInst.x * uSize.x, yy);
  float d = depth01(base);
  vec2 uvb = (base - uRect.xy) / uRect.zw;
  float gm = textureLod(uMask, uvb, 0.0).r;
  float vis = step(0.62, gm) * step(0.0, uvb.x) * step(uvb.x, 1.0);

  float H = sc * (5.0 + 84.0 * pow(d, 1.3)) * (0.70 + 0.60 * aInst.z);
  float Wd = max(0.8 * sc, H * 0.075) * (0.8 + 0.5 * aInst.w);
  float h = float(level) / float(NSEG);

  vec2 wp = screenWorld(base);
  int ix = int(floor(wp.x * 97.3));
  int iz = int(floor(wp.y * 97.3));
  int cx = int(floor(wp.x / ${WIND.clumpSize.toFixed(2)}));
  int cz = int(floor(wp.y / ${WIND.clumpSize.toFixed(2)}));
  float stiff = 0.8 + 0.4 * windHash(ix, iz, 1);
  float swayHz = ${WIND.swayHzLo.toFixed(2)} + ${(WIND.swayHzHi - WIND.swayHzLo).toFixed(2)} * windHash(cx, cz, 3);
  float swayPh = TAU * windHash(cx, cz, 4);
  float fHz = ${WIND.flutterHzLo.toFixed(2)} + ${(WIND.flutterHzHi - WIND.flutterHzLo).toFixed(2)} * windHash(ix, iz, 5);
  float fPh = TAU * windHash(ix, iz, 6);

  float rest = radians(mix(-12.0, 16.0, aInst.w));
  float arch = radians(mix(-6.0, 16.0, fract(aInst.z * 7.31)));
  float W = uMotion.x;

  // integrate the blade: rigid segments, each turned by the wind at its height (a rotation, never a stretch)
  vec2 pos = base;
  vec2 dir = vec2(sin(rest), -cos(rest));
  for (int k = 0; k < NSEG; k++) {
    if (k >= level) break;
    float hm = (float(k) + 0.5) / float(NSEG);
    float phi = rest + arch * hm * hm + radians(bendDeg(hm, wp, stiff, swayHz, swayPh, fHz, fPh) * W);
    dir = vec2(sin(phi), -cos(phi));
    pos += (H / float(NSEG)) * dir;
  }
  if (level == 0) {
    float phi0 = rest + radians(bendDeg(0.5 / float(NSEG), wp, stiff, swayHz, swayPh, fHz, fPh) * W);
    dir = vec2(sin(phi0), -cos(phi0));
  }
  vec2 perp = vec2(-dir.y, dir.x) * -1.0;   // across the blade, in screen space
  perp = vec2(dir.y * -1.0, dir.x) * -1.0;
  float prof = tip ? 0.0 : pow(1.0 - h, 0.72) * 0.92 + 0.08 * (1.0 - h);
  vec2 q = pos + perp * side * Wd * prof * 0.5;

  // colour from the painting around the blade, lighter and warmer toward the tip
  vec2 mid = base + vec2(0.0, -H * 0.30);
  vec3 c = textureLod(uImg, (mid - uRect.xy) / uRect.zw, 2.0).rgb;
  float tone = 0.9 + 0.2 * fract(aInst.z * 3.7);
  vec3 cb = c * 0.78 * tone;
  vec3 ct = c * 1.22 * tone + vec3(0.03, 0.05, -0.01);
  vec3 col = mix(cb, ct, smoothstep(0.1, 1.0, h));
  float g0 = windGust(wp, 0.0);
  col *= 1.0 + 0.10 * W * (g0 - 0.35);
  col *= cloudTint(base, 1.0);

  vCol = col;
  vEdge = vec2(side, h);
  float fade = smoothstep(0.0, 0.06, d);
  if (vis * fade < 0.5) q = vec2(-9999.0);
  gl_Position = vec4(q.x / uSize.x * 2.0 - 1.0, 1.0 - q.y / uSize.y * 2.0, 0.0, 1.0);
}
`;

export const FRAG_BLADE = /* glsl */ `#version 300 es
precision highp float;
in vec3 vCol;
in vec2 vEdge;
out vec4 outColor;
void main() {
  // the base is invisible, so the blade grows out of the painted grass; the edge is soft
  float grow = smoothstep(0.04, 0.42, vEdge.y);
  float edge = smoothstep(1.0, 0.35, abs(vEdge.x));
  outColor = vec4(vCol, grow * edge * 0.80);
}
`;

export const VERT_PART = `${COMMON}
layout(location = 0) in vec4 aSeed;   // random 0..1 x4
out float vA;
out float vKind;

float h11(float n) { return fract(sin(n * 127.1) * 43758.5453); }

void main() {
  float period = 11.0 + 7.0 * aSeed.z;
  float t = uTime / period + aSeed.w;
  float life = fract(t);
  float idx = floor(t);
  float r1 = h11(aSeed.x * 91.0 + idx * 7.13);
  float r2 = h11(aSeed.y * 57.0 + idx * 3.77);
  vec2 start = vec2(r1, mix(0.10, 0.92, r2));
  // drifts downwind (screen right, a little down) and bobs; faster when the gust at its start was strong
  float s = windGust(screenWorld(vec2(start.x * uSize.x, mix(uHorizon, uSize.y, start.y))), 0.0);
  float travel = life * period * (0.012 + 0.045 * s);
  vec2 sp = vec2(start.x + travel * 0.97 + 0.012 * sin(life * 14.0 + aSeed.x * 20.0),
                 start.y + travel * 0.25 - 0.020 * sin(life * 6.0 + aSeed.y * 10.0) - 0.04 * life);
  float yTop = max(uHorizon, 0.0);
  vec2 p = vec2(sp.x * uSize.x, mix(yTop, uSize.y, sp.y));
  float d = depth01(p);
  float sc = uRect.z / 1100.0;
  float kind = step(0.72, aSeed.x);
  vKind = kind;
  float tw = 0.65 + 0.35 * sin(uTime * (2.0 + 3.0 * aSeed.y) + aSeed.w * 30.0);
  vA = sin(3.14159 * life) * tw * uMotion.w * (0.6 + 0.4 * smoothstep(0.0, 0.4, d));
  gl_PointSize = max(2.0, (2.6 + 4.0 * d + kind * 4.0) * sc * uDpr);
  gl_Position = vec4(p.x / uSize.x * 2.0 - 1.0, 1.0 - p.y / uSize.y * 2.0, 0.0, 1.0);
}
`;

export const FRAG_PART = /* glsl */ `#version 300 es
precision highp float;
in float vA;
in float vKind;
out vec4 outColor;
void main() {
  vec2 c = gl_PointCoord * 2.0 - 1.0;
  float r = length(c);
  float glow = exp(-r * r * 3.2);
  float a = glow;
  if (vKind > 0.5) {
    // dandelion seed: a bright core and thin radial wisps
    float ang = atan(c.y, c.x);
    float rays = pow(abs(cos(ang * 4.0)), 18.0) * smoothstep(1.0, 0.1, r) * 0.55;
    a = max(glow * 0.8, rays);
  }
  outColor = vec4(vec3(1.0, 0.97, 0.86), a * vA * 0.85);
}
`;
