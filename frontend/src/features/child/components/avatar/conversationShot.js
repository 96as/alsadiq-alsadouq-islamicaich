// hotfix-2: the CONVERSATION SHOT. Majd said "Sadiq is still small" three times: the meadow page frames
// the whole body (about 57% of the stage), so his face is a small part of the screen. While he speaks
// or listens the camera now eases in from the full body to a head-and-chest shot, so the face (top of
// the ears to the chin) is at least 25% of the viewport height on every window from 2000x713 to 390x844.
//
// Nothing here guesses the face size. At mount it bounds the real head (the skinned vertices that the
// head, ear and jaw bones own, in the head bone's space), and every frame it projects a few hundred of
// those points to the screen and measures the face in pixels; if the measured face is under the floor the
// shot closes in a little more (a feedback correction), and the numbers are on the dev handle
// (controlRef.current.shot.metrics()) for the tests.
//
// The camera never tilts (the meadow picture behind is painted for a level camera): the shot only
// changes the world height the camera sees (zoom), where it looks vertically, and a sideways shift that
// keeps Sadiq on the same screen column (the path). The full-body framing (meadowFraming.js) is the
// shot's start and its end. Reduced motion cuts instead of easing.
import { Box3, MathUtils, Vector3 } from 'three';
import { FOV_DEG } from '../meadowFraming.js';

export const SHOT = {
  /** Target face height, as a share of the stage height (the floor is 25% of the viewport). */
  faceFrac: 0.42,
  /** The face may not be wider than this share of the stage width (a phone is narrower than the face is tall). */
  widthFrac: 0.8,
  /** The least the face may be, as a share of the viewport height; and the margin the feedback keeps over it. */
  floorFrac: 0.25,
  floorMargin: 1.08,
  /** Never ask for a face taller than this share of the room between the header and the controls. */
  usableFrac: 0.94,
  /** Where the face centre sits between the header and the controls (0 = header edge, 1 = controls edge). */
  centreAt: 0.5,
  /** Ease: 1/s for the zoom amount. About 1.2 s to settle. */
  rate: 2.6,
  /** Seconds the shot stays after speaking or listening stops, so a short gap does not pump the camera. */
  holdSec: 1.6,
  /** Bones whose vertices are "the face": the head, both ears, the jaw (names, dots stripped). */
  faceBones: ['head', 'ear_L', 'ear_R', 'jaw'],
};

const tanHalf = Math.tan((FOV_DEG * Math.PI) / 360);
const { clamp, damp, lerp } = MathUtils;
const smooth = (x) => x * x * (3 - 2 * x);

/** The camera height-of-view for a face of `facePx` pixels on a stage `h` px tall, when the face is `headH` world units tall. */
export function worldHeightFor(headH, facePx, h) {
  return (headH * h) / facePx;
}

/**
 * The full shot for the stage w x h (CSS px) and the viewport height viewH.
 * @param {object} fr computeFraming(w, h)
 * @param {{cy: number, h: number, w?: number}} head the face's centre height, height and width, world units
 * @param {number} boost the measured correction (1 = none)
 * @returns {{worldH: number, camY: number, facePx: number}}
 */
export function shotTarget(fr, w, h, viewH, head, boost = 1) {
  const usable = Math.max(40, h - fr.top - fr.bottom);
  let facePx = Math.max(SHOT.faceFrac * h, SHOT.floorFrac * SHOT.floorMargin * 1.1 * viewH) * boost;
  facePx = Math.min(facePx, usable * SHOT.usableFrac);
  // A face wider than it is tall (a phone) must still fit across the stage.
  if (head.w > 0) facePx = Math.min(facePx, ((SHOT.widthFrac * w) / head.w) * head.h);
  // Never zoom out from the full-body framing.
  const worldH = Math.min(worldHeightFor(head.h, facePx, h), fr.worldH);
  const yc = (fr.top + (h - fr.bottom - fr.top) * SHOT.centreAt) / h; // face centre, as a fraction of the stage from its top
  const camY = head.cy - (0.5 - yc) * worldH;
  return { worldH, camY, facePx: (head.h / worldH) * h };
}

/** The camera at zoom amount e (0 = the full-body framing, 1 = the shot). Mutates and returns `out`. */
export function shotCamera(fr, tgt, e, w, h, avatarX, out = {}) {
  const th = fr.tanHalf ?? tanHalf; // look-dev's lens (30 degrees) differs from the meadow framing's (32)
  const worldH = Math.exp(lerp(Math.log(fr.worldH), Math.log(tgt.worldH), e));
  out.worldH = worldH;
  out.x = avatarX - ((fr.pathX - w / 2) / h) * worldH; // Sadiq stays on the path's screen column
  out.y = lerp(fr.targetY, tgt.camY, e);
  out.z = worldH / (2 * th);
  // Look-dev's camera has a vertical lens shift that puts the 3D horizon on the painted one: `y` above is the height at
  // the middle row of the screen, so the camera itself sits (0.5 - horizon) of the view height above it. A level camera's
  // horizon is its principal row at any height or distance, so the painted horizon stays matched through the zoom.
  out.eyeY = fr.lensY == null ? out.y : out.y + (0.5 - fr.lensY) * worldH;
  return out;
}

/** The zoom amount's next value. With reduced motion it cuts. */
export function stepAmount(s, goal, dt, reduced) {
  return reduced ? goal : damp(s, goal, SHOT.rate, dt);
}

/** Skinned-mesh vertices owned by the face bones, bounded in the head bone's space. null when the model has none. */
export function faceBox(scene, headBone) {
  let box = null;
  const v = new Vector3();
  scene.traverse((o) => {
    if (box || !o.isSkinnedMesh || !o.skeleton) return;
    const bones = o.skeleton.bones;
    const hi = bones.indexOf(headBone);
    if (hi < 0) return;
    const norm = (n) => n.replaceAll('.', '');
    const face = new Set(bones.map((b, i) => (SHOT.faceBones.includes(norm(b.name)) ? i : -1)).filter((i) => i >= 0));
    const g = o.geometry;
    const si = g.attributes.skinIndex;
    const sw = g.attributes.skinWeight;
    const pos = g.attributes.position;
    if (!si || !sw || !pos) return;
    const toHead = o.skeleton.boneInverses[hi].clone().multiply(o.bindMatrix);
    const b = new Box3();
    const kept = []; // every vertex, in head space (thinned below)
    let n = 0;
    for (let i = 0; i < pos.count; i += 1) {
      let best = 0;
      let bw = -1;
      for (let k = 0; k < 4; k += 1) {
        const w = sw.getComponent(i, k);
        if (w > bw) {
          bw = w;
          best = si.getComponent(i, k);
        }
      }
      if (bw < 0.5 || !face.has(best)) continue;
      v.fromBufferAttribute(pos, i).applyMatrix4(toHead);
      b.expandByPoint(v);
      kept.push(v.x, v.y, v.z);
      n += 1;
    }
    if (n > 50) {
      // Keep at most about 700 points for the per-frame measure, always the extremes of each axis.
      const stride = Math.max(1, Math.floor(n / 700));
      const pts = [];
      for (let i = 0; i < n; i += stride) pts.push(kept[i * 3], kept[i * 3 + 1], kept[i * 3 + 2]);
      for (let ax = 0; ax < 3; ax += 1) {
        let lo = 0;
        let hi = 0;
        for (let i = 0; i < n; i += 1) {
          if (kept[i * 3 + ax] < kept[lo * 3 + ax]) lo = i;
          if (kept[i * 3 + ax] > kept[hi * 3 + ax]) hi = i;
        }
        pts.push(kept[lo * 3], kept[lo * 3 + 1], kept[lo * 3 + 2], kept[hi * 3], kept[hi * 3 + 1], kept[hi * 3 + 2]);
      }
      box = { box: b, mesh: o, face, count: n, points: new Float32Array(pts) };
    }
  });
  return box;
}

/** Eases the camera between the full body and the conversation shot, and measures the face. */
export class ConversationShot {
  constructor(scene, headBone) {
    this.head = headBone;
    this.fb = headBone ? faceBox(scene, headBone) : null;
    this.enabled = !!this.fb;
    this.amount = 0; // eased 0..1 (the raw amount; the camera uses smooth(amount))
    this.goal = 0;
    this.hold = 0;
    this.boost = 1;
    this.facePx = 0; // measured, this frame, stage px
    this.faceVp = 0; // measured, as a share of the viewport height
    this.cam = { worldH: 1, x: 0, y: 0, z: 1 };
    this.headH = 0.25;
    this.headCy = 0.6;
    this.tgt = { worldH: 1, camY: 0, facePx: 0 };
    this.headW = 0.3;
    this.pt = new Vector3(); // the face's points: in head space, then in the world, then projected
    this.world = new Float32Array(this.fb ? this.fb.points.length : 0); // this frame's world-space points
    this.first = false;
    this.viewH = 1;
    this.stageH = 1;
  }

  /** The face's world-space bounds this frame (call after the pose is final). Fills headH, headW, headCy (damped). */
  measureWorld(dt) {
    const { points } = this.fb;
    const { pt, world } = this;
    this.head.updateWorldMatrix(true, false);
    let lo = Infinity;
    let hi = -Infinity;
    let left = Infinity;
    let right = -Infinity;
    for (let i = 0; i < points.length; i += 3) {
      pt.set(points[i], points[i + 1], points[i + 2]).applyMatrix4(this.head.matrixWorld);
      world[i] = pt.x;
      world[i + 1] = pt.y;
      world[i + 2] = pt.z;
      if (pt.y < lo) lo = pt.y;
      if (pt.y > hi) hi = pt.y;
      if (pt.x < left) left = pt.x;
      if (pt.x > right) right = pt.x;
    }
    const k = this.first ? 1 - Math.exp(-4 * dt) : 1;
    this.headH += (hi - lo - this.headH) * k;
    this.headW += (right - left - this.headW) * k;
    this.headCy += ((hi + lo) / 2 - this.headCy) * k;
    this.first = true;
  }

  /** The face on the screen, in stage px, from the same points. Needs the camera's matrices current. */
  measureScreen(camera, stageH) {
    const { world, pt } = this;
    let lo = Infinity;
    let hi = -Infinity;
    for (let i = 0; i < world.length; i += 3) {
      pt.set(world[i], world[i + 1], world[i + 2]).project(camera);
      const y = (1 - pt.y) * 0.5 * stageH;
      if (y < lo) lo = y;
      if (y > hi) hi = y;
    }
    return { top: lo, bottom: hi, px: hi - lo };
  }

  /**
   * One frame. `want` is true while Sadiq speaks or listens with nothing else going on; `block` is true while
   * the hologram, the walk-in or thinking needs the whole body. Sets the camera. Returns the eased amount (0..1).
   */
  update({ dt, want, block, reduced, camera, fr, w, h, viewH, avatarX }) {
    if (!this.enabled) return 0;
    this.measureWorld(dt);
    this.viewH = viewH;
    this.stageH = h;
    if (block) this.hold = 0;
    else if (want) this.hold = SHOT.holdSec;
    else this.hold = Math.max(0, this.hold - dt);
    this.goal = !block && this.hold > 0 ? 1 : 0;
    this.amount = stepAmount(this.amount, this.goal, dt, reduced);
    if (this.amount < 0.0005) this.amount = this.goal === 0 ? 0 : this.amount;
    const e = reduced ? this.amount : smooth(clamp(this.amount, 0, 1));

    const head = { cy: this.headCy, h: this.headH, w: this.headW };
    this.tgt = shotTarget(fr, w, h, viewH, head, this.boost);
    shotCamera(fr, this.tgt, e, w, h, avatarX, this.cam);
    camera.position.set(this.cam.x, this.cam.eyeY, this.cam.z);
    camera.quaternion.identity();
    camera.updateMatrixWorld(true);

    // Measured, not guessed: the face the child sees, against the floor.
    const m = this.measureScreen(camera, h);
    this.facePx = m.px;
    this.faceTop = m.top;
    this.faceBottom = m.bottom;
    this.faceVp = m.px / viewH;
    if (e > 0.97 && this.goal === 1) {
      const floorPx = SHOT.floorFrac * SHOT.floorMargin * viewH;
      const usable = Math.max(40, h - fr.top - fr.bottom) * SHOT.usableFrac;
      if (m.px < floorPx && this.tgt.facePx < usable * 0.999) {
        this.boost = Math.min(this.boost * (floorPx / Math.max(m.px, 1)) * 1.01, 1.8);
      }
    }
    return e;
  }

  /** What the tests read: the measured face (px of the stage, share of the viewport) and the zoom. */
  metrics() {
    return {
      enabled: this.enabled,
      amount: this.amount,
      goal: this.goal,
      facePx: this.facePx,
      faceTop: this.faceTop,
      faceBottom: this.faceBottom,
      faceOfViewport: this.faceVp,
      stageH: this.stageH,
      viewH: this.viewH,
      boost: this.boost,
      headWorldH: this.headH,
      headWorldW: this.headW,
      camera: { ...this.cam },
    };
  }

  /** Exact: project the real skinned vertices of the face bones (slow, tests only). Stage px. */
  exactFace(camera, stageH) {
    const { mesh, face } = this.fb;
    const g = mesh.geometry;
    const si = g.attributes.skinIndex;
    const sw = g.attributes.skinWeight;
    const v = new Vector3();
    let lo = Infinity;
    let hi = -Infinity;
    mesh.skeleton.update();
    for (let i = 0; i < g.attributes.position.count; i += 1) {
      let best = 0;
      let bw = -1;
      for (let k = 0; k < 4; k += 1) {
        const w = sw.getComponent(i, k);
        if (w > bw) {
          bw = w;
          best = si.getComponent(i, k);
        }
      }
      if (bw < 0.5 || !face.has(best)) continue;
      mesh.getVertexPosition(i, v);
      v.applyMatrix4(mesh.matrixWorld).project(camera);
      const y = (1 - v.y) * 0.5 * stageH;
      lo = Math.min(lo, y);
      hi = Math.max(hi, y);
    }
    return { top: lo, bottom: hi, px: hi - lo };
  }
}
