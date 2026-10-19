import * as THREE from 'three';
import { WIND } from './wind/windField';
import { WIND_GLSL } from './wind/windGlsl';
import { windNoiseThree } from './wind/windTexture';
import { FLOWER_VERT, GRASS_VERT, TREE_BEND_GLSL, BEND_GLSL } from './vegetationShaders';

/**
 * Uniforms shared by every custom material in the scene. Materials get the
 * SAME uniform objects, so one write per frame updates the whole forest.
 */
export function createSharedUniforms() {
  return {
    uTime: { value: 0 },
    uSway: { value: 1 },
    uGrass: { value: new THREE.Color('#ffffff') },
    uNight: { value: 0 },
    uDpr: { value: 1 },
    // the one wind (windField.js / windGlsl.js), written every frame by SceneClock
    uWindNoise: { value: windNoiseThree(THREE) },
    uWOff: { value: new THREE.Vector4() },
    uWVel: { value: new THREE.Vector4() },
    uWMisc: { value: new THREE.Vector4(1, WIND.baseHeading, 0, 0) },
    uWHeadT: { value: 0 },
    uWindGain: { value: 1 },
    uWindMix: { value: new THREE.Vector3(1, 1, 1) }, // dev: gust, sway, flutter on or off
    uFlutterOn: { value: 1 },
    // the avatar's last footprints (x, z, weight, 0): the grass leans away from them
    uFeet: { value: Array.from({ length: 8 }, () => new THREE.Vector4(1e4, 1e4, 0, 0)) },
    uFeetC: { value: new THREE.Vector2(1e4, 1e4) },
    uFeetR: { value: WIND.feetRadius },
    uFeetLean: { value: (WIND.feetLeanDeg * Math.PI) / 180 },
  };
}

const WIND_KEYS = ['uTime', 'uSway', 'uWindNoise', 'uWOff', 'uWVel', 'uWMisc', 'uWHeadT', 'uWindGain', 'uWindMix', 'uFlutterOn'];
/** The wind uniforms every material that moves with the wind needs, as references into the shared bag. */
function windUniforms(shared, extra = []) {
  const o = {};
  [...WIND_KEYS, ...extra].forEach((k) => {
    o[k] = shared[k];
  });
  return o;
}

function withFog(extra) {
  return { ...THREE.UniformsUtils.clone(THREE.UniformsLib.fog), ...extra };
}

/* ---------- grass tufts and flowers (instanced, bent by the wind field) ---------- */

const VEG_FRAG = /* glsl */ `
  uniform vec3 uGrass;
  uniform float uKind;
  uniform float uCut;
  varying vec3 vCol;
  #ifdef FLOWER
    varying vec2 vUv;
    varying float vHead;
    varying float vSpin;
    varying vec3 vTint;
  #endif
  #include <common>
  #include <fog_pars_fragment>
  void main() {
    vec3 col = vCol;
    float alpha = 1.0;
    #ifdef FLOWER
      if (vHead > 0.5) {
        float r = length(vUv);
        float a = atan(vUv.y, vUv.x) + vSpin;
        float edge;
        if (uKind < 0.5) {
          // dandelion: a round pompom with a soft ragged rim, warmer in the middle
          edge = 0.8 + 0.1 * abs(sin(a * 8.0)) + 0.05 * sin(a * 19.0);
          float k = r / edge;
          col = mix(vTint * vec3(1.0, 0.7, 0.3), vTint * 1.06, smoothstep(0.05, 0.8, k));
          col *= 0.92 + 0.08 * sin(a * 26.0) * smoothstep(0.3, 0.9, k);
        } else {
          // five round petals around a yellow eye
          edge = 0.48 + 0.5 * pow(abs(cos(a * 2.5)), 0.7);
          col = vTint * (0.84 + 0.2 * smoothstep(0.2, 1.0, r));
          col = mix(vec3(1.0, 0.76, 0.2), col, smoothstep(0.2, 0.3, r));
        }
        float aa = max(fwidth(r), 0.001);
        alpha = 1.0 - smoothstep(edge - aa, edge + aa, r);
      }
    #endif
    if (alpha < uCut) discard;
    gl_FragColor = vec4(col * uGrass, alpha);
    #include <colorspace_fragment>
    #include <fog_fragment>
  }
`;

/**
 * Grass tufts, or flowers (kind 0 dandelion, 1 bloom). `smoothEdges` uses
 * alpha to coverage for soft flower rims; it only helps when MSAA is on.
 */
export function createVegetationMaterial(shared, { flower = false, kind = 0, smoothEdges = false } = {}) {
  return new THREE.ShaderMaterial({
    vertexShader: flower ? FLOWER_VERT : GRASS_VERT,
    fragmentShader: VEG_FRAG,
    defines: flower ? { FLOWER: '' } : {},
    fog: true,
    side: THREE.DoubleSide,
    alphaToCoverage: flower && smoothEdges,
    uniforms: withFog({
      ...windUniforms(shared, flower ? [] : ['uFeet', 'uFeetC', 'uFeetR', 'uFeetLean']),
      uGrass: shared.uGrass,
      uRoot: { value: new THREE.Color(flower ? '#2c6a2a' : '#1f5a26') },
      uTip: { value: new THREE.Color(flower ? '#6aa63a' : '#9ccb42') },
      uFar: { value: new THREE.Color('#c2d64c') },
      uKind: { value: kind },
      uCut: { value: flower && smoothEdges ? 0.02 : 0.5 },
    }),
  });
}

/* ---------- trees, pines and bushes (instanced, painterly light) ---------- */

const TREE_VERT = /* glsl */ `
  varying vec3 vCol;
  varying vec3 vN;
  varying vec3 vW;
  varying float vCl;
  ${BEND_GLSL}
  ${TREE_BEND_GLSL}
  #include <common>
  #include <fog_pars_vertex>
  void main() {
    vec3 col = color;
    #ifdef USE_INSTANCING_COLOR
      col *= instanceColor;
    #endif
    vCol = col;
    #ifdef USE_INSTANCING
      mat4 m = modelMatrix * instanceMatrix;
    #else
      mat4 m = modelMatrix;
    #endif
    vec4 wp = m * vec4(position, 1.0);
    wp.xyz = treeSway(wp.xyz, m);
    vW = wp.xyz;
    vN = normalize(mat3(m) * normal);
    vCl = windCloud((m * vec4(0.0, 0.0, 0.0, 1.0)).xz);
    vec4 mvPosition = viewMatrix * wp;
    gl_Position = projectionMatrix * mvPosition;
    #include <fog_vertex>
  }
`;

const TREE_FRAG = /* glsl */ `
  uniform vec3 uGrass;
  uniform vec3 uSunDir;
  uniform vec3 uShade;
  uniform vec3 uLight;
  uniform float uTime;
  uniform float uWindGain;
  varying vec3 vCol;
  varying vec3 vN;
  varying vec3 vW;
  varying float vCl;
  #include <common>
  #include <fog_pars_fragment>
  float h3(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
  float n3(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(mix(h3(i), h3(i + vec3(1.0, 0.0, 0.0)), f.x), mix(h3(i + vec3(0.0, 1.0, 0.0)), h3(i + vec3(1.0, 1.0, 0.0)), f.x), f.y),
      mix(mix(h3(i + vec3(0.0, 0.0, 1.0)), h3(i + vec3(1.0, 0.0, 1.0)), f.x), mix(h3(i + vec3(0.0, 1.0, 1.0)), h3(i + vec3(1.0, 1.0, 1.0)), f.x), f.y),
      f.z);
  }
  void main() {
    vec3 n = normalize(vN);
    // soft wrapped light, broken into painted leaf clumps by a little noise
    float wrap = dot(n, uSunDir) * 0.5 + 0.5;
    // the painted leaf clumps crawl slowly, so the light moves through the crown like wind through leaves
    vec3 crawl = vec3(uTime * 0.11, uTime * 0.03, uTime * 0.07) * (0.5 + 0.5 * uWindGain);
    float clump = n3(vW * 2.1 + crawl) * 0.7 + n3(vW * 4.7 - crawl * 1.7) * 0.3;
    float lit = smoothstep(0.28, 0.86, wrap + (clump - 0.5) * 0.5);
    vec3 col = vCol * mix(uShade, uLight, lit);
    col += vCol * 0.12 * max(n.y, 0.0);
    col *= vCl;
    gl_FragColor = vec4(col * uGrass, 1.0);
    #include <colorspace_fragment>
    #include <fog_fragment>
  }
`;

/**
 * Painterly light for the trees: cool blue-green shadows, warm sunny tops, and
 * the same time-of-day tint as the grass. Uses vertex and instance colours.
 */
export function createTreeMaterial(shared) {
  return new THREE.ShaderMaterial({
    vertexShader: TREE_VERT,
    fragmentShader: TREE_FRAG,
    vertexColors: true,
    fog: true,
    uniforms: withFog({
      ...windUniforms(shared),
      uGrass: shared.uGrass,
      uSunDir: { value: new THREE.Vector3(0.45, 0.85, 0.3).normalize() },
      uShade: { value: new THREE.Vector3(0.5, 0.63, 0.74) },
      uLight: { value: new THREE.Vector3(1.22, 1.2, 0.94) },
    }),
  });
}

/* ---------- ground with a winding dirt path ---------- */

const GROUND_VERT = /* glsl */ `
  varying vec3 vW;
  #include <common>
  #include <fog_pars_vertex>
  void main() {
    vec4 wp = modelMatrix * vec4(position, 1.0);
    vW = wp.xyz;
    vec4 mvPosition = viewMatrix * wp;
    gl_Position = projectionMatrix * mvPosition;
    #include <fog_vertex>
  }
`;

const GROUND_FRAG = /* glsl */ `
  uniform vec3 uGrass;
  uniform vec3 uGDark;
  uniform vec3 uGLight;
  uniform vec3 uGFar;
  uniform vec3 uDirt;
  uniform vec3 uDirtLight;
  uniform vec3 uDirtDark;
  uniform float uNight;
  uniform float uTime;
  varying vec3 vW;
  ${WIND_GLSL}
  #include <common>
  #include <fog_pars_fragment>

  float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x),
               mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
  }
  float pathX(float u) {
    float amp = 0.35 + 0.09 * clamp(u, 0.0, 40.0);
    return amp * sin(0.16 * u) + 0.45 * amp * sin(0.41 * u + 1.3) - 0.45 * 0.35 * sin(1.3);
  }
  vec3 speckColor(float h) {
    if (h < 0.5) return vec3(1.0, 0.82, 0.18);
    if (h < 0.7) return vec3(1.0, 0.62, 0.14);
    if (h < 0.88) return vec3(1.0, 0.96, 0.84);
    return vec3(1.0, 0.6, 0.78);
  }
  vec4 speckle(vec2 p, float cell, float dens, float rad) {
    vec2 g = p / cell;
    vec2 id = floor(g);
    vec2 f = fract(g) - 0.5;
    float r = hash(id);
    if (r > dens) return vec4(0.0);
    vec2 off = (vec2(hash(id + 3.1), hash(id + 7.7)) - 0.5) * 0.55;
    float dd = length(f - off);
    float px = length(fwidth(g));
    float fade = 1.0 - smoothstep(rad * 0.6, rad * 1.5, px);
    float a = (1.0 - smoothstep(rad * 0.65, rad, dd)) * fade;
    return vec4(speckColor(hash(id + 11.3)), a);
  }

  void main() {
    vec2 w = vW.xz;
    float u = -w.y;
    float dist = length(vW - cameraPosition);
    float dx = w.x - pathX(u);
    float en = noise(vec2(u * 1.1, w.x * 0.8)) * 0.5 + noise(vec2(u * 4.5, w.x * 3.7)) * 0.2;
    float hw = 0.85 + (en - 0.35) * 0.5;
    float d = abs(dx) - hw;
    float pathM = 1.0 - smoothstep(-0.08, 0.1, d);

    float n1 = noise(w * 0.35);
    float n2 = noise(w * 1.7);
    float n3 = noise(w * 6.0);
    vec3 gcol = mix(uGDark, uGLight, clamp(n1 * 0.75 + n2 * 0.25 + (n3 - 0.5) * 0.18, 0.0, 1.0));
    float far = smoothstep(7.0, 46.0, dist);
    gcol = mix(gcol, uGFar, far);

    vec4 s1 = speckle(w, 0.55, 0.26, 0.2);
    vec4 s2 = speckle(w + 17.3, 1.7, 0.32, 0.19);
    float inGrass = 1.0 - pathM;
    float dayDots = 1.0 - 0.6 * uNight;
    gcol = mix(gcol, s1.rgb, s1.a * inGrass * 0.95 * dayDots);
    gcol = mix(gcol, s2.rgb, s2.a * inGrass * 0.95 * dayDots);

    vec3 dirt = mix(uDirt, uDirtLight, clamp(noise(vec2(w.x * 1.3, u * 0.35)) * 0.8 + noise(w * 5.0) * 0.2, 0.0, 1.0));
    float edge = smoothstep(-0.5, -0.02, d);
    dirt = mix(dirt, uDirtDark, edge * 0.5);
    float streak = noise(vec2(w.x * 7.0, u * 0.6));
    dirt *= 0.94 + 0.12 * streak;

    float fringe = (1.0 - smoothstep(0.0, 0.55, d)) * (1.0 - pathM);
    gcol = mix(gcol, uGDark * 0.7, fringe * 0.55);

    vec3 col = mix(gcol, dirt, pathM);
    // clouds cross the meadow: a soft shadow, strongest on open ground, never on the path edge alone
    col *= windCloud(w);
    col *= uGrass;
    gl_FragColor = vec4(col, 1.0);
    #include <colorspace_fragment>
    #include <fog_fragment>
  }
`;

export function createGroundMaterial(shared) {
  return new THREE.ShaderMaterial({
    vertexShader: GROUND_VERT,
    fragmentShader: GROUND_FRAG,
    fog: true,
    uniforms: withFog({
      ...windUniforms(shared),
      uGrass: shared.uGrass,
      uNight: shared.uNight,
      uGDark: { value: new THREE.Color('#2f6a27') },
      uGLight: { value: new THREE.Color('#68a834') },
      uGFar: { value: new THREE.Color('#c4d24e') },
      uDirt: { value: new THREE.Color('#c9a082') },
      uDirtLight: { value: new THREE.Color('#e2c3a0') },
      uDirtDark: { value: new THREE.Color('#9a7560') },
    }),
  });
}

/* ---------- painted backdrop ---------- */

/** How much wider than the painting the backdrop curtain is; the painting is mirrored into the extra width. */
export const BACKDROP_EXT = 1.5;

const BACKDROP_VERT = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const BACKDROP_FRAG = /* glsl */ `
  uniform sampler2D uMap;
  uniform vec3 uTint;
  uniform vec3 uGlow;
  uniform float uGlowAmt;
  uniform vec3 uCloud;
  uniform float uTime;
  uniform float uNight;
  uniform float uDrift;
  uniform float uWarp;     // 0 with reduced motion
  varying vec2 vUv;
  ${WIND_GLSL}

  float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x),
               mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
  }

  void main() {
    float ux = (1.0 - vUv.x - 0.5) * ${BACKDROP_EXT.toFixed(2)} + 0.5;
    ux = abs(fract(ux * 0.5 + 0.5) * 2.0 - 1.0);   // mirror the painting past its left and right edges
    vec2 uv = vec2(ux, vUv.y);
    vec3 c0 = texture2D(uMap, uv).rgb;
    // The painted trees and grass lean and shimmer with the gust: a small warp, only where the painting is green
    // and only below the horizon band, so the sky, the mountains and the horizon line never move.
    float green = smoothstep(0.015, 0.1, c0.g - max(c0.r * 0.82, c0.b));
    float band = smoothstep(0.30, 0.38, uv.y) * (1.0 - smoothstep(0.455, 0.49, uv.y));
    float wm = green * band * uWarp;
    vec2 wp = vec2(uv.x * 190.0, uv.y * 40.0);   // the gust field read across the picture, in metres
    float s = windGust(wp, 0.0);
    float hd = windHeading(wp);
    float tw = sin(uTime * 1.3 + uv.x * 90.0 + uv.y * 30.0) * 0.35 + sin(uTime * 2.1 + uv.x * 47.0) * 0.25;
    vec2 warp = vec2(cos(hd), 0.0) * (0.0011 * s + 0.00028 * tw * (0.4 + s)) * (0.25 + 0.75 * smoothstep(0.30, 0.46, uv.y));
    vec3 c = wm > 0.001 ? texture2D(uMap, uv + warp * wm).rgb : c0;
    c *= 1.0 + 0.1 * (s - 0.35) * wm;                 // light rides the gust through the foliage
    float lum = dot(c, vec3(0.299, 0.587, 0.114));
    float sky = smoothstep(0.50, 0.62, uv.y);

    // drifting cloud tint: slow noise that warms or cools the bright parts of the sky
    float t = uTime * 0.012 * uDrift;
    float n = noise(vec2(uv.x * 3.2 + t, uv.y * 2.4)) * 0.65 + noise(vec2(uv.x * 7.5 - t * 1.6, uv.y * 5.0)) * 0.35;
    float cloudMask = smoothstep(0.55, 0.9, lum) * sky;
    c = mix(c, c * mix(vec3(1.0), uCloud * 1.12, 0.55), cloudMask * smoothstep(0.25, 0.85, n));
    c *= 1.0 + (n - 0.5) * 0.16 * sky * uDrift;

    // a wisp of cloud shadow over the far hills, the same field that shades the meadow
    c *= mix(1.0, windCloud(wp * 1.3), band * 0.6);
    c *= uTint;
    // horizon glow
    float hz = exp(-pow((uv.y - 0.5) * 5.5, 2.0));
    float sx = exp(-pow((uv.x - 0.56) * 2.4, 2.0));
    c += uGlow * uGlowAmt * (0.35 + 0.65 * sx) * hz;
    // darken far below horizon (never visible, keeps the seam calm)
    gl_FragColor = vec4(c, 1.0);
    #include <colorspace_fragment>
  }
`;

export function createBackdropMaterial(texture, shared) {
  return new THREE.ShaderMaterial({
    vertexShader: BACKDROP_VERT,
    fragmentShader: BACKDROP_FRAG,
    side: THREE.BackSide,
    depthWrite: false,
    fog: false,
    uniforms: {
      ...windUniforms(shared),
      uWarp: { value: 1 },
      uMap: { value: texture },
      uTint: { value: new THREE.Color('#ffffff') },
      uGlow: { value: new THREE.Color('#ffffff') },
      uGlowAmt: { value: 0 },
      uCloud: { value: new THREE.Color('#ffffff') },
      uNight: shared.uNight,
      uDrift: { value: 1 },
    },
  });
}

/* ---------- points: pollen, sparkles, fireflies, stars ---------- */

const POINTS_VERT = /* glsl */ `
  attribute vec4 aSeed;
  uniform float uTime;
  uniform float uDpr;
  uniform float uSize;
  uniform vec3 uBoxMin;
  uniform vec3 uBoxSize;
  uniform vec3 uDrift;
  uniform float uWander;
  uniform float uMove;
  uniform float uBlink;
  uniform float uStatic;
  uniform float uWindPush;
  varying float vA;
  ${WIND_GLSL}
  void main() {
    vec3 p = position;
    if (uStatic < 0.5) {
      float t = uTime * uMove;
      p += uDrift * t;
      p += vec3(sin(t * 0.7 + aSeed.w * 6.283), sin(t * 0.9 + aSeed.w * 12.0) * 0.5, cos(t * 0.6 + aSeed.w * 9.0)) * uWander;
      // a gust shoves the pollen along the wind and lets it settle again (a bounded push, so nothing ever jumps)
      float s = windGust(p.xz, 0.0);
      float hd = windHeading(p.xz);
      p += vec3(cos(hd), 0.12 * (s - 0.4), sin(hd)) * (s - 0.3) * 1.6 * uWindPush;
      p = uBoxMin + mod(p - uBoxMin, uBoxSize);
    }
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    gl_Position = projectionMatrix * mv;
    float tw = 0.5 + 0.5 * sin(uTime * uBlink + aSeed.w * 40.0);
    vA = mix(1.0, tw, 0.85) * (0.55 + 0.45 * aSeed.x);
    float size = uSize * (0.6 + 0.8 * aSeed.y);
    gl_PointSize = clamp(size * uDpr * 14.0 / max(-mv.z, 0.5), 1.0, 40.0 * uDpr);
  }
`;

const POINTS_FRAG = /* glsl */ `
  uniform vec3 uColor;
  uniform float uAlpha;
  uniform float uStar;
  varying float vA;
  void main() {
    vec2 p = gl_PointCoord - 0.5;
    float r = length(p);
    float a = smoothstep(0.5, 0.0, r);
    if (uStar > 0.5) {
      float cross = max(smoothstep(0.06, 0.0, abs(p.x)) * smoothstep(0.5, 0.0, abs(p.y)),
                        smoothstep(0.06, 0.0, abs(p.y)) * smoothstep(0.5, 0.0, abs(p.x)));
      a = max(a * a, cross);
    } else {
      a = a * a;
    }
    gl_FragColor = vec4(uColor, a * vA * uAlpha);
    #include <colorspace_fragment>
  }
`;

export function createPointsMaterial(shared, opts) {
  return new THREE.ShaderMaterial({
    vertexShader: POINTS_VERT,
    fragmentShader: POINTS_FRAG,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    fog: false,
    uniforms: {
      ...windUniforms(shared),
      uWindPush: { value: opts.windPush ?? 0 },
      uDpr: shared.uDpr,
      uSize: { value: opts.size ?? 1 },
      uBoxMin: { value: new THREE.Vector3(...(opts.boxMin ?? [-6, 0, -14])) },
      uBoxSize: { value: new THREE.Vector3(...(opts.boxSize ?? [12, 4, 22])) },
      uDrift: { value: new THREE.Vector3(...(opts.drift ?? [0.05, 0.03, 0])) },
      uWander: { value: opts.wander ?? 0.4 },
      uMove: { value: opts.move ?? 1 },
      uBlink: { value: opts.blink ?? 1.5 },
      uStatic: { value: opts.isStatic ? 1 : 0 },
      uColor: { value: new THREE.Color(opts.color ?? '#fff6d8') },
      uAlpha: { value: opts.alpha ?? 1 },
      uStar: { value: opts.star ? 1 : 0 },
    },
  });
}
