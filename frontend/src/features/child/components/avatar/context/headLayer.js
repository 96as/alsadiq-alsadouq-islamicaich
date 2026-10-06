// The head layer: small rotation offsets applied to the head bone AFTER the mixer and BEFORE the
// look-at. Today it carries the procedural nod. It has a marked spot for the speech-head and micro-
// drift offsets of the mouth-acting package (hk/06-mouth-acting, MOTION-BIBLE WP4), so both can sum
// here without fighting.
//
// Like the look-at it must put the clip's pose back before the mixer runs (restore()), because
// three's PropertyMixer only writes a bone when the blended value changed, so an offset multiplied
// onto last frame's offset would wind up. Order each frame:
//   lookAt.restore() -> headLayer.restore() -> mixer -> headLayer.apply() -> lookAt.update()
// (restore the layer applied last first: the look-at saved the pose that already had the nod in it.)
//
// Nothing is allocated per frame.

import { Euler, Quaternion } from 'three';

const euler = new Euler(0, 0, 0, 'YXZ');
const delta = new Quaternion();

export class HeadLayer {
  /** @param {object|null} head the head bone */
  constructor(head) {
    this.head = head || null;
    this.base = head ? head.quaternion.clone() : null;
    this.applied = false;
    // Offsets, radians. Other packages add to these before apply().
    this.pitch = 0; // + is a nod down (the procedural nod writes here)
    this.yaw = 0;
    this.roll = 0;
  }

  restore() {
    if (!this.applied) return;
    this.applied = false;
    if (this.head) this.head.quaternion.copy(this.base);
  }

  /** Multiply the current offsets onto the clip's pose. Call after the mixer. */
  apply() {
    // 06-mouth-acting: add speech-head and micro-drift offsets to this.pitch / yaw / roll just above.
    if (!this.head) return;
    this.base.copy(this.head.quaternion);
    if (this.pitch !== 0 || this.yaw !== 0 || this.roll !== 0) {
      euler.set(this.pitch, this.yaw, this.roll);
      this.head.quaternion.multiply(delta.setFromEuler(euler));
    }
    this.applied = true;
  }
}
