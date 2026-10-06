// Dev only (imported by the preview page, never by the product). Measures what the child would see:
// the chin of the real mesh through SkinnedMesh.getVertexPosition (which applies morphs and
// skinning), the jaw, the closures, the head angles and the acting events, per frame.
//
//   const mm = new MouthMetrics(scene, acting, lipRig);   // finds the chin vertex once
//   mm.start();  ...frames...  const report = mm.stop();  // M1, M2, M4, M8, B4 numbers
//
// MOTION-BIBLE 6.6: the chin is "the lowest lower-lip vertex with the largest aa dy"; its drop is
// measured in the head's own frame so a nodding head does not count as an open mouth.

import { Matrix4, Quaternion, Vector3 } from 'three';
import { VI } from '../lipsync/visemes.js';

const HEAD_HEIGHT_M = 0.375; // chin to crown [M]
const SAT_FRACTION = 0.95;
const pct = (a, p) => {
  if (!a.length) return NaN;
  const s = [...a].sort((x, y) => x - y);
  return s[Math.min(s.length - 1, Math.max(0, Math.round(p * (s.length - 1))))];
};
const r = (v, d = 3) => (Number.isFinite(v) ? Number(v.toFixed(d)) : null);

export class MouthMetrics {
  constructor(scene, acting, lipRig) {
    this.scene = scene;
    this.acting = acting;
    this.lipRig = lipRig;
    this.mesh = null;
    this.vertex = -1;
    this.restPos = new Vector3();
    this.dir = new Vector3(0, -1, 0);
    this.cmPerRad = NaN;
    this.mPerUnit = NaN; // metres per head-local unit, from the head height (chin tip to crown = 0.375 m)
    this.rows = null;
    this.tmp = new Vector3();
    this.inv = new Matrix4();
    this.prevHead = new Quaternion();
    this.find();
  }

  find() {
    let best = null;
    this.scene.traverse((o) => {
      if (o.isSkinnedMesh && o.morphTargetDictionary && 'aa' in o.morphTargetDictionary && !best) best = o;
    });
    if (!best) return;
    this.mesh = best;
    const aaIndex = best.morphTargetDictionary.aa;
    const delta = best.geometry.morphAttributes.position?.[aaIndex];
    const pos = best.geometry.attributes.position;
    const skinI = best.geometry.attributes.skinIndex;
    const skinW = best.geometry.attributes.skinWeight;
    const jawBone = this.acting.bones.jaw;
    const jawIdx = jawBone ? best.skeleton.bones.indexOf(jawBone) : -1;
    // The vertex the aa shape pulls down the most, among those mostly weighted to the jaw bone or
    // lying in the lower half of the face (the lip vertices are weighted to the jaw only in part).
    let bestDy = 0;
    for (let i = 0; i < pos.count; i++) {
      let jawW = 0;
      for (let k = 0; k < 4; k++) if (skinI.getComponent(i, k) === jawIdx) jawW += skinW.getComponent(i, k);
      if (jawW < 0.3) continue;
      const dy = delta ? delta.getY(i) : 0;
      if (dy < bestDy) {
        bestDy = dy;
        this.vertex = i;
      }
    }
    this.calibrate();
  }

  /** Head-local position of the chin vertex right now (matrices are refreshed first). */
  chinLocal(out, vertex = this.vertex) {
    const { mesh } = this;
    const head = this.acting.bones.head;
    this.scene.updateMatrixWorld(true);
    mesh.skeleton.update();
    mesh.getVertexPosition(vertex, out);
    out.applyMatrix4(mesh.matrixWorld);
    this.inv.copy(head.matrixWorld).invert();
    return out.applyMatrix4(this.inv);
  }

  /** Rest position (jaw 0, morphs 0) and the direction the chin travels when the jaw opens. */
  calibrate() {
    if (!this.mesh || this.vertex < 0) return;
    const jaw = this.acting.bones.jaw;
    const keepJaw = jaw.quaternion.clone();
    const morphs = this.mesh.morphTargetInfluences.slice();
    this.mesh.morphTargetInfluences.fill(0);
    jaw.quaternion.copy(this.acting.bones.jawRest);
    this.chinLocal(this.restPos);
    this.calibrateScale();
    const q = new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), 0.3);
    jaw.quaternion.copy(this.acting.bones.jawRest).multiply(q);
    const open = this.chinLocal(new Vector3());
    const d = open.sub(this.restPos);
    this.cmPerRad = (d.length() * this.mPerUnit * 100) / 0.3;
    this.dir.copy(d.normalize());
    jaw.quaternion.copy(keepJaw);
    for (let i = 0; i < morphs.length; i++) this.mesh.morphTargetInfluences[i] = morphs[i];
  }

  /**
   * Metres per head-local unit. The head is 0.375 m from chin tip to crown (MOTION-BIBLE 6.6), so the
   * scale is that over the distance between the lowest jaw-weighted vertex and the highest vertex
   * mostly weighted to the head bone, both at the rest pose.
   */
  calibrateScale() {
    const { mesh } = this;
    const pos = mesh.geometry.attributes.position;
    const skinI = mesh.geometry.attributes.skinIndex;
    const skinW = mesh.geometry.attributes.skinWeight;
    const bones = mesh.skeleton.bones;
    const jawIdx = bones.indexOf(this.acting.bones.jaw);
    const headIdx = bones.indexOf(this.acting.bones.head);
    let tip = -1;
    let crown = -1;
    let tipY = Infinity;
    let crownY = -Infinity;
    for (let i = 0; i < pos.count; i++) {
      let jawW = 0;
      let headW = 0;
      for (let k = 0; k < 4; k++) {
        const bi = skinI.getComponent(i, k);
        if (bi === jawIdx) jawW += skinW.getComponent(i, k);
        if (bi === headIdx) headW += skinW.getComponent(i, k);
      }
      const y = pos.getY(i);
      if (jawW > 0.5 && y < tipY) {
        tipY = y;
        tip = i;
      }
      if (headW > 0.5 && y > crownY) {
        crownY = y;
        crown = i;
      }
    }
    const a = this.chinLocal(new Vector3(), tip);
    const b = this.chinLocal(new Vector3(), crown);
    this.mPerUnit = HEAD_HEIGHT_M / Math.max(1e-6, a.distanceTo(b));
  }

  start() {
    this.rows = [];
    this.acting.events = [];
    this.t0 = performance.now();
    const head = this.acting.bones.head;
    if (head) this.prevHead.copy(head.quaternion);
    this.prevT = this.t0;
  }

  /** Call once per frame, after the avatar has updated (ClipAvatar's loop, via the preview page). */
  sample() {
    if (!this.rows || !this.mesh || this.vertex < 0) return;
    const now = performance.now();
    const dt = (now - this.prevT) / 1000;
    this.prevT = now;
    const chin = this.chinLocal(this.tmp).sub(this.restPos).dot(this.dir) * this.mPerUnit * 100; // cm
    const head = this.acting.bones.head;
    const hq = head ? head.quaternion : this.prevHead;
    const omega = dt > 1e-4 ? (2 * Math.acos(Math.min(1, Math.abs(this.prevHead.dot(hq)))) * 180) / Math.PI / dt : 0;
    if (head) this.prevHead.copy(hq);
    const shown = this.lipRig.shown;
    this.rows.push({
      t: (now - this.t0) / 1000,
      dt,
      chin,
      jaw: this.acting.shaper.jaw,
      pp: shown[VI.PP],
      ppRaw: this.lipRig.target[VI.PP], // what the lip-sync asked for, before the rig's follow stage
      ppOut: this.acting.shaper.morph[VI.PP], // what is written to the PP morph
      aa: shown[VI.aa],
      aaWritten: this.acting.shaper.morph[VI.aa],
      omega,
      syncPhase: globalThis.__voice?.timeline?.phase,
      syncOffset: globalThis.__voice?.timeline?.offset,
      speaking: this.lipRig.live,
      active: this.lipRig.active,
    });
  }

  stop() {
    const rows = this.rows ?? [];
    const events = this.acting.events ?? [];
    this.rows = null;
    this.acting.events = null;
    const speakRows = rows.filter((x) => x.speaking);
    const voiced = speakRows.filter((x) => x.active);
    const chins = voiced.map((x) => x.chin);
    const jawMax = this.acting.shaper.jawCfg.max;
    const openVowel = speakRows.filter((x) => x.aa >= 0.5).map((x) => x.chin / 100 / HEAD_HEIGHT_M);
    const ppRows = speakRows.filter((x) => x.pp >= 0.3);
    const ppJawLimit = this.acting.shaper.ppJaw + 1e-3;
    const sec = (rows[rows.length - 1]?.t ?? 0) - (rows[0]?.t ?? 0);
    const nods = events.filter((e) => e.type === 'nod');
    const brows = events.filter((e) => e.type === 'brow');
    const accents = events.filter((e) => e.type === 'accent');
    const gaps = (list) => list.slice(1).map((e, i) => (e.t - list[i].t) / 1000);
    return {
      meshVersion: this.acting.version,
      vertex: this.vertex,
      cmPerRad: r(this.cmPerRad, 2),
      metersPerUnit: r(this.mPerUnit, 4),
      frames: rows.length,
      speakingFrames: speakRows.length,
      voicedFrames: voiced.length,
      seconds: r(sec, 2),
      fps: r(rows.length / Math.max(sec, 1e-3), 1),
      M1: {
        chinCm: { p50: r(pct(chins, 0.5), 2), p90: r(pct(chins, 0.9), 2), max: r(Math.max(...chins), 2) },
        underHalfCmShare: r(chins.filter((c) => c < 0.5).length / Math.max(1, chins.length), 3),
        saturationShare: r(voiced.filter((x) => x.jaw >= SAT_FRACTION * jawMax).length / Math.max(1, voiced.length), 3),
      },
      M2: { frames: openVowel.length, ratio: { p50: r(pct(openVowel, 0.5), 4), p90: r(pct(openVowel, 0.9), 4) } },
      M4: {
        ppFrames: ppRows.length,
        jawClampedShare: r(ppRows.filter((x) => x.jaw <= ppJawLimit).length / Math.max(1, ppRows.length), 3),
      },
      M8: {
        accents: accents.length,
        nods: nods.length,
        nodMinGapS: r(Math.min(...gaps(nods)), 2),
        nodAmpDeg: nods.length ? { min: r((Math.min(...nods.map((n) => n.amp)) * 180) / Math.PI, 1), max: r((Math.max(...nods.map((n) => n.amp)) * 180) / Math.PI, 1) } : null,
        browFlashes: brows.length,
        browMinGapS: r(Math.min(...gaps(brows)), 2),
        browPerAccent: r(brows.length / Math.max(1, accents.length), 2),
      },
      B4: { speakingOmegaGe2Share: r(speakRows.filter((x) => x.omega >= 2).length / Math.max(1, speakRows.length), 3) },
      perfMsPerFrame: r(this.acting.perf.total / Math.max(1, this.acting.perf.n), 4),
      perfMaxMs: r(this.acting.perf.max, 3),
      rows,
      events,
    };
  }
}
