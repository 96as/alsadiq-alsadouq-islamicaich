// GLSL for the search hologram (SPEC-EXPERIENCE 7.3). Everything is drawn from signed distance
// fields: no textures, no texture fetches. One draw call per layer: beam, panel, halo, sparkles.
//
// The panel shader draws a dark glass plate (premultiplied alpha, so it stays readable against the
// bright meadow sky) plus additive content in the same pass. The layout is designed right to left
// ("d" space: +x is the reading start side); in English it is mirrored with uRtl = 0, while the
// motion (the page turn, the progress bar) always runs left to right in screen space ("q" space).
//
// No real content and no letters are drawn: only abstract shapes.

// Fragment shaders run at mediump (half floats on phones: fewer ALU cycles, less bandwidth). Desktop GPUs
// ignore it. The vertex stage stays highp (a mediump modelViewMatrix would make the panel shimmer), and the
// two things that need the range are marked highp: the clock (it runs to 600 s) and the hash (it multiplies
// up to ~2300, and a half float cannot hold the fraction there).
const MEDIUMP = 'precision mediump float;\n';

export const COMMON = /* glsl */ `
const vec2 HS = vec2(0.13, 0.0975);   // half size of the panel in metres
const float PAD = 1.12;               // the panel quad is this much larger than the plate
highp float h11(highp float p){ p = fract(p * 0.1031); p *= p + 33.33; p *= p + p; return fract(p); }
float aa(float d){ float w = max(fwidth(d), 1e-5); return 1.0 - smoothstep(-w, w, d); }
float sdRound(vec2 p, vec2 b, float r){ vec2 q = abs(p) - b + r; return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r; }
float sdSeg(vec2 p, vec2 a, vec2 b){ vec2 pa = p - a, ba = b - a; float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0); return length(pa - ba * h); }
float sdBox(vec2 p, vec2 b){ vec2 q = abs(p) - b; return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0); }
mat2 rot(float a){ float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
float easeOutBack(float x){ float u = clamp(x, 0.0, 1.0) - 1.0; return 1.0 + 2.2 * u * u * u + 1.2 * u * u; }
`;

export const PANEL_VERT = /* glsl */ `
varying vec2 vUv;
void main(){
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

export const PANEL_FRAG = MEDIUMP + /* glsl */ `
uniform highp float uTime;
uniform float uAlpha, uWipe, uGold, uDim, uLuma, uStamp;
uniform float uPageT, uPage, uProgress, uKind, uPrevKind, uKindMix, uRtl, uPlateA;
uniform vec2 uPar;
uniform vec3 uCore, uHi, uPlate, uFound, uFoundHi, uT0, uT1, uT2;
varying vec2 vUv;
${COMMON}

// ---- skin: verified library (book spines, an open book, wavy lines, a star, a seal) ----
vec3 skinLibrary(vec2 d, vec2 q, vec3 C, vec3 H){
  vec3 acc = vec3(0.0);
  // a strip of book spines
  for (int i = 0; i < 6; i++) {
    float fi = float(i);
    float h = 0.018 + 0.018 * h11(fi * 7.3 + 1.7);
    vec2 c = vec2(-0.062 + fi * 0.032, 0.047 + h * 0.5);
    float dist = sdRound(d - c, vec2(0.0095, h * 0.5), 0.003);
    vec3 tint = mix(C, H, 0.25 + 0.5 * h11(fi * 3.1));
    acc += tint * (0.16 * aa(dist) + 0.8 * aa(abs(dist) - 0.0012) + 0.2 * exp(-max(dist, 0.0) / 0.004));
    float band = aa(abs(d.y - (c.y + h * 0.5 - 0.006)) - 0.0012) * aa(dist + 0.002);
    acc += H * 0.5 * band;
  }
  // the open book: two pages, the first one (reading start) on the +x side
  for (int s = 0; s < 2; s++) {
    float sg = s == 0 ? 1.0 : -1.0;
    vec2 c = vec2(sg * 0.047, -0.02);
    vec2 lp = d - c;
    float dist = sdRound(lp, vec2(0.043, 0.0555), 0.008);
    acc += C * (0.12 * aa(dist) + 0.9 * aa(abs(dist) - 0.0014) + 0.22 * exp(-max(dist, 0.0) / 0.004));
    // wavy lines (no letters): ragged on the far side
    float ry = (lp.y + 0.046) / 0.0156;
    float row = floor(ry);
    float fy = fract(ry) - 0.5 + 0.16 * sin(lp.x * 62.0 + row * 1.9);
    float len = 0.42 + 0.5 * h11(row * 3.1 + sg * 11.0 + uPage * 5.3);
    float inX = step(lp.x, 0.034) * step(0.034 - len * 0.068, lp.x);
    float inRow = step(0.0, row) * step(row, 5.0) * step(abs(lp.y), 0.0505);
    acc += mix(C, H, 0.2) * 0.55 * aa((abs(fy) - 0.1) * 0.0156) * inX * inRow * aa(dist + 0.004);
  }
  acc += C * 0.9 * aa(sdBox(d - vec2(0.0, -0.02), vec2(0.0011, 0.0555)));   // the spine of the book
  // the page turn: a leaf pivoting at the spine, always left to right on screen
  if (uPageT < 0.25) {
    float f = smoothstep(0.0, 1.0, uPageT / 0.25);
    float w = -0.086 * cos(f * 3.14159);
    vec2 lc = vec2(w * 0.5, -0.02);
    float dist = sdRound(q - lc, vec2(max(abs(w) * 0.5, 0.001), 0.0555), 0.006);
    float edge = aa(abs(q.x - w) - 0.0014) * step(abs(q.y + 0.02), 0.0555);
    acc += H * (0.22 * aa(dist) + 0.85 * aa(abs(dist) - 0.0014) + 0.9 * edge);
  }
  // an 8-point star ornament in the far corner
  vec2 sp = d - vec2(-0.108, 0.073);
  float star = min(sdBox(sp, vec2(0.0075)), sdBox(rot(0.7854) * sp, vec2(0.0075)));
  acc += mix(C, H, 0.5) * (0.5 * aa(star) + 0.5 * exp(-max(star, 0.0) / 0.004)) * (0.7 + 0.3 * sin(uTime * 2.0));
  // on Found: a verified seal (a check in a rosette) is stamped on the page
  if (uStamp >= 0.0) {
    float sc = easeOutBack(uStamp / 0.22) * mix(1.5, 1.0, clamp(uStamp / 0.22, 0.0, 1.0));
    vec2 sp2 = (d - vec2(0.05, -0.024)) / max(sc, 0.001);
    float a = atan(sp2.y, sp2.x);
    float rr = length(sp2) - 0.03 * (1.0 + 0.07 * cos(12.0 * a));
    float ring = length(sp2) - 0.021;
    float chk = min(sdSeg(sp2, vec2(-0.012, -0.001), vec2(-0.003, -0.011)), sdSeg(sp2, vec2(-0.003, -0.011), vec2(0.014, 0.011)));
    float on = clamp(uStamp / 0.08, 0.0, 1.0);
    acc += H * on * (0.35 * aa(rr) + 0.9 * aa(abs(ring) - 0.0014) + 1.1 * aa(chk - 0.0026));
    acc += C * on * 0.3 * exp(-max(rr, 0.0) / 0.006);
  }
  return acc;
}

// ---- skin: the child's folders (three tabbed folders, a lid opens, cards peek, a star lands) ----
vec3 skinFolders(vec2 d, vec2 q, vec3 C, vec3 H){
  vec3 acc = vec3(0.0);
  // a stack of cards behind (a fake depth: smaller and dimmer toward the back)
  float b0 = sdRound(d - vec2(0.0, -0.012), vec2(0.116, 0.046), 0.012);
  float b1 = sdRound(d - vec2(0.0, -0.002), vec2(0.104, 0.05), 0.011);
  acc += C * (0.05 * aa(b0) + 0.35 * aa(abs(b0) - 0.001));
  acc += C * (0.03 * aa(b1) + 0.18 * aa(abs(b1) - 0.001));
  // a title pill and a smaller one
  float p0 = sdRound(d - vec2(0.05, 0.071), vec2(0.052, 0.0075), 0.0075);
  float p1 = sdRound(d - vec2(-0.07, 0.071), vec2(0.028, 0.0075), 0.0075);
  acc += H * (0.14 * aa(p0) + 0.6 * aa(abs(p0) - 0.0012)) + C * (0.1 * aa(p1) + 0.45 * aa(abs(p1) - 0.0012));
  for (int i = 0; i < 3; i++) {
    float fi = float(i);
    float x = (1.0 - fi) * 0.075;
    vec3 tint = i == 0 ? uT0 : (i == 1 ? uT1 : uT2);
    tint = mix(tint, C, uGold * 0.5);
    float ph = fract(uTime * 0.33 + fi * 0.34);
    float o = smoothstep(0.0, 0.22, ph) * (1.0 - smoothstep(0.5, 0.75, ph));
    // the back plate and its tab
    float body = sdRound(d - vec2(x, -0.0), vec2(0.031, 0.0285), 0.006);
    float tab = sdRound(d - vec2(x + 0.014, 0.031), vec2(0.0105, 0.0055), 0.0035);
    acc += tint * (0.14 * aa(body) + 0.8 * aa(abs(body) - 0.0013) + 0.7 * aa(tab) * 0.45 + 0.6 * aa(abs(tab) - 0.0011));
    // cards peeking out
    for (int k = 0; k < 2; k++) {
      float fk = float(k);
      vec2 cc = vec2(x - 0.002 + fk * 0.003, 0.002 + o * (0.020 + fk * 0.007));
      float card = sdRound(d - cc, vec2(0.0235 - fk * 0.002, 0.0185), 0.004);
      float clip = step(-0.027, d.y);
      acc += mix(tint, H, 0.35) * (0.22 * aa(card) + 0.65 * aa(abs(card) - 0.0011)) * clip * (0.7 + 0.3 * fk);
    }
    // the lid (front flap) opens: it gets shorter
    float hh = 0.0165 * (1.0 - 0.5 * o);
    float flap = sdRound(d - vec2(x, -0.0285 + hh), vec2(0.031, hh), 0.005);
    acc += tint * (0.28 * aa(flap) + 0.95 * aa(abs(flap) - 0.0013) + 0.25 * exp(-max(flap, 0.0) / 0.004));
  }
  // on Found: a star sticker lands on the middle folder
  if (uStamp >= 0.0) {
    float k = clamp(uStamp / 0.25, 0.0, 1.0);
    float sc = easeOutBack(k) * (1.0 + 0.9 * (1.0 - k));
    vec2 sp = rot((1.0 - k) * 1.3) * (d - vec2(0.0, -0.018)) / max(sc, 0.001);
    float a = atan(sp.y, sp.x) - 1.5708;
    float r = length(sp);
    float rr = r - 0.016 * (0.52 + 0.48 * pow(0.5 + 0.5 * cos(5.0 * a), 0.7));
    acc += H * clamp(k * 3.0, 0.0, 1.0) * (0.95 * aa(rr) + 0.5 * exp(-max(rr, 0.0) / 0.005));
  }
  return acc;
}

// ---- skin: search cards (a search bar with typing dots, result cards scrolling up) ----
vec3 skinWeb(vec2 d, vec2 q, vec3 C, vec3 H){
  vec3 acc = vec3(0.0);
  // the search bar: a pill with a magnifier on the start side and typing dots
  float bar = sdRound(d - vec2(0.0, 0.066), vec2(0.096, 0.0125), 0.0125);
  acc += C * (0.12 * aa(bar) + 0.85 * aa(abs(bar) - 0.0013) + 0.2 * exp(-max(bar, 0.0) / 0.005));
  vec2 mp = d - vec2(0.075, 0.066);
  float ring = abs(length(mp) - 0.0055) - 0.0011;
  float handle = sdSeg(mp, vec2(0.0039, -0.0039), vec2(0.0085, -0.0085)) - 0.0012;
  acc += H * 0.95 * (aa(ring) + aa(handle));
  for (int k = 0; k < 3; k++) {
    float fk = float(k);
    float on = 0.3 + 0.7 * pow(0.5 + 0.5 * sin(uTime * 5.0 - fk * 1.3), 2.0);
    float dot_ = length(d - vec2(0.03 - fk * 0.014, 0.066)) - 0.0026;
    acc += H * on * aa(dot_) + C * on * 0.4 * exp(-max(dot_, 0.0) / 0.004);
  }
  // result cards scroll up, 0.9 cards per second, and jump one card when the page turns
  float sp = 0.0;
  {
    float u = clamp(uPageT / 0.25, 0.0, 1.0);
    float spring = u < 1.0 ? easeOutBack(u) : 1.0;
    sp = uTime * 0.9 + uPage - 1.0 + spring;
  }
  float pitch = 0.05;
  float cm = smoothstep(-0.088, -0.072, d.y) * (1.0 - smoothstep(0.03, 0.043, d.y));
  for (int j = 0; j < 5; j++) {
    float fj = float(j);
    float id = floor(sp) + fj;
    float y = 0.02 - fj * pitch + fract(sp) * pitch + 0.025;
    vec3 tint = mix(C, H, 0.15 * h11(id * 1.9));
    float card = sdRound(d - vec2(0.0, y), vec2(0.092, 0.0195), 0.007);
    float th = sdRound(d - vec2(0.069, y), vec2(0.0135, 0.0135), 0.004);
    float acc2 = 0.07 * aa(card) + 0.5 * aa(abs(card) - 0.0011) + 0.28 * aa(th) + 0.7 * aa(abs(th) - 0.001);
    for (int k = 0; k < 3; k++) {
      float fk = float(k);
      float len = 0.3 + 0.55 * h11(id * 5.3 + fk * 2.1);
      float ly = y + 0.009 - fk * 0.0088;
      float l = sdBox(d - vec2(0.04 - len * 0.045, ly), vec2(len * 0.045, 0.0014));
      acc2 += 0.55 * aa(l);
    }
    acc += tint * acc2 * cm;
  }
  return acc;
}

vec3 skin(float k, vec2 d, vec2 q, vec3 C, vec3 H){
  if (k < 0.5) return skinLibrary(d, q, C, H);
  if (k < 1.5) return skinFolders(d, q, C, H);
  return skinWeb(d, q, C, H);
}

void main(){
  vec2 q = (vUv - 0.5) * HS * 2.0 * PAD;   // the quad is PAD times the panel, so the rim glow is not clipped
  vec2 d = vec2(uRtl > 0.5 ? q.x : -q.x, q.y);
  vec3 C = mix(uCore, uFound, uGold);
  vec3 H = mix(uHi, uFoundHi, uGold);

  float sd = sdRound(q, HS, 0.022);
  float inside = aa(sd);

  // the dark glass plate, a little lighter toward the top, with a soft diagonal sheen
  vec3 plate = uPlate * (0.8 + 0.55 * vUv.y);
  float sheen = exp(-pow((q.x + q.y * 1.2 + 0.075) / 0.03, 2.0)) * 0.1;
  float plateA = uPlateA * inside;
  vec3 add = vec3(0.0);
  add += H * sheen * inside;
  add += C * 0.07 * inside;
  add += C * exp(-max(-sd, 0.0) / 0.007) * 0.3 * inside;   // light gathering at the inner edge

  // the rim, a thin bright line with a glow outside, and HUD corner brackets
  float rim = aa(abs(sd) - 0.002);
  add += mix(C, H, 0.55) * rim * 0.95;
  add += C * exp(-max(sd, 0.0) / 0.0055) * 0.38 * (1.0 - inside);
  vec2 a = abs(q);
  vec2 e = HS - vec2(0.012);
  float bh = step(a.x, e.x) * step(e.x - 0.03, a.x) * aa(abs(a.y - e.y) - 0.0013);
  float bv = step(a.y, e.y) * step(e.y - 0.03, a.y) * aa(abs(a.x - e.x) - 0.0013);
  add += H * (bh + bv) * 0.85;

  // content, revealed by a scan line from the top
  float wipeY = HS.y - uWipe * (2.0 * HS.y + 0.02);
  float cm = smoothstep(wipeY - 0.003, wipeY + 0.003, q.y) * aa(sd + 0.008);
  vec3 content;
  // the magnifier lens: a Lissajous path, content seen at x1.35 inside the circle
  // Parallax: the content sits 4 mm behind the rim light and the lens 12 mm in front, so the three
  // layers slide against each other as the hand floats (uPar, from the sway).
  vec2 qc = q - uPar;
  vec2 ql = q + uPar * 1.8;
  vec2 dc = vec2(uRtl > 0.5 ? qc.x : -qc.x, qc.y);
  vec2 dl = vec2(uRtl > 0.5 ? ql.x : -ql.x, ql.y);
  vec2 lc = vec2(0.07 * cos(uTime * 1.3), 0.034 * sin(uTime * 1.9) - 0.014);
  vec2 lcd = vec2(uRtl > 0.5 ? lc.x : -lc.x, lc.y);
  float lensD = length(dl - lcd) - 0.022;
  float lensIn = aa(lensD + 0.001);
  vec2 dm = dc - (dl - lcd) * 0.2593 * lensIn;
  vec2 qm = qc - (ql - lc) * 0.2593 * lensIn;
  if (uKindMix < 1.0) {
    content = mix(skin(uPrevKind, dm, qm, C, H), skin(uKind, dm, qm, C, H), uKindMix);
  } else {
    content = skin(uKind, dm, qm, C, H);
  }
  // the lens itself (drawn above the content, +0.012 in depth)
  float lensRing = abs(lensD) - 0.0016;
  float lensGlass = aa(lensD);
  float lensHandle = sdSeg(dl - lcd, vec2(0.0155, -0.0155), vec2(0.027, -0.027)) - 0.0022;
  content += H * (0.9 * aa(lensRing) + 0.5 * aa(lensHandle)) * (1.0 - 0.0 * lensGlass);
  content += C * 0.12 * lensGlass + C * 0.35 * exp(-max(lensD, 0.0) / 0.004) * 0.5;
  add += content * cm;
  add += H * exp(-pow((q.y - wipeY) / 0.0045, 2.0)) * step(uWipe, 0.999) * 0.85 * aa(sd + 0.004);

  // a progress shimmer: a diagonal band sweeping right to left every 1.2 s
  float shimmerPos = 0.17 - fract(uTime / 1.2) * 0.4;
  float band = exp(-pow((q.x + q.y * 0.6 - shimmerPos) / 0.018, 2.0));
  add += H * band * 0.16 * cm * (0.4 + 0.6 * min(1.0, length(content)));
  // faint slow scanlines
  add *= 1.0 - 0.02 * (0.5 + 0.5 * sin(q.y * 700.0 - uTime * 2.2));

  // the progress bar along the bottom: it fills from the right to the left
  float track = sdRound(q - vec2(0.0, -0.0875), vec2(0.1, 0.0026), 0.0026);
  float fillX = 0.1 - 0.2 * uProgress;
  float filled = aa(track) * smoothstep(fillX - 0.002, fillX + 0.002, q.x);
  add += C * (0.18 * aa(track) + 0.85 * filled) * cm;

  // not found: dimmed and half desaturated
  float lum = dot(add, vec3(0.299, 0.587, 0.114));
  add = mix(add, vec3(lum), 0.5 * uDim) * (1.0 - 0.5 * uDim);
  // soft knee: bright content keeps its hue instead of clipping to white (gold especially)
  add = 1.0 - exp(-1.5 * add * (1.0 - 0.55 * uGold));
  // gold stays gold: the cream highlight colour and the summed glints pull every channel toward white, and
  // the flash (uLuma) lifts it further. Rebuild the colour from the gold hue at the same peak brightness.
  float peakC = max(add.r, max(add.g, add.b));
  add = mix(add, uFound * peakC, 0.7 * uGold);
  add *= 1.0 + uLuma;

  gl_FragColor = vec4(plate * plateA + add, plateA) * uAlpha;
  #include <colorspace_fragment>
}
`;

// ---- the light pyramid: four triangles from the palm to the panel's bottom edge ----
export const BEAM_VERT = /* glsl */ `
attribute float aT;
varying float vT;
void main(){
  vT = aT;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

export const BEAM_FRAG = MEDIUMP + /* glsl */ `
uniform vec3 uColor;
uniform highp float uTime;
uniform float uAmount, uAlphaPalm, uAlphaPanel, uFlicker;
varying float vT;
void main(){
  float a = mix(uAlphaPalm, uAlphaPanel, vT);
  float band = 0.82 + 0.18 * sin(vT * 13.0 - uTime * 1.4);
  float flick = 1.0 + uFlicker * sin(uTime * 2.3);
  gl_FragColor = vec4(uColor * a * band * flick * uAmount, 1.0);
  #include <colorspace_fragment>
}
`;

// ---- the halo: one quad, additive, radial falloff ----
export const HALO_FRAG = MEDIUMP + /* glsl */ `
uniform vec3 uColor;
uniform float uIntensity;
uniform float uScale;
uniform vec2 uHS; // w3: the plate's half size (the held web page is not the library panel's shape)
varying vec2 vUv;
${COMMON}
void main(){
  vec2 q = (vUv - 0.5) * uHS * 2.0 * uScale;
  float sd = sdRound(q, uHS, 0.022);
  // Glow outside the plate only, and exactly zero before the quad's edge (uScale 1.8 leaves 0.078 at the short side).
  float so = max(sd, 0.0);
  float g = exp(-so / 0.024) * (1.0 - smoothstep(0.0, 0.074, so)) * smoothstep(-0.004, 0.012, sd);
  // premultiplied: part light, part tint, so the glow keeps its colour over a bright backdrop instead of clipping to white
  float ga = clamp(g * uIntensity * 0.55, 0.0, 1.0);
  gl_FragColor = vec4(uColor * ga, ga * 0.7);
  #include <colorspace_fragment>
}
`;

// ---- sparkles: 18 orbiting the rim, 14 for the burst. One Points draw. ----
export const SPARK_VERT = /* glsl */ `
attribute vec4 aSeed;
attribute float aKind;
uniform float uTime, uOrbit, uBurstT, uBurstLife, uGravity, uBurstSpeed, uPx, uZ;
uniform vec3 uCenter, uRight, uUp, uNormal, uBurstOrigin;
uniform vec2 uHalf;
varying float vA;
varying float vGold;
void main(){
  vec3 pos;
  float size;
  if (aKind < 0.5) {
    float th = aSeed.x * 6.2832 + uTime * (0.22 + 0.18 * aSeed.y);
    float z = (aSeed.w < 0.5 ? -1.0 : 1.0) * uZ;
    pos = uCenter + uRight * cos(th) * uHalf.x * 1.04 + uUp * sin(th) * uHalf.y * 1.06 + uNormal * z;
    size = 0.0085 + 0.007 * aSeed.z;
    vA = uOrbit * (0.45 + 0.55 * sin(uTime * 2.4 + aSeed.y * 6.2832));
    vGold = 0.0;
  } else {
    float bt = uBurstT;
    float az = aSeed.x * 6.2832;
    float el = (aSeed.y - 0.3) * 1.6;
    vec3 dir = vec3(cos(az) * cos(el), sin(el), sin(az) * cos(el));
    float v = uBurstSpeed * (0.55 + 0.45 * aSeed.z);
    pos = uBurstOrigin + dir * v * max(bt, 0.0) - vec3(0.0, uGravity * bt * bt, 0.0);
    size = (0.011 + 0.008 * aSeed.w) * (1.0 - 0.5 * bt / uBurstLife);
    vA = bt < 0.0 ? 0.0 : (1.0 - bt / uBurstLife);
    vGold = 1.0;
  }
  vec4 mv = modelViewMatrix * vec4(pos, 1.0);
  gl_Position = projectionMatrix * mv;
  gl_PointSize = max(1.0, size * uPx / max(-mv.z, 0.05));
}
`;

export const SPARK_FRAG = MEDIUMP + /* glsl */ `
uniform vec3 uColor, uGoldColor, uHiColor;
varying float vA;
varying float vGold;
void main(){
  vec2 p = gl_PointCoord - 0.5;
  float r = length(p) * 2.0;
  float core = pow(max(1.0 - r, 0.0), 2.0);
  float glint = max(0.0, 1.0 - abs(p.x) * 16.0) * max(0.0, 1.0 - abs(p.y) * 2.2) + max(0.0, 1.0 - abs(p.y) * 16.0) * max(0.0, 1.0 - abs(p.x) * 2.2);
  float a = (core + 0.6 * glint) * vA;
  vec3 col = mix(uColor, uGoldColor, vGold);
  col = mix(col, uHiColor, 0.4 * core);
  gl_FragColor = vec4(col * a, 1.0);
  #include <colorspace_fragment>
}
`;
