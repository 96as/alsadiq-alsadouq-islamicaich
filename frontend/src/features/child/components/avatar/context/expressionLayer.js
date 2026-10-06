// The expression layer's eyelid squint (SPEC-EXPERIENCE 6.4): the eyelids move part way toward the
// Blink clip's closed pose, so a smile reaches the eyes ("smiling eyes") and empathy softens them.
// Applied after the mixer; the clip's pose is put back before the mixer runs (restore()), for the same
// reason as the look-at: three only writes a bone when the blended value changed.
//
// The closed pose is read from the GLB's own Blink clip (the eyelid_X.quaternion track at 0.0667 s,
// the frame where the lids are shut), so it is right for this rig whatever the bone axes are.
// Without the bones or the clip the layer does nothing. The viseme side of the expression layer
// (smile, soft mouth, "ooh") goes through lipsyncRig.bias, not through bones.
//
// Nothing is allocated per frame.

import { Quaternion } from 'three';
import { CLIP } from '../avatarConfig.js';

const CLOSED_AT = 2 / 30; // the closed frame of the 12-frame Blink clip

const clean = (n) => n.replaceAll('.', '');

function sampleTrack(track, t) {
  const v = track.createInterpolant().evaluate(t);
  return new Quaternion(v[0], v[1], v[2], v[3]).normalize();
}

export class ExpressionLayer {
  /**
   * @param {object} root the avatar scene
   * @param {object[]} clips the GLB's animation clips
   */
  constructor(root, clips = []) {
    this.lids = []; // {bone, closed, base}
    this.applied = false;
    this.amount = 0;
    const blink = clips.find((c) => c.name === CLIP.blink);
    if (!blink) return;
    for (const side of ['L', 'R']) {
      const names = [`eyelid_${side}`, `eyelid.${side}`];
      let bone = null;
      root.traverse((o) => {
        if (!bone && o.isBone && names.some((n) => o.name === n || o.name === clean(n))) bone = o;
      });
      if (!bone) continue;
      const track = blink.tracks.find((t) => t.name === `${bone.name}.quaternion`);
      if (!track) continue;
      this.lids.push({ bone, closed: sampleTrack(track, CLOSED_AT), base: bone.quaternion.clone() });
    }
  }

  get ready() {
    return this.lids.length > 0;
  }

  restore() {
    if (!this.applied) return;
    this.applied = false;
    for (const l of this.lids) l.bone.quaternion.copy(l.base);
  }

  /** @param {number} amount 0..1 how far toward closed (the director already capped it at 0.35) */
  apply(amount) {
    this.amount = amount;
    if (amount <= 0.001 || this.lids.length === 0) return;
    for (const l of this.lids) {
      l.base.copy(l.bone.quaternion);
      l.bone.quaternion.slerp(l.closed, amount);
    }
    this.applied = true;
  }
}
