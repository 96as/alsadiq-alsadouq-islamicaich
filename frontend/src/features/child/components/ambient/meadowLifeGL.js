// The WebGL2 side of MeadowLife: compiles the three passes, owns the textures and draws a frame. No React.
// See meadowLifeShader.js for what each pass does.

import { MEADOW_IMAGE } from '../meadowFraming';
import { MASK_H, MASK_W, computeMeadowMasks } from './meadowMasks';
import { meadowRect } from './meadowGeometry';
import { BLADE_SEGMENTS, FRAG_BASE, FRAG_BLADE, FRAG_PART, VERT_BLADE, VERT_FULL, VERT_PART } from './meadowLifeShader';
import { makeWindState, windState } from '../forest/wind/windField';
import { packWindUniforms } from '../forest/wind/windGlsl';
import { createWindNoiseGL } from '../forest/wind/windTexture';

const COMMON_UNIFORMS = ['uRect', 'uSize', 'uDpr', 'uHorizon', 'uTime', 'uMotion', 'uWindNoise', 'uWOff', 'uWVel', 'uWMisc', 'uWHeadT', 'uImg', 'uMask'];

const COUNTS = { high: { blades: 1700, particles: 12 }, low: { blades: 800, particles: 10 } };

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

function compile(gl, type, src) {
  const s = gl.createShader(type);
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(s);
    gl.deleteShader(s);
    throw new Error(`MeadowLife shader: ${log}`);
  }
  return s;
}

function program(gl, vs, fs, extraUniforms = []) {
  const p = gl.createProgram();
  const v = compile(gl, gl.VERTEX_SHADER, vs);
  const f = compile(gl, gl.FRAGMENT_SHADER, fs);
  gl.attachShader(p, v);
  gl.attachShader(p, f);
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(`MeadowLife link: ${gl.getProgramInfoLog(p)}`);
  gl.deleteShader(v);
  gl.deleteShader(f);
  const loc = {};
  for (const n of [...COMMON_UNIFORMS, ...extraUniforms]) loc[n] = gl.getUniformLocation(p, n);
  return { p, loc };
}

// cards-spec (05) perf: the narrow tier washes out the columns a portrait phone never shows, so its masks are not the full picture's:
// they are kept per tier (a rotation to landscape loads the full file and needs its own).
const maskCache = new Map();
function masksFor(img) {
  const key = /meadow-narrow-/.test(img.currentSrc || img.src || '') ? 'narrow' : 'full';
  if (maskCache.has(key)) return maskCache.get(key);
  const c = document.createElement('canvas');
  c.width = MASK_W;
  c.height = MASK_H;
  const g = c.getContext('2d', { willReadFrequently: true });
  g.imageSmoothingEnabled = true;
  g.imageSmoothingQuality = 'high';
  g.drawImage(img, 0, 0, MASK_W, MASK_H);
  const masks = computeMeadowMasks(g.getImageData(0, 0, MASK_W, MASK_H).data);
  maskCache.set(key, masks);
  return masks;
}

/** The smallest file of the srcset that covers `needPx`, capped. */
export function pickWidth(needPx, cap) {
  const ws = MEADOW_IMAGE.widths.filter((w) => w <= cap);
  for (const w of ws) if (w >= needPx) return w;
  return ws[ws.length - 1];
}

/**
 * opts: { quality: 'high'|'low', anchored: boolean }.
 * Returns null when WebGL2 or a shader is unavailable (the caller keeps the <img>).
 */
export function createMeadowGL(canvas, opts = {}) {
  const quality = opts.quality === 'low' ? 'low' : 'high';
  let gl;
  try {
    gl = canvas.getContext('webgl2', {
      alpha: false,
      antialias: false,
      depth: false,
      stencil: false,
      powerPreference: 'high-performance',
    });
  } catch {
    gl = null;
  }
  if (!gl) return null;

  let base;
  let blade;
  let part;
  try {
    base = program(gl, VERT_FULL, FRAG_BASE, ['uShadow', 'uSharp', 'uDebug']);
    blade = program(gl, VERT_BLADE, FRAG_BLADE);
    part = program(gl, VERT_PART, FRAG_PART);
  } catch (e) {
    console.warn(e.message);
    return null;
  }

  const counts = COUNTS[quality];
  const rnd = mulberry32(20261004);

  // textures: 0 image, 1 mask, 2 wind noise
  const noiseTex = createWindNoiseGL(gl);
  const maskTex = gl.createTexture();
  const imgTex = gl.createTexture();
  let imgReady = false;
  let maxTex = gl.getParameter(gl.MAX_TEXTURE_SIZE);

  function setImage(img) {
    let src = img;
    const nw = img.naturalWidth || img.width;
    const nh = img.naturalHeight || img.height;
    if (nw > maxTex) {
      const c = document.createElement('canvas');
      c.width = maxTex;
      c.height = Math.round((nh * maxTex) / nw);
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      src = c;
    }
    const masks = masksFor(img);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, imgTex);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, src);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, maskTex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, MASK_W, MASK_H, 0, gl.RGBA, gl.UNSIGNED_BYTE, masks);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    gl.activeTexture(gl.TEXTURE2);
    gl.bindTexture(gl.TEXTURE_2D, noiseTex);
    imgReady = true;
  }

  // instance buffers
  const bladeData = new Float32Array(counts.blades * 4);
  for (let i = 0; i < bladeData.length; i++) bladeData[i] = rnd();
  const partData = new Float32Array(counts.particles * 4);
  for (let i = 0; i < partData.length; i++) partData[i] = rnd();

  function makeVao(data, divisor) {
    const vao = gl.createVertexArray();
    const buf = gl.createBuffer();
    gl.bindVertexArray(vao);
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 4, gl.FLOAT, false, 0, 0);
    gl.vertexAttribDivisor(0, divisor);
    gl.bindVertexArray(null);
    return { vao, buf };
  }
  const bladeVao = makeVao(bladeData, 1);
  const partVao = makeVao(partData, 1);
  const emptyVao = gl.createVertexArray();

  const wind = makeWindState();
  const wu = { uWOff: new Float32Array(4), uWVel: new Float32Array(4), uWMisc: new Float32Array(4), uWHeadT: 0 };
  const rect = {};
  const motion = new Float32Array([1, 1, 1, 1]);
  const state = {
    cssW: 1,
    cssH: 1,
    dpr: 1,
    anchored: opts.anchored !== false,
    sharp: quality === 'low' ? 0 : 0.22,
    bladesOn: true,
    particlesOn: true,
    debug: 0,
    lastTime: 0,
    drawCalls: 0,
  };

  function setMotion(reduced) {
    motion[0] = reduced ? 0.25 : 1; // wind amplitude
    motion[1] = reduced ? 0 : 1; // flutter
    motion[2] = reduced ? 0.25 : 1; // painted warp
    motion[3] = reduced ? 0 : 1; // particles and shaft breathing
  }

  /** Dev and checks: set the four motion scales directly (wind, flutter, warp, breathing). */
  function setMotionRaw(a, b, c, d) {
    motion[0] = a;
    motion[1] = b;
    motion[2] = c;
    motion[3] = d;
  }

  function resize(cssW, cssH, dpr) {
    state.cssW = cssW;
    state.cssH = cssH;
    state.dpr = dpr;
    const w = Math.max(1, Math.round(cssW * dpr));
    const h = Math.max(1, Math.round(cssH * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
  }

  function geometry() {
    if (state.anchored) {
      meadowRect(state.cssW, state.cssH, rect);
    } else {
      // plain cover, object-position 47.5% 50% (MeadowImage without `anchored`)
      const s = Math.max(state.cssW / MEADOW_IMAGE.aspect, state.cssH);
      rect.width = s * MEADOW_IMAGE.aspect;
      rect.height = s;
      rect.left = -0.475 * (rect.width - state.cssW);
      rect.top = -0.5 * (rect.height - state.cssH);
      rect.horizonY = rect.top + 0.455 * rect.height;
      rect.pathX = 0;
      rect.feetY = 0;
      rect.avatarPx = 0;
    }
    return rect;
  }

  function setCommon(pr, t) {
    const L = pr.loc;
    gl.useProgram(pr.p);
    gl.uniform4f(L.uRect, rect.left, rect.top, rect.width, rect.height);
    gl.uniform2f(L.uSize, state.cssW, state.cssH);
    gl.uniform1f(L.uDpr, state.dpr);
    gl.uniform1f(L.uHorizon, rect.horizonY);
    gl.uniform1f(L.uTime, t);
    gl.uniform4fv(L.uMotion, motion);
    gl.uniform1i(L.uImg, 0);
    gl.uniform1i(L.uMask, 1);
    gl.uniform1i(L.uWindNoise, 2);
    gl.uniform4fv(L.uWOff, wu.uWOff);
    gl.uniform4fv(L.uWVel, wu.uWVel);
    gl.uniform4fv(L.uWMisc, wu.uWMisc);
    gl.uniform1f(L.uWHeadT, wu.uWHeadT);
  }

  function render(t) {
    if (!imgReady) return;
    geometry();
    windState(t, wind);
    packWindUniforms(wind, wu);
    gl.viewport(0, 0, canvas.width, canvas.height);

    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, imgTex);
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, maskTex);
    gl.activeTexture(gl.TEXTURE2);
    gl.bindTexture(gl.TEXTURE_2D, noiseTex);

    gl.disable(gl.BLEND);
    setCommon(base, t);
    const hasShadow = state.anchored && rect.avatarPx > 0;
    if (hasShadow) {
      const wS = rect.avatarPx * 0.62;
      const hS = rect.avatarPx * 0.11;
      gl.uniform4f(base.loc.uShadow, rect.pathX, rect.feetY + 0.08 * hS, wS / 2, hS / 2);
    } else {
      gl.uniform4f(base.loc.uShadow, 0, 0, 0, 0);
    }
    gl.uniform1f(base.loc.uSharp, state.sharp);
    gl.uniform1f(base.loc.uDebug, state.debug);
    gl.bindVertexArray(emptyVao);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    let calls = 1;

    if (!state.debug) {
      gl.enable(gl.BLEND);
      if (state.bladesOn) {
        gl.blendFuncSeparate(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA, gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
        setCommon(blade, t);
        gl.bindVertexArray(bladeVao.vao);
        gl.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, 2 * BLADE_SEGMENTS + 1, counts.blades);
        calls++;
      }
      if (state.particlesOn && motion[3] > 0) {
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
        setCommon(part, t);
        gl.bindVertexArray(partVao.vao);
        gl.drawArraysInstanced(gl.POINTS, 0, 1, counts.particles);
        calls++;
      }
      gl.disable(gl.BLEND);
    }
    gl.bindVertexArray(null);
    state.drawCalls = calls;
    state.lastTime = t;
  }

  /** Render the gust strength as grey and read one pixel (css px). Used by the sync test (gate N8). */
  function readGust(xCss, yCss, t) {
    const prev = state.debug;
    state.debug = 1;
    render(t);
    const px = new Uint8Array(4);
    gl.readPixels(Math.round(xCss * state.dpr), Math.round(canvas.height - yCss * state.dpr - 1), 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
    state.debug = prev;
    return px[0] / 255;
  }

  function dispose() {
    try {
      gl.deleteTexture(noiseTex);
      gl.deleteTexture(maskTex);
      gl.deleteTexture(imgTex);
      gl.deleteBuffer(bladeVao.buf);
      gl.deleteBuffer(partVao.buf);
      gl.deleteVertexArray(bladeVao.vao);
      gl.deleteVertexArray(partVao.vao);
      gl.deleteVertexArray(emptyVao);
      gl.deleteProgram(base.p);
      gl.deleteProgram(blade.p);
      gl.deleteProgram(part.p);
      const lose = gl.getExtension('WEBGL_lose_context');
      if (lose) lose.loseContext();
    } catch {
      // already gone
    }
  }

  maxTex = Math.min(maxTex, 8192);
  return { gl, state, rect, counts, setImage, setMotion, setMotionRaw, resize, render, readGust, dispose, isReady: () => imgReady };
}
