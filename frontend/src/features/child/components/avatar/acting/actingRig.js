// WP4 glue: one object per loaded avatar scene that owns the mouth shaper, the stress detector, the
// speech head, the face accents and the studio blinker, and writes their output to the bones and
// morphs. ClipAvatar creates one and calls update() and apply() each frame; the modules it uses are
// pure and tested (tests/acting.test.mjs), this file is only the three.js wiring.
//
// Per frame, in ClipAvatar's order:
//   restore()  before the mixer      puts the ears back (the mixer skips unchanged bones)
//   update()   after lipRig.update   runs the shaper's results through stress, head and face
//   applyJaw() after update()        the jaw bone from the shaper
//   applyHead() after lookAt.update  speech head, neck and ears on top of the look-at
//
// Nothing is allocated per frame.

import { Euler, Quaternion, Vector3 } from 'three';
import { VI } from '../lipsync/visemes.js';
import { MouthShaper } from './mouthShaping.js';
import { StressDetector } from './stressDetector.js';
import { SpeechHead } from './speechHead.js';
import { FaceAccents } from './faceAccents.js';

const MOUTH_SMILE_NEUTRAL = 0.15; // the V2 resting mouth: a slight smile
const euler = new Euler(0, 0, 0, 'YXZ');
const delta = new Quaternion();
const JAW_AXIS = new Vector3(1, 0, 0);
const EAR_AXIS = new Vector3(0, 0, 1);
const jawTurn = new Quaternion();
const earTurn = new Quaternion();

// Optional face morphs (they arrive with the WP5 mesh). Lowercase candidates per output.
const FACE_MORPHS = {
  browUp: ['browup', 'brow_up', 'browouterup'],
  browInnerUp: ['browinnerup', 'brow_inner_up'],
  cheek: ['cheekpuff', 'cheek_puff'],
  mouthSmile: ['mouthsmile', 'mouth_smile'],
  ppJaw: ['pp_jaw', 'ppjaw'],
};

/** The mesh version: 2 once the WP5 mesh (it has a browUp morph) is loaded, else 1. */
export function detectMeshVersion(scene) {
  let version = 1;
  scene.traverse((obj) => {
    const dict = obj.morphTargetDictionary;
    if (!dict) return;
    for (const name of Object.keys(dict)) if (FACE_MORPHS.browUp.includes(name.toLowerCase())) version = 2;
  });
  return version;
}

function bindFace(scene) {
  const bound = { browUp: [], browInnerUp: [], cheek: [], mouthSmile: [], ppJaw: [] };
  scene.traverse((obj) => {
    const dict = obj.morphTargetDictionary;
    if (!dict || !obj.morphTargetInfluences) return;
    for (const [name, index] of Object.entries(dict)) {
      const key = name.toLowerCase();
      for (const out of Object.keys(bound)) if (FACE_MORPHS[out].includes(key)) bound[out].push({ mesh: obj, index });
    }
  });
  return bound;
}

function write(list, weight) {
  for (let i = 0; i < list.length; i++) list[i].mesh.morphTargetInfluences[list[i].index] = weight;
}

export class ActingRig {
  /**
   * @param {object} o
   * @param {object} o.scene the cloned avatar scene
   * @param {{head?: object, neck?: object, jaw?: object, jawRest?: object}} o.bones
   * @param {object} o.lipRig the LipsyncRig (this rig installs itself as its mouth shaper)
   * @param {() => number} [o.rng]
   */
  constructor({ scene, bones, lipRig, rng = Math.random }) {
    this.bones = bones;
    this.lipRig = lipRig;
    this.version = detectMeshVersion(scene);
    this.shaper = new MouthShaper({ version: this.version, audioPath: true });
    this.stress = new StressDetector();
    this.speechHead = new SpeechHead({ rng });
    this.face = new FaceAccents({ rng });
    this.faceBound = bindFace(scene);
    this.hasFaceMorphs = Object.values(this.faceBound).some((l) => l.length > 0);
    lipRig.shaper = this.shaper;

    this.earL = scene.getObjectByName('ear_L') ?? scene.getObjectByName('earL') ?? null;
    this.earR = scene.getObjectByName('ear_R') ?? scene.getObjectByName('earR') ?? null;
    this.earLBase = this.earL ? this.earL.quaternion.clone() : null;
    this.earRBase = this.earR ? this.earR.quaternion.clone() : null;
    this.earsApplied = false;

    this.onFrame = null; // dev: called at the end of every frame (mouthMetrics.js samples here)
    this.events = null; // dev: an array while a measurement runs (see mouthMetrics.js)
    this.perf = { n: 0, total: 0, max: 0 }; // dev: ms spent in update()
  }

  /** Put the ears back to what the mixer left, before the mixer runs. */
  restore() {
    if (!this.earsApplied) return;
    this.earsApplied = false;
    if (this.earL) this.earL.quaternion.copy(this.earLBase);
    if (this.earR) this.earR.quaternion.copy(this.earRBase);
  }

  /**
   * @param {number} dt seconds
   * @param {object} ctx
   * @param {object|null} ctx.lipsync the analysis result, or null
   * @param {number} ctx.open the level or synthetic opening, 0..1
   * @param {boolean} ctx.speaking
   * @param {boolean} ctx.reduced
   * @param {string} ctx.state idle | listening | speaking | thinking | oneshot | walk
   */
  update(dt, { lipsync, open, speaking, reduced, state }) {
    const t0 = performance.now();
    const level = lipsync ? lipsync.level : open;
    const ev = this.stress.update(dt, level, speaking);
    const accent = ev.accent;
    if (accent && this.events) this.events.push({ type: 'accent', t: t0, strength: ev.strength });

    const jaw = this.shaper.jaw;
    const head = this.speechHead;
    const nodsBefore = head.nods;
    head.update(dt, { speaking, level, jaw, accent, accentStrength: ev.strength, state, reduced });
    if (this.events && head.nods !== nodsBefore) this.events.push({ type: 'nod', t: t0, amp: head.nodAmp });

    const shown = this.lipRig.shown;
    const flashesBefore = this.face.flashes;
    const f = this.face.update(dt, { accent, accentStrength: ev.strength, jaw, pp: shown[VI.PP], aa: shown[VI.aa], level, speaking, reduced });
    if (this.events && this.face.flashes !== flashesBefore) this.events.push({ type: 'brow', t: t0, amp: this.face.flashAmp });
    if (this.hasFaceMorphs) {
      write(this.faceBound.browUp, f.browUp);
      write(this.faceBound.browInnerUp, f.browInnerUp);
      write(this.faceBound.cheek, f.cheek);
      write(this.faceBound.mouthSmile, MOUTH_SMILE_NEUTRAL);
    }
    // The PP_jaw corrective, only when the GLB has it (the current V2 mesh does not).
    if (this.faceBound.ppJaw.length) write(this.faceBound.ppJaw, this.shaper.ppJawMorph);

    // The blink rate follows what the avatar is doing.
    if (this.lipRig.blinker.setState) this.lipRig.blinker.setState(state === 'speaking' ? 'speaking' : state === 'thinking' ? 'thinking' : state === 'listening' ? 'listening' : 'idle');

    const ms = performance.now() - t0;
    const p = this.perf;
    p.n++;
    p.total += ms;
    if (ms > p.max) p.max = ms;
  }

  /** The jaw bone, from the shaper (or a forced opening 0..1 for the dev page). */
  applyJaw(forced = -1) {
    const { jaw, jawRest } = this.bones;
    if (!jaw) return;
    const angle = forced >= 0 ? forced * this.shaper.jawCfg.max : this.shaper.jaw;
    jaw.quaternion.copy(jawRest).multiply(jawTurn.setFromAxisAngle(JAW_AXIS, angle));
  }

  /** Speech head and neck on top of the look-at, ears on top of the clip. Call after lookAt.update. */
  applyHead() {
    const { head, neck } = this.bones;
    const h = this.speechHead;
    if (neck) {
      euler.set(h.neck.pitch, h.neck.yaw, h.neck.roll);
      neck.quaternion.multiply(delta.setFromEuler(euler));
    }
    if (head) {
      euler.set(h.head.pitch, h.head.yaw, h.head.roll);
      head.quaternion.multiply(delta.setFromEuler(euler));
    }
    if (this.earL) {
      this.earLBase.copy(this.earL.quaternion); // what the mixer left, restored before the next mixer run
      this.earL.quaternion.multiply(earTurn.setFromAxisAngle(EAR_AXIS, h.ears.l));
    }
    if (this.earR) {
      this.earRBase.copy(this.earR.quaternion);
      this.earR.quaternion.multiply(earTurn.setFromAxisAngle(EAR_AXIS, -h.ears.r));
    }
    this.earsApplied = true;
  }
}
