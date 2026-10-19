import { useEffect, useRef } from 'react';
import { computeFraming } from '../meadowFraming';
import { usePageVisible, useReducedMotion } from './quality';
import { avatarFilterCss } from './palette';
import { FLOWER_SPRING, REDUCED, WIND, makeWindState, screenGustWith, springStep, windState } from './wind/windField';
import { windNow } from './wind/windClock';

/**
 * The foreground strip: blades and a few flowers in front of the avatar's feet (Motion Bible 7.7).
 *
 * The avatar is its own canvas, so 3D grass can never pass in front of it. This is a 2D layer above it that
 * frames the character in the meadow: 20-40 blades along the bottom edge (tall at the sides, short in the
 * middle so the legs stay readable), 3-6 flowers on second-order springs, and a few big blurred stems at the
 * screen edge for depth. Blades lean 3-6 degrees with the same gust field as the rest of the nature layers
 * plus a 1 degree flutter; the strip never covers more than 30% of the avatar's legs.
 *
 * Everything is drawn from sprites built once (the blur is paid once), no per-frame allocation.
 *
 * props
 *   mode  'painted' (the lead's painting: its own wind clock, feet from the framing)
 *         'forest'  (the 3D forest: rt.shared.uTime is the clock, rt.screen holds the projected feet,
 *                    and the strip takes the avatar's time-of-day tint)
 *   rt    the forest runtime (forest mode only)
 */

const TAU = Math.PI * 2;
const DEG = Math.PI / 180;
const SPR_W = 64; // blade sprite size, px
const SPR_H = 256;
const BODY = 40; // blade width at the base inside the sprite, px
const HEAD = 64; // flower head sprite size, px

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

const smooth = (a, b, x) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

// Blade colour sets: root, mid, tip, rim light. Sunny lime to deep green, like the painting.
const BLADE_COLORS = [
  ['#0b3a2a', '#1d6a3a', '#8cc43c', '#d4f08a'],
  ['#0a3626', '#19623c', '#74b83e', '#c2e87c'],
  ['#0d402c', '#247444', '#a2d04a', '#e0f69a'],
  ['#082f24', '#145a38', '#62ac44', '#b0e082'],
  ['#12462a', '#2c8040', '#b6dc54', '#eafaa6'],
  ['#0a3a30', '#1c6a4a', '#7cc470', '#c6f0a4'],
];

const supportsFilter = (() => {
  try {
    const c = document.createElement('canvas').getContext('2d');
    return !!c && 'filter' in c;
  } catch {
    return false;
  }
})();

/** One blade drawn at rest: tapered, with a slight arch, a rim light and a midrib. Base at the bottom centre. */
function drawBladeSprite(ctx, cols, arch, blurPx) {
  const cx = SPR_W / 2;
  const pad = blurPx * 2;
  ctx.save();
  if (blurPx > 0 && supportsFilter) ctx.filter = `blur(${blurPx}px)`;
  const g = ctx.createLinearGradient(0, SPR_H - pad, 0, pad);
  g.addColorStop(0, cols[0]);
  g.addColorStop(0.45, cols[1]);
  g.addColorStop(1, cols[2]);
  const top = pad + 2;
  const base = SPR_H - pad * 0.2 + 4;
  const half = BODY / 2 - pad * 0.15;
  const tipX = cx + arch;
  // a real blade: the centre line arches toward the tip, the width tapers to a point (16 points a side)
  const path = new Path2D();
  const N = 16;
  const cxAt = (k) => cx + arch * k * k;
  const wAt = (k) => half * Math.pow(1 - k, 0.72) * (1 - 0.18 * k);
  path.moveTo(cx - half, base);
  for (let n = 1; n <= N; n += 1) {
    const k = n / N;
    path.lineTo(cxAt(k) - wAt(k), base - (base - top) * k);
  }
  for (let n = N - 1; n >= 0; n -= 1) {
    const k = n / N;
    path.lineTo(cxAt(k) + wAt(k), base - (base - top) * k);
  }
  path.closePath();
  ctx.fillStyle = g;
  ctx.fill(path);
  if (blurPx === 0) {
    // the sun side: a thin lighter band on the right edge, and a midrib
    ctx.clip(path);
    const rim = ctx.createLinearGradient(cx - half, 0, cx + half, 0);
    rim.addColorStop(0.55, 'rgba(255,255,255,0)');
    rim.addColorStop(1, cols[3]);
    ctx.globalAlpha = 0.55;
    ctx.fillStyle = rim;
    ctx.fillRect(0, 0, SPR_W, SPR_H);
    ctx.globalAlpha = 0.28;
    ctx.strokeStyle = cols[3];
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(cx, base);
    ctx.quadraticCurveTo(cx + arch * 0.05, base - (base - top) * 0.55, tipX, top + 6);
    ctx.stroke();
  }
  ctx.restore();
}

const FLOWERS = [
  { petal: '#ffffff', edge: '#e8e6ee', core: '#ffc940', n: 9, kind: 'bloom' },
  { petal: '#ff9fc4', edge: '#e0679a', core: '#ffe27a', n: 7, kind: 'bloom' },
  { petal: '#c9a8ff', edge: '#8d63d8', core: '#fff0a0', n: 6, kind: 'small' },
  { petal: '#ffd84a', edge: '#e8a516', core: '#ff9a1f', n: 10, kind: 'small' },
  { petal: '#f4f1e6', edge: '#cfc9b4', core: '#e8d98a', n: 14, kind: 'dandelion' },
];

function drawFlowerSprite(ctx, f) {
  const c = HEAD / 2;
  ctx.clearRect(0, 0, HEAD, HEAD);
  const pr = f.kind === 'dandelion' ? c * 0.8 : c * 0.62;
  for (let i = 0; i < f.n; i += 1) {
    const a = (i / f.n) * TAU;
    ctx.save();
    ctx.translate(c + Math.cos(a) * pr * 0.55, c + Math.sin(a) * pr * 0.55);
    ctx.rotate(a);
    const pg = ctx.createRadialGradient(0, 0, 0, pr * 0.3, 0, pr * 0.62);
    pg.addColorStop(0, f.petal);
    pg.addColorStop(1, f.edge);
    ctx.fillStyle = pg;
    ctx.beginPath();
    ctx.ellipse(0, 0, pr * 0.62, pr * (f.kind === 'dandelion' ? 0.16 : 0.3), 0, 0, TAU);
    ctx.fill();
    ctx.restore();
  }
  const cg = ctx.createRadialGradient(c - 2, c - 2, 1, c, c, pr * 0.36);
  cg.addColorStop(0, '#fff6c8');
  cg.addColorStop(0.4, f.core);
  cg.addColorStop(1, f.edge);
  ctx.fillStyle = cg;
  ctx.beginPath();
  ctx.arc(c, c, pr * 0.34, 0, TAU);
  ctx.fill();
}

let atlasCache = null;
function getAtlas() {
  if (atlasCache) return atlasCache;
  const blades = BLADE_COLORS.map((cols, i) => {
    const cv = document.createElement('canvas');
    cv.width = SPR_W;
    cv.height = SPR_H;
    drawBladeSprite(cv.getContext('2d'), cols, (i % 2 ? 1 : -1) * (4 + (i % 3) * 3), 0);
    return cv;
  });
  // the big edge stems: darker, wide, blurred once. Without ctx.filter (Safari) the blur is a stacked offset fill.
  const edge = [0, 1].map((i) => {
    const cv = document.createElement('canvas');
    cv.width = SPR_W;
    cv.height = SPR_H;
    const cx = cv.getContext('2d');
    const dark = i ? ['#0a3322', '#1a5c34', '#4f9a3c', '#8cc060'] : ['#08301f', '#175830', '#468e38', '#7ab45a'];
    if (supportsFilter) {
      drawBladeSprite(cx, dark, i ? 7 : -7, 7);
    } else {
      cx.globalAlpha = 0.34;
      [-3, 0, 3].forEach((o) => {
        cx.save();
        cx.translate(o, 0);
        drawBladeSprite(cx, dark, i ? 7 : -7, 0);
        cx.restore();
      });
    }
    return cv;
  });
  const heads = FLOWERS.map((f) => {
    const cv = document.createElement('canvas');
    cv.width = HEAD;
    cv.height = HEAD;
    drawFlowerSprite(cv.getContext('2d'), f);
    return cv;
  });
  atlasCache = { blades, edge, heads };
  return atlasCache;
}

/** Lay out the blades, flowers and edge stems for a stage of w x h css px. Deterministic. */
function layout(w, h, pathPx) {
  const r = rng(20261004);
  const nBlades = Math.round(Math.min(40, Math.max(20, w / 48)));
  const nFlowers = w < 600 ? 3 : w < 1100 ? 5 : 6;
  const cxn = Math.min(0.9, Math.max(0.1, pathPx / w));
  const blades = [];
  for (let i = 0; i < nBlades; i += 1) {
    // stratified across the width, then pulled toward the path so the centre is densest
    let u = (i + 0.5 + 1.1 * (r() - 0.5)) / nBlades;
    u = cxn + (u - cxn) * (0.78 + 0.22 * Math.abs(u - cxn) * 2);
    const side = smooth(0.08, 0.5, Math.abs(u - cxn)); // 0 at the avatar, 1 far to the side
    blades.push({
      x: u * w,
      u,
      hf: (0.5 + 0.5 * side) * (0.42 + 0.58 * r() * r() + 0.2 * r()), // share of the allowed height
      wf: 0.9 + 0.8 * r(),
      v: Math.floor(r() * BLADE_COLORS.length),
      stiff: r(),
      rest: (r() * 2 - 1) * 7 * DEG,
      swayHz: WIND.swayHzLo + (WIND.swayHzHi - WIND.swayHzLo) * r(),
      swayPh: TAU * r(),
      flHz: 3 + r(),
      flPh: TAU * r(),
      back: r() < 0.45,
    });
  }
  blades.sort((a, b) => a.hf - b.hf);
  const flowers = [];
  for (let i = 0; i < nFlowers; i += 1) {
    const u = Math.min(0.97, Math.max(0.03, cxn + ((i + 0.5) / nFlowers - 0.5) * 0.95 + (r() - 0.5) * 0.06));
    const k = Math.floor(r() * FLOWERS.length);
    flowers.push({
      x: u * w,
      u,
      hf: 0.55 + 0.4 * r(),
      kind: k,
      size: 0.8 + 0.5 * r(),
      sp: { init: false, y: 0, yd: 0, xp: 0 },
      preset: FLOWER_SPRING[FLOWERS[k].kind],
      ph: TAU * r(),
    });
  }
  const edges = [0.015, 0.075, 0.935, 0.985].map((u, i) => ({
    x: u * w,
    u,
    hf: 1.35 + 0.4 * r(),
    v: i % 2,
    wf: 1.9 + 0.7 * r(),
    hz: 0.25 + 0.15 * r(),
    ph: TAU * r(),
    flip: u < 0.5 ? -1 : 1,
  }));
  return { blades, flowers, edges };
}

export default function ForegroundStrip({ mode = 'painted', rt = null }) {
  const canvasRef = useRef(null);
  const reduced = useReducedMotion();
  const visible = usePageVisible();
  const reducedRef = useRef(reduced);
  const visibleRef = useRef(visible);
  useEffect(() => {
    reducedRef.current = reduced;
    visibleRef.current = visible;
  }, [reduced, visible]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const host = canvas && canvas.parentElement;
    if (!canvas || !host) return undefined;
    const ctx = canvas.getContext('2d');
    if (!ctx) return undefined;
    const atlas = getAtlas();
    const st = makeWindState();
    let L = null;
    let W = 0;
    let H = 0;
    let cssH = 0;
    let dpr = 1;
    let raf = 0;
    let last = 0;
    let lastFilter = '';
    let staticDirty = true;
    let timeOverride = null;
    const stat = { frames: 0, ms: 0, max: 0, blades: 0 };

    const measure = () => {
      const r = host.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) return;
      W = r.width;
      H = r.height;
      dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      cssH = Math.ceil(H * 0.27);
      canvas.style.height = `${cssH}px`;
      canvas.width = Math.round(W * dpr);
      canvas.height = Math.round(cssH * dpr);
      const fr = computeFraming(W, H);
      L = layout(W, H, fr.pathX);
      L.fr = fr;
      stat.blades = L.blades.length;
      staticDirty = true;
    };

    const draw = (t, dt) => {
      if (!L) return;
      const calm = reducedRef.current;
      windState(calm ? 0 : t, st);
      // the room the strip may use: the bottom 16% of the stage, and at most 30% of the legs (legs = 0.4 of the avatar)
      let feetY;
      let avatarPx;
      if (mode === 'forest' && rt && rt.screen && rt.screen.avatarPx > 0) {
        feetY = rt.screen.y;
        avatarPx = rt.screen.avatarPx;
      } else {
        feetY = L.fr.feetY;
        avatarPx = L.fr.avatarPx;
      }
      const maxH = Math.max(0.09 * H, Math.min(0.16 * H, H - feetY + 0.12 * avatarPx));
      const baseY = cssH + 4;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const gustAt = (u, lag) => (calm ? REDUCED.wind : screenGustWith(st, u, 1, lag));
      const lean = Math.cos(st.heading); // toward screen right, the way the fronts travel

      const bladeDraw = (b) => {
        const h = b.hf * maxH;
        const lag = WIND.tipLag * 0.55;
        const s = gustAt(b.u, lag);
        const deg = 3 + 3 * b.stiff;
        const ang =
          b.rest +
          (deg * s * lean) * DEG +
          (calm ? 0 : 1.2 * Math.sin(TAU * b.swayHz * t + b.swayPh) * (0.4 + 0.6 * s) * DEG) +
          (calm ? 0 : 1 * (0.3 + 0.7 * s) * Math.sin(TAU * b.flHz * t + b.flPh) * DEG);
        const c = Math.cos(ang);
        const sn = Math.sin(ang);
        const bw = Math.max(7, Math.min(20, W * 0.0095)) * b.wf * (SPR_W / BODY);
        ctx.setTransform(c * dpr, sn * dpr, -sn * dpr, c * dpr, b.x * dpr, baseY * dpr);
        ctx.drawImage(atlas.blades[b.v], -bw / 2, -h, bw, h + 4);
      };

      for (let i = 0; i < L.blades.length; i += 1) if (L.blades[i].back) bladeDraw(L.blades[i]);

      // flowers: the stem is a curve of fixed length, the head follows on a second-order spring
      const dts = Math.min(0.05, Math.max(0.001, dt));
      ctx.lineCap = 'round';
      for (let i = 0; i < L.flowers.length; i += 1) {
        const f = L.flowers[i];
        const sh = f.hf * maxH * 0.95;
        const s = gustAt(f.u, 0.12);
        const target = (calm ? 0.2 : s * 0.55 + 0.1 * Math.sin(TAU * 0.6 * t + f.ph)) * lean * sh * 0.42;
        const off = Math.max(-sh * 0.6, Math.min(sh * 0.6, calm ? target : springStep(f.sp, target, dts, f.preset.f, f.preset.z, f.preset.r)));
        const tx = f.x + off;
        const ty = baseY - Math.sqrt(Math.max(1, sh * sh - off * off));
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.strokeStyle = '#1f6a30';
        ctx.lineWidth = Math.max(2.4, W * 0.0024);
        ctx.beginPath();
        ctx.moveTo(f.x, baseY);
        ctx.quadraticCurveTo(f.x + off * 0.12, baseY - sh * 0.58, tx, ty);
        ctx.stroke();
        const hs = Math.max(20, Math.min(46, H * 0.056)) * f.size;
        const rot = Math.atan2(off, sh) * 1.2;
        const c = Math.cos(rot);
        const sn = Math.sin(rot);
        ctx.setTransform(c * dpr, sn * dpr, -sn * dpr, c * dpr, tx * dpr, ty * dpr);
        ctx.drawImage(atlas.heads[f.kind], -hs / 2, -hs / 2, hs, hs);
      }

      for (let i = 0; i < L.blades.length; i += 1) if (!L.blades[i].back) bladeDraw(L.blades[i]);

      // the big blurred edge stems, slow
      for (let i = 0; i < L.edges.length; i += 1) {
        const e = L.edges[i];
        const h = Math.min(0.27 * H, e.hf * maxH);
        const s = gustAt(e.u, 0.3);
        const ang = e.flip * 3 * DEG * 0.4 + (4 * Math.sin(TAU * e.hz * t + e.ph) * (0.3 + 0.7 * s) + 3 * s * lean) * DEG * (calm ? 0 : 1) * 1;
        const c = Math.cos(ang);
        const sn = Math.sin(ang);
        const bw = Math.max(26, Math.min(80, W * 0.034)) * e.wf * (SPR_W / BODY) * 0.5;
        ctx.setTransform(c * dpr, sn * dpr, -sn * dpr, c * dpr, e.x * dpr, baseY * dpr);
        ctx.globalAlpha = 0.93;
        ctx.drawImage(atlas.edge[e.v], -bw / 2, -h, bw, h + 4);
        ctx.globalAlpha = 1;
      }
    };

    const frame = (now) => {
      raf = requestAnimationFrame(frame);
      if (!visibleRef.current) return;
      const t = timeOverride != null ? timeOverride : mode === 'forest' && rt ? rt.shared.uTime.value : windNow(now);
      if (mode === 'forest' && rt) {
        const f = avatarFilterCss(rt.palette.avatar);
        if (f !== lastFilter) {
          lastFilter = f;
          canvas.style.filter = f === 'none' ? '' : f;
        }
      }
      if (reducedRef.current) {
        // one still frame, redrawn only on resize
        if (!staticDirty) return;
        staticDirty = false;
        draw(0, 0.016);
        return;
      }
      staticDirty = false;
      const dt = last ? (now - last) / 1000 : 0.016;
      last = now;
      const t0 = performance.now();
      draw(t, dt);
      const ms = performance.now() - t0;
      stat.frames += 1;
      stat.ms += ms;
      if (ms > stat.max) stat.max = ms;
    };

    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(host);
    raf = requestAnimationFrame(frame);

    if (import.meta.env.DEV) {
      window.__strip = {
        stat,
        setTime: (v) => {
          timeOverride = v;
        },
        draw: (t) => draw(t, 0.016),
        get layout() {
          return L;
        },
      };
    }
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      canvas.style.filter = '';
      if (import.meta.env.DEV) delete window.__strip;
    };
  }, [mode, rt]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      data-foreground-strip=""
      className="pointer-events-none absolute inset-x-0 bottom-0 z-[5] block w-full"
    />
  );
}
