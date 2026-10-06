// w3: the held web page window as one draw call (BEHAVIOUR-SPEC 6.1 to 6.4). One quad, three texture tiles.
//
// Everything that moves is a uniform, so scrolling, the skeleton shimmer, the found highlight and the open and
// close all cost no canvas work and no texture upload: the page is drawn once per content state (pageRenderer.js)
// and this shader slides a 424 px viewport over it.
//
//   window    a rounded rectangle (radius 27 logical px) with a mint rim and a soft outer glow
//   chrome    the top 56 px, fixed (title row and URL pill), from atlas y 0 to 56
//   page      atlas y = lp.y + scroll for lp.y >= 56, a 12 px fade at the bottom, a 3 px scroll bar
//   skeleton  a diagonal shimmer over the grey placeholder bars, every 1.2 s
//   found     the gold outline and glow of the found card, in page space, with one pulse
//
// The window is 360 x 480 logical px = 0.24 x 0.32 m (1500 logical px per metre).

import { COMMON, PANEL_VERT } from '../hologramShader.js';

export const WEB_VERT = PANEL_VERT;

export const WEB_FRAG = /* glsl */ `
precision mediump float;
uniform sampler2D uTex0, uTex1, uTex2;
uniform float uScale, uCanvasH, uScroll, uPageH, uSharp;
uniform float uAlpha, uWipe, uGold, uDim, uLuma, uRtl, uSkel, uShim, uBarA, uHlA, uPulse, uReady;
uniform vec4 uHl;
uniform vec3 uCore, uFoundC, uPlate;
varying vec2 vUv;
${COMMON}

const vec2 WS = vec2(360.0, 480.0);
const float CHROME = 56.0;
const float VIEW = 424.0;
const float TILEH = 480.0;
const float TILEPAD = 4.0;
const vec3 BG = vec3(0.930, 0.947, 0.956);

void main(){
  vec2 p = (vUv - 0.5) * WS * PAD;                 // window space, metres-free logical px, y up, origin at the centre
  highp vec2 lp = vec2(p.x + 180.0, 240.0 - p.y);  // from the top left of the window
  float d = sdRound(p, WS * 0.5, 27.0);
  float inside = aa(d);

  // ---- the atlas lookup (highp: a half float cannot address a 900 px texture sharply) ----
  highp float ay = lp.y < CHROME ? lp.y : lp.y + uScroll;
  highp float py = lp.y - CHROME + uScroll;
  highp float tk = clamp(floor(ay / TILEH), 0.0, 2.0);
  highp vec2 uv = vec2(lp.x / 360.0, 1.0 - (ay - tk * TILEH + TILEPAD) * uScale / uCanvasH);
  highp vec2 gx = dFdx(lp) * vec2(1.0 / 360.0, -uScale / uCanvasH);
  highp vec2 gy = dFdy(lp) * vec2(1.0 / 360.0, -uScale / uCanvasH);
  vec3 col = BG;
  bool have = uReady > 0.5 && (lp.y < CHROME || (py >= 0.0 && py < uPageH));
  if (have) {
    vec4 t = tk < 0.5 ? textureGrad(uTex0, uv, gx, gy) : (tk < 1.5 ? textureGrad(uTex1, uv, gx, gy) : textureGrad(uTex2, uv, gx, gy));
    col = t.rgb;
    if (uSharp > 0.001) {   // a light unsharp mask: resampling the atlas at about 1 device px per texel softens the glyph edges
      highp vec2 ox = gx * 0.7, oy = gy * 0.7;
      vec3 a = vec3(0.0);
      if (tk < 0.5) a = textureGrad(uTex0, uv + ox, gx, gy).rgb + textureGrad(uTex0, uv - ox, gx, gy).rgb + textureGrad(uTex0, uv + oy, gx, gy).rgb + textureGrad(uTex0, uv - oy, gx, gy).rgb;
      else if (tk < 1.5) a = textureGrad(uTex1, uv + ox, gx, gy).rgb + textureGrad(uTex1, uv - ox, gx, gy).rgb + textureGrad(uTex1, uv + oy, gx, gy).rgb + textureGrad(uTex1, uv - oy, gx, gy).rgb;
      else a = textureGrad(uTex2, uv + ox, gx, gy).rgb + textureGrad(uTex2, uv - ox, gx, gy).rgb + textureGrad(uTex2, uv + oy, gx, gy).rgb + textureGrad(uTex2, uv - oy, gx, gy).rgb;
      col = clamp(col + (col - a * 0.25) * uSharp, 0.0, 1.0);
    }
  }

  // the page's own edges: a soft fade at the bottom and just under the chrome
  float page = step(CHROME, lp.y);
  col = mix(BG, col, mix(1.0, smoothstep(CHROME, CHROME + 10.0, lp.y), page) * (1.0 - page * smoothstep(WS.y - 14.0, WS.y - 1.0, lp.y)));

  // ---- the skeleton shimmer: a diagonal band over the grey placeholder bars, every 1.2 s ----
  if (uSkel > 0.5) {
    float u = lp.x + lp.y * 0.6;
    float c = mix(-140.0, 600.0, uShim);
    float band = smoothstep(70.0, 0.0, abs(u - c));
    float lum = dot(col, vec3(0.3333));
    float gray = smoothstep(0.84, 0.74, lum) * step(CHROME, lp.y);   // linear luminance of the grey bars and a little above
    col += (1.0 - col) * band * (0.35 + 0.65 * gray) * 0.85 * step(CHROME, lp.y);
  }

  // ---- the found card: gold outline and glow in page space ----
  if (uHl.z > 0.5 && uHlA > 0.001) {
    vec2 hc = uHl.xy + uHl.zw * 0.5;
    float dH = sdRound(vec2(lp.x, py) - hc, uHl.zw * 0.5, 16.0);
    float vis = uHlA * smoothstep(CHROME - 2.0, CHROME + 10.0, lp.y);
    float ring = aa(abs(dH) - (1.4 + 1.6 * uPulse));
    float glow = exp(-max(dH, 0.0) / 7.0) * (1.0 - smoothstep(0.0, 18.0, dH)) * (0.35 + 0.35 * uPulse);
    col *= mix(vec3(1.0), vec3(1.0, 0.92, 0.72), aa(dH) * vis);   // a warm card tint that keeps the text dark (a mix toward gold would turn dark text olive)
    col = mix(col, uFoundC, glow * 0.55 * vis * (1.0 - aa(dH)));
    col = mix(col, uFoundC, ring * vis);
  }

  // ---- the scroll bar: 3 px, on the reading-end side (the right in English, the left in Arabic) ----
  if (uBarA > 0.001 && uPageH > VIEW + 8.0) {
    float bx = uRtl > 0.5 ? 5.5 : 354.5;
    float top = CHROME + 10.0;
    float run = WS.y - 14.0 - top;
    float len = max(28.0, VIEW / uPageH * run);
    float tp = top + clamp(uScroll / max(uPageH - VIEW, 1.0), 0.0, 1.0) * (run - len);
    float bar = aa(sdRound(lp - vec2(bx, tp + len * 0.5), vec2(1.5, len * 0.5), 1.5));
    col = mix(col, vec3(0.19, 0.25, 0.27), bar * uBarA * 0.5);
  }

  // ---- the open: the content is scanned in from the top ----
  float rv = smoothstep(0.0, 14.0, uWipe * (WS.y + 14.0) - lp.y);
  col = mix(uPlate, col, rv);
  col += uCore * (1.0 - smoothstep(0.0, 5.0, abs(uWipe * (WS.y + 14.0) - lp.y))) * 0.6 * step(uWipe, 0.999);

  // ---- not found: dimmed and washed out; found: the flash lifts it (at most uLuma) ----
  float gl = dot(col, vec3(0.3333));
  col = mix(col, vec3(gl), 0.5 * uDim) * (1.0 - 0.45 * uDim);
  col *= 1.0 + uLuma * 0.5;

  // ---- the rim and the glow ----
  float rim = clamp(aa(d) - aa(d + 6.0), 0.0, 1.0);
  vec3 rimC = mix(uCore, uFoundC, uGold) * (1.0 + uLuma);
  col = mix(col, rimC, rim * 0.92);
  float so = max(d, 0.0);
  float g = exp(-so / 9.0) * (1.0 - smoothstep(0.0, 30.0, so)) * (0.30 + 0.25 * uGold) * (1.0 - 0.5 * uDim);

  vec3 rgb = col * inside + rimC * g * (1.0 - inside);
  float a = inside + g * 0.6 * (1.0 - inside);
  gl_FragColor = vec4(rgb, a) * uAlpha;
  #include <colorspace_fragment>
}
`;
