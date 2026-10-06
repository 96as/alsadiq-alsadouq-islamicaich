// w3: the held web page window, as plain three.js objects (BEHAVIOUR-SPEC 6). The rig (HologramRig.js) places it;
// this owns what is on it: the three canvas tiles and their textures, the scroll, the reading gaze.
//
// Budget (6.10): one draw call (this mesh), no per-frame allocation, at most three texture uploads per content
// state, one upload or one canvas band per frame, JS well under 0.1 ms a frame once the page is drawn.
//
//   setModel(model)   the page model (contentFilter.buildPageModel): a skeleton, then results, none or the grown-up card
//   pump(dt)          every frame, even while closed: draws the next band or uploads the next tile
//   update(...)       while open: scroll physics, gaze, uniforms

import {
  CanvasTexture,
  Color,
  CustomBlending,
  DoubleSide,
  LinearFilter,
  LinearMipmapLinearFilter,
  Mesh,
  OneFactor,
  OneMinusSrcAlphaFactor,
  PlaneGeometry,
  ShaderMaterial,
  SRGBColorSpace,
  Vector4,
} from 'three';
import { HP } from '../../context/holoTimeline.js';
import { buildPageModel } from './contentFilter.js';
import { HOLO } from '../hologramConfig.js';
import { FONT, WIN, foundScroll, layoutPage, layoutSkeleton, scrollInfo } from './pageLayout.js';
import { TILE, drawTile, makeMeasure } from './pageRenderer.js';
import { createReadingGaze } from './readingGaze.js';
import { createScroll } from './scrollPhysics.js';
import { WEB_FRAG, WEB_VERT } from './webPageShader.js';

/** The window in model-local metres (0.24 x 0.32 m: 360 x 480 logical px at 1500 px per metre). */
export const WEB_SIZE = [0.24, 0.32];
export const TEX = { high: 2.5, low: 1.75, keepMs: 30000, fontWaitMs: 600 };

const FONT_PROBES = [
  ['600 21px "IBM Plex Sans Arabic"', 'مرحبا'],
  ['400 17px "IBM Plex Sans Arabic"', 'مرحبا'],
  ['600 21px "IBM Plex Sans Arabic"', 'Hello'],
  ['800 30px "Baloo Bhaijaan 2"', 'مرحبا Hello'],
];

const now = () => (typeof performance !== 'undefined' ? performance.now() : Date.now());

export class WebPagePanel {
  /**
   * @param {{lowTier?: boolean, core: Color, found: Color, plate: Color}} opts
   */
  constructor({ lowTier = false, core, found, plate }) {
    this.lowTier = lowTier;
    this.scale = lowTier ? TEX.low : TEX.high;
    this.canvasW = Math.round(WIN.w * this.scale);
    this.canvasH = Math.round((TILE.h + 2 * TILE.pad) * this.scale);

    this.tiles = [];
    for (let k = 0; k < TILE.count; k++) this.tiles.push({ canvas: null, ctx: null, tex: null, dirty: false });
    this.hasDom = typeof document !== 'undefined';
    // The textures exist from the start, so the shader compiles with all three samplers bound. A texture with no
    // image is skipped by three (it binds an empty one) until its first upload.
    this.U = {
      uTex0: { value: null },
      uTex1: { value: null },
      uTex2: { value: null },
      uScale: { value: this.scale },
      uCanvasH: { value: this.canvasH },
      uScroll: { value: 0 },
      uPageH: { value: WIN.view },
      uAlpha: { value: 0 },
      uWipe: { value: 1 },
      uGold: { value: 0 },
      uDim: { value: 0 },
      uLuma: { value: 0 },
      uRtl: { value: 0 },
      uSkel: { value: 0 },
      uShim: { value: 0 },
      uBarA: { value: 0 },
      uHlA: { value: 0 },
      uPulse: { value: 0 },
      uSharp: { value: lowTier ? 0.9 : 0.55 },
      uReady: { value: 0 },
      uHl: { value: new Vector4(0, 0, 0, 0) },
      uCore: { value: core.clone() },
      uFoundC: { value: found.clone() },
      uPlate: { value: plate.clone() },
    };
    if (this.hasDom) for (let k = 0; k < TILE.count; k++) this.makeTile(k);
    this.material = new ShaderMaterial({
      uniforms: this.U,
      vertexShader: WEB_VERT,
      fragmentShader: WEB_FRAG,
      transparent: true,
      depthWrite: false,
      blending: CustomBlending, // premultiplied alpha, like the library panel
      blendSrc: OneFactor,
      blendDst: OneMinusSrcAlphaFactor,
      blendSrcAlpha: OneFactor,
      blendDstAlpha: OneMinusSrcAlphaFactor,
      toneMapped: false,
      fog: false,
      side: DoubleSide,
    });
    this.mesh = new Mesh(new PlaneGeometry(1, 1), this.material);
    this.mesh.frustumCulled = false;
    this.mesh.renderOrder = 22;
    this.mesh.visible = false;

    this.scroll = createScroll();
    this.gaze = createReadingGaze();

    // content
    this.model = null; // the latest model set
    this.queue = []; // [{type: 'draw'|'up', k, band}]
    this.job = null; // the model and layout being drawn
    this.shown = null; // {model, layout, info} what the textures hold now
    this.needLayout = false;
    this.fontsOk = false;
    this.fontsLate = false;
    this.fontDeadline = 0;
    this.uploads = 0; // uploads since the last setModel (a test reads this)
    this.stats = { uploads: 0, bands: 0, maxBandMs: 0, maxUpMs: 0 };
    this.idleT = 0;
    this.released = false;
    this.warmStep = this.hasDom ? 0 : 99; // the first-use costs (fonts, canvas, JIT) are paid at idle, one step a frame

    // open state
    this.open = false;
    this.lastPage = 0;
    this.found = false;
    this.time = 0;
    this.pulseT = 0;
  }

  makeTile(k) {
    const t = this.tiles[k];
    const cv = document.createElement('canvas');
    cv.width = this.canvasW;
    cv.height = this.canvasH;
    t.canvas = cv;
    t.ctx = cv.getContext('2d');
    const tex = new CanvasTexture(cv);
    tex.colorSpace = SRGBColorSpace;
    tex.generateMipmaps = true;
    tex.minFilter = LinearMipmapLinearFilter;
    tex.magFilter = LinearFilter;
    tex.anisotropy = this.lowTier ? 4 : 8;
    t.tex = tex;
    this.U[`uTex${k}`].value = tex;
  }

  /** Load the two fonts the page uses (they are already requested by index.html). Waits at most 600 ms. */
  preload() {
    if (!this.hasDom || !document.fonts || this.fontsOk || this.fontDeadline) return;
    this.fontDeadline = now() + TEX.fontWaitMs;
    const loads = FONT_PROBES.map(([f, text]) => document.fonts.load(f, text));
    Promise.all(loads)
      .then(() => {
        this.fontsOk = true;
      })
      .catch(() => {
        this.fontsOk = true; // nothing more to wait for: the fallback font is used
      });
  }

  fontsReady() {
    if (!this.hasDom) return true;
    if (this.fontsOk) return true;
    if (!this.fontDeadline) this.preload();
    if (now() >= this.fontDeadline) {
      // Too slow: draw with system-ui now and draw again when the fonts do arrive.
      if (!this.fontsLate && document.fonts && document.fonts.ready) {
        this.fontsLate = true;
        document.fonts.ready.then(() => {
          this.fontsOk = true;
          if (this.shown && this.model) this.redraw();
        });
      }
      return true;
    }
    return false;
  }

  /** Draw the current model again (the fonts arrived late). */
  redraw() {
    const m = this.model;
    if (!m) return;
    this.model = null;
    this.setModel(m, true);
  }

  /** The page model changed (or is new). Cheap when the content is the same. */
  setModel(model, force = false) {
    if (!model) {
      this.model = null;
      return;
    }
    if (!force && this.model && this.model.id === model.id && this.model.key === model.key) return;
    this.model = model;
    this.warmStep = 99;
    this.queue.length = 0;
    this.job = null;
    this.needLayout = true;
    this.uploads = 0;
    this.released = false;
    this.idleT = 0;
  }

  /** True when a page is on the textures and the window can show something. */
  get ready() {
    return !!this.shown;
  }

  /** Plan the drawing of the current model: layout, then the bands and uploads (tiles from the bottom up, tile 0 last). */
  plan() {
    const model = this.model;
    const t0 = this.tiles[0];
    if (!model || !t0.ctx) {
      this.needLayout = false;
      return;
    }
    const measure = makeMeasure(t0.ctx);
    const layout = model.state === 'skeleton' ? layoutSkeleton(model, measure) : layoutPage(model, measure);
    this.job = { model, layout };
    const n = model.state === 'skeleton' ? 1 : Math.min(TILE.count, Math.max(1, Math.ceil(layout.atlasH / TILE.h)));
    for (let k = n - 1; k >= 0; k--) {
      for (let b = 0; b < TILE.bands; b++) this.queue.push({ type: 'draw', k, band: b });
      this.queue.push({ type: 'up', k, band: 0 });
    }
    this.needLayout = false;
  }

  /**
   * Pay the first-use costs while nobody is looking: the fonts' first glyphs, the canvas backing store, the layout and
   * drawing code. Each step is one frame's work and goes to tile 0 without showing anything. Runs only with no page.
   */
  warm() {
    const t = this.tiles[0];
    if (!t.ctx || this.released) {
      this.warmStep = 99;
      return;
    }
    const step = this.warmStep;
    if (step === 0) {
      if (!this.fontsReady()) return;
      this.warmStep = 1;
      return;
    }
    const measure = makeMeasure(t.ctx);
    const msg = {
      id: 'warm',
      q: 'warm',
      lang: 'ar',
      st: 'results',
      hl: 0,
      r: [
        { t: 'Hello', d: 'warm.example', s: 'Hello مرحبا' },
        { t: 'Hello', d: 'warm.example', s: 'Hello مرحبا' },
      ],
    };
    if (step === 1) {
      const m = buildPageModel({ id: 'warm', q: 'warm', lang: 'ar' });
      const lay = layoutSkeleton(m, measure);
      drawTile(t.ctx, 0, this.scale, lay, m, 0, TILE.bands);
    } else if (step === 2) {
      const m = buildPageModel(msg);
      const lay = layoutPage(m, measure);
      drawTile(t.ctx, 0, this.scale, lay, m, 0, TILE.bands);
    } else if (step === 3) {
      const m = buildPageModel(msg);
      const lay = layoutPage(m, measure);
      drawTile(t.ctx, 0, this.scale, lay, m, 1, TILE.bands);
      t.ctx.clearRect(0, 0, this.canvasW, this.canvasH);
    }
    this.warmStep = step + 1 > 3 ? 99 : step + 1;
  }

  /** One unit of work per frame: lay out, draw a band or upload a tile. Runs whether or not the window is showing. */
  pump(dt, visible) {
    if (visible) this.idleT = 0;
    else if (this.shown || this.job) {
      this.idleT += dt;
      if (this.idleT * 1000 > TEX.keepMs) this.release();
    }
    if (this.released && !this.model) return;
    if (this.warmStep < 99 && !this.model && !this.shown) {
      this.warm();
      return;
    }
    if (!this.needLayout && this.queue.length === 0) return;
    if (this.released) {
      this.released = false;
      this.ensureTiles();
    }
    if (this.needLayout) {
      if (!this.fontsReady()) return;
      this.plan();
      return; // the layout was this frame's work
    }
    const task = this.queue.shift();
    if (!task || !this.job) return;
    const t = this.tiles[task.k];
    const t0 = now();
    if (task.type === 'draw') {
      drawTile(t.ctx, task.k, this.scale, this.job.layout, this.job.model, task.band, TILE.bands);
      this.stats.bands += 1;
      this.stats.maxBandMs = Math.max(this.stats.maxBandMs, now() - t0);
    } else {
      t.tex.needsUpdate = true;
      this.uploads += 1;
      this.stats.uploads += 1;
      if (task.k === 0) this.commit();
    }
  }

  /** Tile 0 is on the GPU: the new page is now what the shader shows (the other tiles went up before it). */
  commit() {
    const { model, layout } = this.job;
    const info = layout.state === 'skeleton' ? { max: 0, pitch: 170, stops: [] } : scrollInfo(layout);
    const was = this.shown;
    this.shown = { model, layout, info };
    this.job = null;
    const sc = this.scroll;
    const sameSearch = was && was.model.id === model.id;
    // a new page starts at the top; a skeleton that turns into results keeps the clock (the reading goes on)
    const mode = sc.mode;
    const flicks = sc.flicks;
    sc.reset(info.max, info.pitch);
    if (sameSearch && mode !== 'idle' && mode !== 'found') {
      sc.mode = mode;
      sc.flicks = flicks;
    }
    if (this.found && layout.hl) sc.found(foundScroll(layout), sc.reduced);
    this.U.uSkel.value = layout.state === 'skeleton' ? 1 : 0;
    this.U.uPageH.value = layout.state === 'skeleton' ? WIN.view : layout.pageH;
    this.U.uRtl.value = model.rtl ? 1 : 0;
    this.U.uReady.value = 1;
    const hl = layout.hl;
    if (hl) this.U.uHl.value.set(hl.x - 3, hl.y - 3, hl.w + 6, hl.h + 6);
    else this.U.uHl.value.set(0, 0, 0, 0);
    this.gaze.reset(model.rtl);
  }

  ensureTiles() {
    if (!this.hasDom) return;
    for (let k = 0; k < TILE.count; k++) {
      const t = this.tiles[k];
      if (t.canvas && t.canvas.width !== this.canvasW) {
        t.canvas.width = this.canvasW;
        t.canvas.height = this.canvasH;
      }
      if (!t.tex) this.makeTile(k);
    }
  }

  /** Free the textures and the canvas memory (30 s after the window closed). The next search draws again. */
  release() {
    this.released = true;
    this.shown = null;
    this.job = null;
    this.queue.length = 0;
    this.needLayout = false;
    this.U.uReady.value = 0;
    for (const t of this.tiles) {
      if (!t.tex) continue;
      t.tex.dispose();
      if (t.canvas) {
        t.canvas.width = 1;
        t.canvas.height = 1;
      }
    }
    if (this.model) this.needLayout = true;
  }

  /** The window opens (the OPENING transition): scroll and gaze start from the top. */
  begin(reduced) {
    this.open = true;
    this.found = false;
    this.scroll.reduced = !!reduced;
    this.lastPage = 0;
    this.pulseT = 0;
    const s = this.shown;
    this.scroll.reset(s ? s.info.max : 0, s ? s.info.pitch : 170);
    this.scroll.read();
    this.gaze.reset(this.model ? this.model.rtl : s ? s.model.rtl : false);
  }

  /** The window closed. */
  end() {
    this.open = false;
    this.found = false;
    this.mesh.visible = false;
  }

  /**
   * Per frame while the window is up.
   * @param {number} dt
   * @param {object} holo timeline output (phase, foundT, page)
   * @param {object} e holoEnvelope output
   * @param {boolean} reduced
   */
  update(dt, holo, e, reduced) {
    this.time += dt;
    const U = this.U;
    const sc = this.scroll;
    const s = this.shown;
    sc.reduced = reduced;
    const reading = (holo.phase === HP.OPENING || holo.phase === HP.HOLD) && holo.foundT < 0;
    if (reading && sc.mode === 'idle') sc.read();
    // a page turn of the timeline is a flick of the page
    if (holo.page !== this.lastPage) {
      this.lastPage = holo.page;
      if (sc.flick()) this.gaze.onFlick();
    }
    // Found: the card goes to a quarter of the way down the viewport
    if (holo.foundT >= 0 && !this.found) {
      this.found = true;
      if (s && s.layout.hl) sc.found(foundScroll(s.layout), reduced);
    }
    sc.step(dt);
    this.gaze.step(dt, sc.pos, reading && !reduced);

    U.uScroll.value = sc.pos;
    U.uAlpha.value = e.alpha;
    U.uWipe.value = reduced ? 1 : e.wipe;
    U.uGold.value = e.gold;
    U.uDim.value = e.dim;
    U.uLuma.value = e.luma;
    U.uShim.value = reduced ? -5 : (this.time % 1.2) / 1.2;
    U.uBarA.value = reduced ? 0 : e.alpha * (this.found ? 0 : 0.9);
    U.uHlA.value = s && s.layout.hl ? e.gold : 0;
    U.uPulse.value = e.luma > 0 ? Math.min(1, e.luma / HOLO.found.flashLuma) : 0;
  }
}

export { FONT };
