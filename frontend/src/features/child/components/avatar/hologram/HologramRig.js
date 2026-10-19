// The search hologram as plain three.js objects (SPEC-EXPERIENCE section 7). No React, no per-frame
// allocation: every vector below is created once. ClipAvatar owns one rig and calls update() each
// frame with the timeline's output (context/holoTimeline.js).
//
//   beam      4 triangles (palm to the panel bottom edge), light-additive (no alpha write)
//   panel     1 quad, SDF glass plate + content in one draw call
//   halo      1 quad, premultiplied radial falloff
//   sparkles  Points (18 orbiting the rim, 14 for the burst)
//   icon      reduced motion only: one 128 x 128 canvas texture
// At most 4 draw calls (2 on the low tier: beam and panel), at most 300 triangles, no textures
// outside the reduced-motion icon.

import {
  ZeroFactor,
  BufferAttribute,
  BufferGeometry,
  CanvasTexture,
  Color,
  CustomBlending,
  DoubleSide,
  Group,
  Matrix4,
  Mesh,
  MeshBasicMaterial,
  OneFactor,
  OneMinusSrcAlphaFactor,
  PlaneGeometry,
  Points,
  Quaternion,
  ShaderMaterial,
  SRGBColorSpace,
  Vector2,
  Vector3,
} from 'three';
import { HP } from '../context/holoTimeline.js';
import { HOLO, SKIN_INDEX } from './hologramConfig.js';
import { holoEnvelope, makeEnvelope } from './holoEnvelope.js';
import { drawHoloIcon } from './holoIcon.js';
import {
  BEAM_FRAG,
  BEAM_VERT,
  HALO_FRAG,
  PANEL_FRAG,
  PANEL_VERT,
  SPARK_FRAG,
  SPARK_VERT,
} from './hologramShader.js';
import { WEB_SIZE, WebPagePanel } from './webPage/WebPagePanel.js'; // w3
import { heroRect, minJerk } from './webPage/heroLayout.js'; // w3

const UP = new Vector3(0, 1, 0);
const PANEL_PAD = 1.12; // must equal PAD in hologramShader.js
const WEB_OFFSET = [0.035, 0.19, 0.04]; // w3: the tall web window floats higher over the palm than the library panel
// avatar-integ: BEHAVIOUR-SPEC 6.3. When the GLB carries the P6 W clips (SearchScroll_W), the palm is raised and
// presented by the clip itself, so the window sits closer over it. Without the clips, WEB_OFFSET stays as it was.
const WEB_OFFSET_W = [0, 0.13, 0.03];
// w3 review: where SearchHold raises prop_L (measured in the meadow, avatar-local): the reduced-motion page's anchor
const REDUCED_WEB_ANCHOR = [0.29, 0.48, 0.175];

// Additive light that never writes alpha. The canvas is transparent and premultiplied, so an additive
// layer that wrote alpha 1 would show as an opaque dark rectangle over the page behind it.
const LIGHT_BLEND = {
  blending: CustomBlending,
  blendSrc: OneFactor,
  blendDst: OneFactor,
  blendSrcAlpha: ZeroFactor,
  blendDstAlpha: OneFactor,
};

const col = (hex) => new Color(hex); // sRGB hex into the linear working space

function mulberry(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function findNode(scene, names) {
  let found = null;
  scene.traverse((o) => {
    if (found || !o.name) return;
    for (const n of names) if (o.name === n || o.name === n.replaceAll('.', '')) found = o;
  });
  return found;
}

export class HologramRig {
  /**
   * @param {object} scene the avatar scene (to find prop_L, the hand and the head)
   * @param {{lowTier?: boolean}} [opts]
   */
  constructor(scene, { lowTier = false } = {}) {
    this.lowTier = lowTier;
    this.root = new Group();
    this.root.name = 'SearchHologram';
    this.root.visible = false;
    this.root.renderOrder = 20;
    this.env = makeEnvelope();
    this.rtl = true;
    this.warming = false;

    this.socket = findNode(scene, [HOLO.socketBone]);
    this.hand = findNode(scene, [HOLO.handBone, 'hand.l']);
    this.head = findNode(scene, [HOLO.headBone]);
    this.sceneRoot = scene;
    this.chain = this.buildChain(scene);
    this.invRoot = new Matrix4(); // the inverse of the root's world matrix, once per frame

    const C = HOLO.color;
    const core = col(C.core);
    const hi = col(C.highlight);
    const found = col(C.found);
    const foundHi = col(C.foundHighlight);
    const tints = C.folders.map((h) => col(h).lerp(core, C.folderToCore));

    const W = HOLO.size[0];
    const H = HOLO.size[1];
    this.W = W;
    this.H = H;

    // ---- panel ----
    this.panelU = {
      uTime: { value: 0 },
      uAlpha: { value: 0 },
      uWipe: { value: 1 },
      uGold: { value: 0 },
      uDim: { value: 0 },
      uLuma: { value: 0 },
      uStamp: { value: -1 },
      uPageT: { value: 9 },
      uPage: { value: 0 },
      uProgress: { value: 0 },
      uKind: { value: 2 },
      uPrevKind: { value: 2 },
      uKindMix: { value: 1 },
      uRtl: { value: 1 },
      uPlateA: { value: HOLO.plateAlpha },
      uPar: { value: new Vector2() },
      uCore: { value: core },
      uHi: { value: hi },
      uPlate: { value: col(C.plate) },
      uFound: { value: found },
      uFoundHi: { value: foundHi },
      uT0: { value: tints[0] },
      uT1: { value: tints[1] },
      uT2: { value: tints[2] },
    };
    const panelMat = new ShaderMaterial({
      uniforms: this.panelU,
      vertexShader: PANEL_VERT,
      fragmentShader: PANEL_FRAG,
      transparent: true,
      depthWrite: false,
      blending: CustomBlending, // premultiplied alpha: ONE, ONE_MINUS_SRC_ALPHA
      blendSrc: OneFactor,
      blendDst: OneMinusSrcAlphaFactor,
      blendSrcAlpha: OneFactor,
      blendDstAlpha: OneMinusSrcAlphaFactor,
      toneMapped: false,
      fog: false,
      side: DoubleSide,
    });
    this.panel = new Mesh(new PlaneGeometry(1, 1), panelMat);
    this.panel.frustumCulled = false;
    this.panel.renderOrder = 22;
    this.root.add(this.panel);

    // ---- w3: the held web page window (one more quad; the library panel is hidden while it shows) ----
    this.web = new WebPagePanel({ lowTier, core, found, plate: col(C.plate) });
    this.root.add(this.web.mesh);
    this.webOn = false;
    this.dW = W; // the plate's size this frame (the library panel's, or the window's)
    this.dH = H;
    this.off = HOLO.panelOffset;
    this.sm = 1; // hero scale multiplier
    this.hk = 0; // hero amount 0..1
    this.heroInit = false;
    this.heroTarget = new Vector3();
    this.heroSize = 1;
    this.hpos = new Vector3();
    this.hrect = { x: 0, y: 0, w: 0, h: 0, side: 1 };
    this.camW = new Vector3();
    this.gazeOn = false; // the head reads the page: a root-local point on the window
    this.gazePt = new Vector3();
    this.glance = 0; // 0..1 how much of the gaze is on the child instead
    this.webBlink = false;

    // ---- beam ----
    const beamPos = new Float32Array(12 * 3);
    const beamT = new Float32Array(12);
    for (let f = 0; f < 4; f++) {
      beamT[f * 3] = 0;
      beamT[f * 3 + 1] = 1;
      beamT[f * 3 + 2] = 1;
    }
    const beamGeo = new BufferGeometry();
    beamGeo.setAttribute('position', new BufferAttribute(beamPos, 3));
    beamGeo.setAttribute('aT', new BufferAttribute(beamT, 1));
    this.beamPos = beamPos;
    this.beamU = {
      uColor: { value: core.clone() },
      uTime: { value: 0 },
      uAmount: { value: 0 },
      uAlphaPalm: { value: HOLO.pyramid.alphaPalm },
      uAlphaPanel: { value: HOLO.pyramid.alphaPanel },
      uFlicker: { value: HOLO.pyramid.flicker },
    };
    const beamMat = new ShaderMaterial({
      uniforms: this.beamU,
      vertexShader: BEAM_VERT,
      fragmentShader: BEAM_FRAG,
      transparent: true,
      depthWrite: false,
      ...LIGHT_BLEND,
      toneMapped: false,
      fog: false,
      side: DoubleSide,
    });
    this.beam = new Mesh(beamGeo, beamMat);
    this.beam.frustumCulled = false;
    this.beam.renderOrder = 21;
    this.root.add(this.beam);

    // ---- halo and sparkles (not on the low tier) ----
    this.haloU = {
      uColor: { value: core.clone() },
      uIntensity: { value: 0 },
      uScale: { value: HOLO.halo.scale },
      uHS: { value: new Vector2(W / 2, H / 2) }, // w3
    };
    this.halo = new Mesh(
      new PlaneGeometry(1, 1),
      new ShaderMaterial({
        uniforms: this.haloU,
        vertexShader: PANEL_VERT,
        fragmentShader: HALO_FRAG,
        transparent: true,
        depthWrite: false,
        blending: CustomBlending, // premultiplied, like the panel (see HALO_FRAG)
        blendSrc: OneFactor,
        blendDst: OneMinusSrcAlphaFactor,
        blendSrcAlpha: OneFactor,
        blendDstAlpha: OneMinusSrcAlphaFactor,
        toneMapped: false,
        fog: false,
      }),
    );
    this.halo.frustumCulled = false;
    this.halo.renderOrder = 21;
    this.root.add(this.halo);

    const nSpark = HOLO.sparkles.orbit + HOLO.sparkles.burst;
    const rnd = mulberry(7);
    const seed = new Float32Array(nSpark * 4);
    const kind = new Float32Array(nSpark);
    for (let i = 0; i < nSpark; i++) {
      for (let k = 0; k < 4; k++) seed[i * 4 + k] = rnd();
      kind[i] = i < HOLO.sparkles.orbit ? 0 : 1;
    }
    const sparkGeo = new BufferGeometry();
    sparkGeo.setAttribute('position', new BufferAttribute(new Float32Array(nSpark * 3), 3));
    sparkGeo.setAttribute('aSeed', new BufferAttribute(seed, 4));
    sparkGeo.setAttribute('aKind', new BufferAttribute(kind, 1));
    this.sparkU = {
      uTime: { value: 0 },
      uOrbit: { value: 0 },
      uBurstT: { value: -1 },
      uBurstLife: { value: HOLO.sparkles.burstLife },
      uGravity: { value: HOLO.sparkles.gravity },
      uBurstSpeed: { value: HOLO.sparkles.burstSpeed },
      uPx: { value: 600 },
      uZ: { value: HOLO.z.sparkle },
      uCenter: { value: new Vector3() },
      uRight: { value: new Vector3(1, 0, 0) },
      uUp: { value: new Vector3(0, 1, 0) },
      uNormal: { value: new Vector3(0, 0, 1) },
      uBurstOrigin: { value: new Vector3() },
      uHalf: { value: new Vector2(W / 2, H / 2) },
      uColor: { value: core.clone() },
      uGoldColor: { value: found.clone() },
      uHiColor: { value: hi.clone() },
    };
    this.sparks = new Points(
      sparkGeo,
      new ShaderMaterial({
        uniforms: this.sparkU,
        vertexShader: SPARK_VERT,
        fragmentShader: SPARK_FRAG,
        transparent: true,
        depthWrite: false,
        ...LIGHT_BLEND,
        toneMapped: false,
        fog: false,
      }),
    );
    this.sparks.frustumCulled = false;
    this.sparks.renderOrder = 23;
    this.root.add(this.sparks);

    // ---- the reduced-motion icon ----
    this.iconKey = -1;
    this.icon = null;
    if (typeof document !== 'undefined') {
      const cv = document.createElement('canvas');
      cv.width = HOLO.icon.canvas;
      cv.height = HOLO.icon.canvas;
      this.iconCanvas = cv;
      const tex = new CanvasTexture(cv);
      tex.colorSpace = SRGBColorSpace;
      this.iconTex = tex;
      this.icon = new Mesh(
        new PlaneGeometry(1, 1),
        new MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, toneMapped: false, fog: false }),
      );
      this.icon.scale.setScalar(HOLO.icon.size);
      this.icon.position.set(HOLO.icon.pos[0], HOLO.icon.pos[1], HOLO.icon.pos[2]);
      this.icon.renderOrder = 24;
      this.icon.visible = false;
      this.root.add(this.icon);
    }

    // ---- placement state ----
    this.anchor = new Vector3(); // the spring-followed palm point
    this.anchorTarget = new Vector3();
    this.anchorInit = false;
    this.center = new Vector3();
    this.facing = new Quaternion();
    this.facingInit = false;
    this.pose = new Quaternion(); // facing + sway + twist
    this.right = new Vector3(1, 0, 0);
    this.up = new Vector3(0, 1, 0);
    this.normal = new Vector3(0, 0, 1);
    this.camLocal = new Vector3();
    this.headLocal = new Vector3();
    this.tmpA = new Vector3();
    this.tmpB = new Vector3();
    this.tmpC = new Vector3();
    this.tmpM = new Matrix4();
    this.tmpQ = new Quaternion();
    this.tmpQ2 = new Quaternion();
    this.safeShift = new Vector2();
    this.safeScale = 1;
    this.safeGoal = new Vector3(0, 0, 1); // w3 review: the web window's safe shift (x, y) and scale (z) it eases to
    this.webSafeT = 0;
    this.prevPhase = HP.CLOSED;
    this.viewW = -1; // the view size frame safety last ran for
    this.viewH = -1;
    this.time = 0;
    this.hasBeam = false;
  }

  /** Language: Arabic mirrors the layout (thumbnails and header bars on the right). */
  setRtl(rtl) {
    this.rtl = !!rtl;
    this.panelU.uRtl.value = rtl ? 1 : 0;
  }

  /**
   * Compile every shader once, hidden, so the first search does not hitch (section 7.7).
   * @param {{compileAsync?: Function, compile?: Function}} gl the WebGLRenderer
   */
  async warmUp(gl, scene, camera) {
    this.warming = true;
    this.root.visible = true;
    this.beam.visible = true;
    this.panel.visible = true;
    this.halo.visible = !this.lowTier;
    this.sparks.visible = !this.lowTier;
    this.panelU.uAlpha.value = 0;
    this.web.mesh.visible = true; // w3
    this.web.U.uAlpha.value = 0;
    this.web.preload();
    try {
      if (gl.compileAsync) await gl.compileAsync(scene, camera);
      else gl.compile(scene, camera);
    } catch {
      /* a failed warm-up only costs the first-use hitch */
    }
    this.warming = false;
    this.web.mesh.visible = false;
    this.root.visible = false;
  }

  /**
   * The nodes whose world matrices the rig needs (prop_L, the hand and the head, and every ancestor up to
   * the scene root), parents first. Built once; refreshChain() walks it once a frame, so reading three
   * positions costs one pass over about 16 nodes and not three walks up the skeleton (each of which
   * getWorldPosition repeats).
   */
  buildChain(scene) {
    const depth = new Map();
    for (const target of [this.socket, this.hand, this.head]) {
      let n = target;
      const up = [];
      while (n) {
        up.push(n);
        if (n === scene) break;
        n = n.parent;
      }
      if (!n) continue; // not under the scene root: never refreshed here
      up.forEach((node, i) => depth.set(node, up.length - 1 - i));
    }
    return [...depth.keys()].sort((a, b) => depth.get(a) - depth.get(b));
  }

  /** Recompose the local matrices of the chain and chain them down: the pose is final, the renderer has not run yet. */
  refreshChain() {
    const list = this.chain;
    for (let i = 0; i < list.length; i++) {
      const n = list[i];
      n.updateMatrix();
      if (n.parent) n.matrixWorld.multiplyMatrices(n.parent.matrixWorld, n.matrix);
      else n.matrixWorld.copy(n.matrix);
    }
  }

  /** World position of a node in the root's local space (the avatar's, before MODEL_SCALE). Needs refreshChain() this frame. */
  localOf(node, out) {
    const e = node.matrixWorld.elements;
    return out.set(e[12], e[13], e[14]).applyMatrix4(this.invRoot);
  }

  /**
   * @param {number} dt seconds
   * @param {object} holo the timeline output
   * @param {{camera: object, hasHold: boolean, reduced: boolean, viewW: number, viewH: number}} ctx
   */
  update(dt, holo, ctx) {
    if (this.warming) return;
    // w3: the held page draws in the background (one canvas band or one upload a frame), window up or not
    const wm = ctx.web || null;
    if (wm) this.web.setModel(wm);
    this.web.pump(dt, this.root.visible);
    const e = holoEnvelope(holo, this.env);
    const phase = holo.phase;
    const iconOn = phase === HP.ICON || phase === HP.ICON_CHECK;
    if (!e.visible && !iconOn) {
      if (this.webOn) this.closeWeb(); // w3
      this.root.visible = false;
      this.prevPhase = phase;
      this.anchorInit = false;
      return;
    }
    this.root.visible = true;
    this.time += dt;
    // w3: the timeline says this search shows the page (it latched when it opened, or late while it was still reading)
    let relatch = false;
    if (holo.web && !this.webOn && this.web.model) {
      this.webOn = true;
      relatch = true;
      this.web.begin(!!holo.reduced);
    } else if (!holo.web && this.webOn) this.closeWeb();
    const webOn = this.webOn;
    const dW = webOn ? WEB_SIZE[0] : this.W;
    const dH = webOn ? WEB_SIZE[1] : this.H;
    this.dW = dW;
    this.dH = dH;
    this.off = webOn ? (ctx.webClips ? WEB_OFFSET_W : WEB_OFFSET) : HOLO.panelOffset; // avatar-integ: W3 offset with the P6 W clips
    this.haloU.uHS.value.set(dW / 2, dH / 2);
    // The skeleton and the root are read as the last render left them (one frame, 16 ms, behind the pose; the
    // anchor spring below already lags by 60 ms, and root and hand come from the same pass so they agree).
    // Only the frame that snaps the anchor (the open) recomposes the chain, so it starts on the exact palm.
    if (!this.anchorInit) {
      this.root.updateWorldMatrix(true, false);
      this.refreshChain();
    }
    this.invRoot.copy(this.root.matrixWorld).invert();

    if (iconOn) {
      this.updateIcon(holo, ctx);
      this.beam.visible = false;
      this.panel.visible = false;
      this.halo.visible = false;
      this.sparks.visible = false;
      this.prevPhase = phase;
      return;
    }
    if (this.icon) this.icon.visible = false;
    this.panel.visible = !webOn && e.panel && e.alpha > 0.001;
    this.halo.visible = !this.lowTier && e.halo > 0.001;
    this.sparks.visible = !this.lowTier && (e.orbit > 0.01 || e.burstT >= 0);

    // ---- the anchor: the palm, followed by a critically damped spring ----
    this.hasBeam = false;
    const at = this.anchorTarget;
    if (this.socket) {
      this.localOf(this.socket, at);
      this.hasBeam = true;
    } else if (this.hand && ctx.hasHold) {
      this.localOf(this.hand, at);
      at.x += HOLO.fallbackOffset[0];
      at.y += HOLO.fallbackOffset[1];
      at.z += HOLO.fallbackOffset[2];
      this.hasBeam = true;
    } else {
      at.set(HOLO.virtualAnchor[0], HOLO.virtualAnchor[1], HOLO.virtualAnchor[2]);
    }
    // w3 review: reduced motion plays no SearchStart, so the palm stays at his waist and the page sat half behind his
    // arm and sweater. Hold it, still, where the raised palm would be: beside the left shoulder (BEHAVIOUR-SPEC 6.11).
    const reducedWeb = webOn && !!holo.reduced;
    if (reducedWeb) {
      at.set(REDUCED_WEB_ANCHOR[0], REDUCED_WEB_ANCHOR[1], REDUCED_WEB_ANCHOR[2]);
      this.hasBeam = false;
    }
    this.beam.visible = this.hasBeam && e.pyr > 0.001;
    const opening = phase === HP.OPENING && this.prevPhase !== HP.OPENING;
    if (!this.anchorInit || opening || (relatch && reducedWeb)) {
      this.anchor.copy(at);
      this.anchorInit = true;
      this.facingInit = false;
    } else {
      const k = 1 - 2 ** (-dt / HOLO.anchorHalfLife);
      this.anchor.lerp(at, k);
    }

    // ---- the panel centre and the facing ----
    const c = this.center;
    c.set(
      this.anchor.x + this.off[0] + this.safeShift.x,
      this.anchor.y + this.off[1] + this.safeShift.y,
      this.anchor.z + this.off[2],
    );
    this.faceTarget(ctx.camera, dt);
    // The hand floats: +-4 deg of yaw. It is also the parallax between the layers.
    const sway = webOn && holo.reduced ? 0 : Math.sin(this.time * Math.PI * 2 * HOLO.swayHz); // w3: still in reduced motion
    this.tmpQ.setFromAxisAngle(UP, HOLO.swayYaw * sway);
    this.pose.copy(this.facing).multiply(this.tmpQ);
    if (e.twist !== 0) {
      this.tmpQ2.setFromAxisAngle(this.normal.set(0, 0, 1), e.twist);
      this.pose.multiply(this.tmpQ2);
    }
    this.right.set(1, 0, 0).applyQuaternion(this.pose);
    this.up.set(0, 1, 0).applyQuaternion(this.pose);
    this.normal.set(0, 0, 1).applyQuaternion(this.pose);

    // Frame safety: at the open and when the view changes. (Two numbers, not a string key: a string
    // built here would be a per-frame allocation.)
    if (opening || relatch || ((ctx.viewW !== this.viewW || ctx.viewH !== this.viewH) && phase !== HP.CLOSED)) {
      this.viewW = ctx.viewW;
      this.viewH = ctx.viewH;
      this.frameSafety(ctx.camera, ctx.viewW / Math.max(ctx.viewH, 1));
      this.safeGoal.set(this.safeShift.x, this.safeShift.y, this.safeScale);
      this.webSafeT = 0;
    } else if (webOn && !holo.reduced && !ctx.scrollW) this.webSafety(dt, ctx, phase, holo.hero); // reduced motion: placed once, never moved; avatar-integ: frozen (shift and scale) while SearchScroll_W plays, the clip moves the palm
    const sc = this.safeScale;
    const toPalm = e.toPalm;
    let px = c.x + (this.anchor.x - c.x) * toPalm;
    let py = c.y + (this.anchor.y - c.y) * toPalm;
    let pz = c.z + (this.anchor.z - c.z) * toPalm;
    // w3: the hero hold takes the window out of the hand to the child (and back); a camera-facing pose, a bigger size
    this.hk = webOn ? holo.hero : 0;
    this.sm = 1;
    if (this.hk > 0.0005) {
      this.placeHero(this.hk, dt, ctx, sc, px, py, pz);
      px = this.hpos.x;
      py = this.hpos.y;
      pz = this.hpos.z;
    } else this.heroInit = false;
    if (webOn) c.set(px, py, pz); // the beam and the look-at read the centre where the window is
    const sm = this.sm;

    // ---- w3: the web window (replaces the library panel's plate while a page shows) ----
    if (webOn) {
      const M = this.web.mesh;
      M.visible = e.panel && e.alpha > 0.001;
      M.position.set(px, py, pz);
      M.quaternion.copy(this.pose);
      M.scale.set(dW * e.sx * sc * sm * PANEL_PAD, dH * e.sy * sc * sm * PANEL_PAD, 1);
      this.web.update(dt, holo, e, !!holo.reduced);
      const g = this.web.gaze;
      if (g.blink) this.webBlink = true;
      const reading = (phase === HP.OPENING || phase === HP.HOLD) && holo.foundT < 0 && !holo.reduced;
      this.gazeOn = reading;
      if (reading) {
        // the head's target: a point on the window (window px to root-local metres)
        const k = sc * sm;
        const lx = (g.x / 360 - 0.5) * dW * k;
        const ly = (0.5 - g.y / 480) * dH * k;
        this.gazePt.set(px + this.right.x * lx + this.up.x * ly, py + this.right.y * lx + this.up.y * ly, pz + this.right.z * lx + this.up.z * ly);
      }
      this.glance = Math.max(reading ? g.glance : 0, this.hk);
    } else {
      this.gazeOn = false;
      this.glance = 0;
    }

    // ---- panel ----
    const P = this.panel;
    P.position.set(px, py, pz);
    P.quaternion.copy(this.pose);
    P.scale.set(this.W * e.sx * sc * PANEL_PAD, this.H * e.sy * sc * PANEL_PAD, 1);
    const U = this.panelU;
    U.uTime.value = this.time % 600;
    U.uAlpha.value = e.alpha;
    U.uWipe.value = e.wipe;
    U.uGold.value = e.gold;
    U.uDim.value = e.dim;
    U.uLuma.value = e.luma;
    U.uStamp.value = e.stamp;
    U.uPageT.value = holo.pageT;
    U.uPage.value = holo.page;
    U.uProgress.value = Math.min(1, holo.total / HOLO.progressFill);
    U.uKind.value = SKIN_INDEX[holo.kind] ?? 2;
    U.uPrevKind.value = SKIN_INDEX[holo.prevKind] ?? 2;
    U.uKindMix.value = holo.kindMix;
    // The layers slide against each other: the content 4 mm behind the rim light, the lens in front.
    U.uPar.value.set(sway * 0.0042, Math.cos(this.time * 1.7) * 0.0016);

    // ---- beam: four triangles from the palm to the panel's bottom edge ----
    if (this.hk > 0.995) this.beam.visible = false; // w3: out in the child's hands, the beam is gone
    if (this.beam.visible) this.updateBeam(e, sc * sm);
    this.beamU.uTime.value = this.time % 600;
    this.beamU.uAmount.value = e.alpha * (1 - 0.5 * e.dim) * (1 - this.hk);
    this.beamU.uColor.value.copy(this.panelU.uCore.value).lerp(this.panelU.uFound.value, e.gold);

    // ---- halo and sparkles ----
    if (this.halo.visible) {
      const h = this.halo;
      h.position.set(px, py, pz).addScaledVector(this.normal, HOLO.z.plate - 0.004);
      h.quaternion.copy(this.pose);
      h.scale.set(dW * e.sx * sc * sm * HOLO.halo.scale, dH * e.sy * sc * sm * HOLO.halo.scale, 1);
      this.haloU.uIntensity.value = e.halo;
      this.haloU.uColor.value.copy(this.panelU.uCore.value).lerp(this.panelU.uFound.value, e.haloGold);
    }
    if (this.sparks.visible) {
      const S = this.sparkU;
      S.uTime.value = this.time % 600;
      S.uOrbit.value = e.orbit * (1 - 0.5 * e.dim);
      S.uBurstT.value = e.burstT;
      S.uCenter.value.set(px, py, pz);
      S.uRight.value.copy(this.right);
      S.uUp.value.copy(this.up);
      S.uNormal.value.copy(this.normal);
      S.uBurstOrigin.value.copy(this.anchor);
      S.uHalf.value.set((dW / 2) * e.sx * sc * sm, (dH / 2) * e.sy * sc * sm);
      S.uPx.value = ctx.pxPerUnit ?? 600;
    }
    this.prevPhase = phase;
  }

  /** The panel's facing: 70 percent toward the child, 30 percent toward Sadiq, tilted back 8 degrees. */
  faceTarget(camera, dt) {
    const c = this.center;
    const n = this.tmpA;
    const h = this.tmpB;
    camera.getWorldPosition(this.camLocal);
    this.camLocal.applyMatrix4(this.invRoot);
    n.copy(this.camLocal).sub(c).normalize();
    if (this.head) {
      this.localOf(this.head, this.headLocal);
      h.copy(this.headLocal).sub(c).normalize();
    } else h.set(0, 0, 1);
    n.lerp(h, HOLO.towardHead).normalize();
    // tilt back: the top edge leans away, so the normal rises
    const xz = Math.hypot(n.x, n.z);
    n.y += Math.tan(HOLO.tiltBack) * xz;
    n.normalize();
    const x = this.tmpC.crossVectors(UP, n);
    if (x.lengthSq() < 1e-6) x.set(1, 0, 0);
    x.normalize();
    const y = h.crossVectors(n, x);
    this.tmpM.makeBasis(x, y, n);
    this.tmpQ.setFromRotationMatrix(this.tmpM);
    if (!this.facingInit) {
      this.facing.copy(this.tmpQ);
      this.facingInit = true;
    } else this.facing.slerp(this.tmpQ, 1 - Math.exp(-HOLO.facingRate * dt));
  }

  updateBeam(e, sc) {
    const pos = this.beamPos;
    const A = this.anchor;
    const w = HOLO.pyramid.width * this.dW * e.sx * sc * 0.5;
    const d = HOLO.pyramid.depth * 0.5;
    const half = this.dH * e.sy * sc * 0.5;
    // The base midpoint: the bottom edge of the panel (at its current place).
    const bx = this.center.x - this.up.x * half;
    const by = this.center.y - this.up.y * half;
    const bz = this.center.z - this.up.z * half;
    const g = e.pyr;
    const r = this.right;
    const n = this.normal;
    // four base corners, grown from the palm by g
    for (let i = 0; i < 4; i++) {
      const sx = i === 0 || i === 1 ? 1 : -1;
      const sn = i === 0 || i === 3 ? 1 : -1;
      const cx = bx + r.x * w * sx + n.x * d * sn;
      const cy = by + r.y * w * sx + n.y * d * sn;
      const cz = bz + r.z * w * sx + n.z * d * sn;
      this.corner(i, A.x + (cx - A.x) * g, A.y + (cy - A.y) * g, A.z + (cz - A.z) * g);
    }
    for (let f = 0; f < 4; f++) {
      const o = f * 9;
      pos[o] = A.x;
      pos[o + 1] = A.y;
      pos[o + 2] = A.z;
      const a = this.cornerBuf;
      const i0 = f * 3;
      const i1 = ((f + 1) % 4) * 3;
      pos[o + 3] = a[i0];
      pos[o + 4] = a[i0 + 1];
      pos[o + 5] = a[i0 + 2];
      pos[o + 6] = a[i1];
      pos[o + 7] = a[i1 + 1];
      pos[o + 8] = a[i1 + 2];
    }
    this.beam.geometry.attributes.position.needsUpdate = true;
  }

  corner(i, x, y, z) {
    if (!this.cornerBuf) this.cornerBuf = new Float32Array(12);
    this.cornerBuf[i * 3] = x;
    this.cornerBuf[i * 3 + 1] = y;
    this.cornerBuf[i * 3 + 2] = z;
  }

  /**
   * Keep the panel on screen and off Sadiq's face (section 7.4). Runs at the open and on resize.
   * Projects the panel corners and the head's sphere to NDC and nudges the panel (shift, then scale).
   */
  frameSafety(camera, aspect, keep = false) {
    const S = HOLO.safety;
    if (!keep) {
      this.safeShift.set(0, 0);
      this.safeScale = 1;
    }
    if (!camera) return;
    const side = this.anchor.x >= (this.head ? this.headLocal.x : 0) ? 1 : -1; // the hand's side
    if (this.head) this.localOf(this.head, this.headLocal);
    // the head circle in NDC (x in aspect-corrected units)
    const hc = this.tmpA.copy(this.headLocal);
    this.root.localToWorld(hc);
    const wp = this.tmpB.copy(hc);
    wp.project(camera);
    const hx = wp.x * aspect;
    const hy = wp.y;
    const ro = this.tmpC.set(1, 0, 0).transformDirection(camera.matrixWorld).multiplyScalar(S.headRadius * 0.87);
    const edge = ro.add(hc).project(camera);
    // w3 review: the held page's re-check (keep) also keeps clear of his cheeks, which are wider than the head circle
    const hr = Math.hypot(edge.x * aspect - hx, edge.y - hy) * (keep ? 1.3 : 1);

    const hw = this.dW * 0.5; // w3: the window's size when a page shows
    const hh = this.dH * 0.5;
    const off = this.off;
    for (let it = 0; it < 8; it++) {
      let minX = 9;
      let maxX = -9;
      let minY = 9;
      let maxY = -9;
      for (let k = 0; k < 4; k++) {
        const sx = k < 2 ? 1 : -1;
        const sy = k % 2 === 0 ? 1 : -1;
        const v = this.tmpA;
        v.set(
          this.anchor.x + off[0] + this.safeShift.x + this.right.x * hw * sx * this.safeScale + this.up.x * hh * sy * this.safeScale,
          this.anchor.y + off[1] + this.safeShift.y + this.right.y * hw * sx * this.safeScale + this.up.y * hh * sy * this.safeScale,
          this.anchor.z + off[2] + this.right.z * hw * sx * this.safeScale + this.up.z * hh * sy * this.safeScale,
        );
        this.root.localToWorld(v);
        v.project(camera);
        const x = v.x * aspect;
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (v.y < minY) minY = v.y;
        if (v.y > maxY) maxY = v.y;
      }
      // the head circle against the rectangle
      const nx = Math.min(Math.max(hx, minX), maxX);
      const ny = Math.min(Math.max(hy, minY), maxY);
      const overlap = Math.hypot(nx - hx, ny - hy) < hr;
      const out = Math.max(maxX / aspect - S.ndcLimit, -minX / aspect - S.ndcLimit, maxY - S.ndcLimit, -minY - S.ndcLimit);
      if (keep && overlap && out > 0) {
        // w3 review: squeezed between his face and the screen edge: only a smaller window fits
        if (this.safeScale <= S.minScale) break;
        this.safeScale = Math.max(S.minScale, this.safeScale * 0.95);
      } else if (overlap && Math.abs(this.safeShift.x) < S.maxShift) {
        this.safeShift.x += 0.015 * side;
      } else if (out > 0) {
        if (maxX / aspect > S.ndcLimit) this.safeShift.x -= 0.015;
        else if (-minX / aspect > S.ndcLimit) this.safeShift.x += 0.015;
        this.safeScale = Math.max(S.minScale, this.safeScale * 0.95);
      } else break;
    }
  }

  /**
   * w3 review: the web window opens at the bloom, while the palm is still rising (SearchStart), so the open-time
   * safety above is for a hand that is about to move: on a phone the window then hung 13 to 17 css px off the right
   * edge for the whole search. While the page is held, check the placement every 0.25 s from where it is heading
   * (keep = true: a placement that is already safe is left alone, so it never wobbles) and ease to it in about 0.25 s.
   */
  webSafety(dt, ctx, phase, hero) {
    const g = this.safeGoal;
    if (ctx.camera && hero <= 0 && (phase === HP.OPENING || phase === HP.HOLD)) {
      this.webSafeT += dt;
      if (this.webSafeT >= 0.25) {
        this.webSafeT = 0;
        const sx = this.safeShift.x;
        const sy = this.safeShift.y;
        const ss = this.safeScale;
        this.safeShift.set(g.x, g.y);
        this.safeScale = g.z;
        this.frameSafety(ctx.camera, ctx.viewW / Math.max(ctx.viewH, 1), true);
        g.set(this.safeShift.x, this.safeShift.y, this.safeScale);
        this.safeShift.set(sx, sy);
        this.safeScale = ss;
      }
    }
    const f = 1 - Math.exp(-dt / 0.25);
    this.safeShift.x += (g.x - this.safeShift.x) * f;
    this.safeShift.y += (g.y - this.safeShift.y) * f;
    this.safeScale += (g.z - this.safeScale) * f;
  }

  /** w3: the window closed or the search turned out not to be a page. */
  closeWeb() {
    this.webOn = false;
    this.web.end();
    this.gazeOn = false;
    this.glance = 0;
    this.hk = 0;
    this.heroInit = false;
  }

  /**
   * w3: the hero hold (BEHAVIOUR-SPEC 6.6). k (0..1) blends the window from where it floats over the palm to a
   * rectangle held out to the child: portrait, centred below his mouth; landscape, beside him on the hand side
   * (heroLayout.heroRect). The rectangle is stage px, converted to a root-local point at the window's own depth, so
   * the window stays camera-facing and exactly the rectangle's size on screen. Writes this.hpos, this.sm and this.pose.
   */
  placeHero(k, dt, ctx, sc, bx, by, bz) {
    const cam = ctx.camera;
    const W = ctx.viewW;
    const H = ctx.viewH;
    this.hpos.set(bx, by, bz);
    if (!cam || !this.head || W < 2 || H < 2) return;
    const S = HOLO.safety;
    const P11 = cam.projectionMatrix.elements[5];
    cam.getWorldPosition(this.camW);
    // the head circle and the mouth, in stage px
    const hw = this.tmpA.copy(this.headLocal);
    this.root.localToWorld(hw);
    const hn = this.tmpB.copy(hw).project(cam);
    const hx = (hn.x * 0.5 + 0.5) * W;
    const hy = (0.5 - hn.y * 0.5) * H;
    const edge = this.tmpC.set(1, 0, 0).transformDirection(cam.matrixWorld).multiplyScalar(S.headRadius * 0.87).add(hw).project(cam);
    const hr = Math.hypot((edge.x - hn.x) * 0.5 * W, (edge.y - hn.y) * 0.5 * H);
    let mouthY = hy + 0.55 * hr;
    if (ctx.jaw) {
      ctx.jaw.getWorldPosition(this.tmpA);
      const jn = this.tmpA.project(cam);
      mouthY = Math.max(mouthY, (0.5 - jn.y * 0.5) * H + 0.3 * hr);
    }
    const an = this.tmpA.copy(this.anchor);
    this.root.localToWorld(an).project(cam);
    const side = an.x >= hn.x ? 1 : -1;
    const r = heroRect(W, H, { x: hx, y: hy, r: hr, mouthY }, side, this.hrect);
    // the rectangle's centre as a point at the window's depth (along the camera's forward axis)
    const bw = this.tmpA.set(bx, by, bz);
    this.root.localToWorld(bw);
    const fwd = this.tmpB.set(0, 0, -1).transformDirection(cam.matrixWorld);
    const d = Math.max(0.05, bw.sub(this.camW).dot(fwd));
    const dir = this.tmpC.set(((r.x + r.w / 2) / W) * 2 - 1, 1 - ((r.y + r.h / 2) / H) * 2, 0.5).unproject(cam).sub(this.camW).normalize();
    const target = dir.multiplyScalar(d / Math.max(0.2, dir.dot(fwd))).add(this.camW).applyMatrix4(this.invRoot);
    const rs = this.tmpA.setFromMatrixScale(this.root.matrixWorld).y || 1;
    const localH = (r.h * (2 * d)) / (P11 * H) / rs;
    const size = localH / (this.dH * sc);
    if (!this.heroInit) {
      this.heroTarget.copy(target);
      this.heroSize = size;
      this.heroInit = true;
    } else {
      const f = 1 - Math.exp(-14 * dt);
      this.heroTarget.lerp(target, f);
      this.heroSize += (size - this.heroSize) * f;
    }
    // the pose: the camera's own orientation (in the root's space), so the window faces the child square on
    this.root.getWorldQuaternion(this.tmpQ).invert().multiply(cam.quaternion);
    this.pose.slerp(this.tmpQ, k);
    this.right.set(1, 0, 0).applyQuaternion(this.pose);
    this.up.set(0, 1, 0).applyQuaternion(this.pose);
    this.normal.set(0, 0, 1).applyQuaternion(this.pose);
    // the way out: a straight lerp plus a small outward arc (a quarter of the distance, along the camera's right)
    const camRight = this.tmpA.set(1, 0, 0).applyQuaternion(this.tmpQ);
    const tx = this.heroTarget.x;
    const ty = this.heroTarget.y;
    const tz = this.heroTarget.z;
    const dist = Math.hypot(tx - bx, ty - by, tz - bz);
    const arc = r.side * 0.25 * dist * Math.sin(Math.PI * k);
    if (H >= W) {
      // portrait: drop first (down his side, under the mouth), then slide in and grow, so it never sweeps across the face
      const camUp = this.tmpB.set(0, 1, 0).applyQuaternion(this.tmpQ);
      const dx = tx - bx;
      const dy = ty - by;
      const dz = tz - bz;
      const dr = dx * camRight.x + dy * camRight.y + dz * camRight.z;
      const du = dx * camUp.x + dy * camUp.y + dz * camUp.z;
      const ky = minJerk(Math.min(1, k / 0.55));
      const kx = minJerk(Math.max(0, (k - 0.45) / 0.55));
      this.hpos.set(
        bx + dx * k + camRight.x * dr * (kx - k) + camUp.x * du * (ky - k),
        by + dy * k + camRight.y * dr * (kx - k) + camUp.y * du * (ky - k),
        bz + dz * k + camRight.z * dr * (kx - k) + camUp.z * du * (ky - k),
      );
      this.sm = 1 + (this.heroSize - 1) * kx;
      return;
    }
    this.hpos.set(bx + (tx - bx) * k + camRight.x * arc, by + (ty - by) * k + camRight.y * arc, bz + (tz - bz) * k + camRight.z * arc);
    this.sm = 1 + (this.heroSize - 1) * k;
  }

  updateIcon(holo, ctx) {
    const ic = this.icon;
    if (!ic) return;
    const key = (holo.icon === 2 ? 3 : (SKIN_INDEX[holo.kind] ?? 2)) + 1;
    if (key !== this.iconKey) {
      this.iconKey = key;
      drawHoloIcon(this.iconCanvas.getContext('2d'), holo.icon === 2 ? 'check' : holo.kind, HOLO.icon.canvas);
      this.iconTex.needsUpdate = true;
    }
    ic.visible = true;
    ic.material.opacity = holo.iconA;
    if (ctx.camera) {
      ic.quaternion.copy(ctx.camera.quaternion);
    }
  }

  dispose() {
    for (const m of [this.panel, this.beam, this.halo, this.sparks, this.icon]) {
      if (!m) continue;
      m.geometry.dispose();
      m.material.map?.dispose?.();
      m.material.dispose();
    }
    // w3: the page window's geometry, material and the three tile textures
    this.web.mesh.geometry.dispose();
    this.web.material.dispose();
    for (const t of this.web.tiles) t.tex?.dispose();
    // (the root stays attached: React owns it, and a StrictMode remount builds the meshes' GPU data again)
  }
}
