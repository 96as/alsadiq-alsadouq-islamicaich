// Look-at: a subtle turn of the head and neck toward the camera, or the pointer on desktop.
// Owned by code and applied AFTER the mixer has posed the bones, on top of whatever the clip did
// (post-multiplied onto the local quaternion), so it never fights an animation. Angles are
// clamped to LOOK, which keeps the head clear of the collar. The model has no eye bones.
//
// Call restore() BEFORE the mixer runs. three's PropertyMixer only writes a bone when the blended
// value differs from the previous frame, so on a frame where the clip holds the head still the
// look-at turn would otherwise be multiplied onto last frame's turn and the head would wind up.
//
// Nothing is allocated per frame.

import { Euler, MathUtils, Quaternion } from 'three';
import { LOOK } from './avatarConfig.js';

const { clamp, damp } = MathUtils;

const euler = new Euler(0, 0, 0, 'YXZ');
const delta = new Quaternion();

export class LookAt {
  /**
   * @param {{head?: object, neck?: object}} bones three.js bones (either may be missing)
   * @param {{yawSign?: number, pitchSign?: number}} [opts] flip if a rig's local axes differ
   */
  constructor({ head, neck }, { yawSign = 1, pitchSign = 1 } = {}) {
    this.head = head || null;
    this.neck = neck || null;
    this.yawSign = yawSign;
    this.pitchSign = pitchSign;
    this.yaw = 0; // smoothed, total (head plus neck)
    this.pitch = 0;
    // What the mixer left on the bones this frame, before the turn was added (see restore()).
    this.headBase = this.head ? this.head.quaternion.clone() : null;
    this.neckBase = this.neck ? this.neck.quaternion.clone() : null;
    this.applied = false;
  }

  /** Put back the clip's pose from before the last update(), so the turn never accumulates. */
  restore() {
    if (!this.applied) return;
    this.applied = false;
    if (this.head) this.head.quaternion.copy(this.headBase);
    if (this.neck) this.neck.quaternion.copy(this.neckBase);
  }

  /**
   * @param {number} dt seconds
   * @param {number} x -1..1 where to look, across the screen (+1 = the viewer's right)
   * @param {number} y -1..1 where to look, up the screen (+1 = up)
   * @param {number} weight 0..1, how much of the look-at is allowed right now
   */
  update(dt, x, y, weight) {
    const tx = clamp(x * LOOK.pointerGain, -1, 1) * LOOK.yaw;
    const ty = clamp(y * LOOK.pointerGain, -1, 1);
    const tp = ty >= 0 ? -ty * LOOK.pitchUp : -ty * LOOK.pitchDown; // negative pitch looks up
    this.yaw = damp(this.yaw, tx, LOOK.rate, dt);
    this.pitch = damp(this.pitch, tp, LOOK.rate, dt);
    const yaw = this.yaw * weight * this.yawSign;
    const pitch = this.pitch * weight * this.pitchSign;
    if (this.neck) {
      this.neckBase.copy(this.neck.quaternion);
      euler.set(pitch * (1 - LOOK.headShare), yaw * (1 - LOOK.headShare), 0);
      this.neck.quaternion.multiply(delta.setFromEuler(euler));
    }
    if (this.head) {
      this.headBase.copy(this.head.quaternion);
      euler.set(pitch * LOOK.headShare, yaw * LOOK.headShare, 0);
      this.head.quaternion.multiply(delta.setFromEuler(euler));
    }
    this.applied = true;
  }
}
