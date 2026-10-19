// Speech head, accent nods, micro-drift and ear flicks [MB 4, 5.1, 6.7]. Pure math: it returns
// Euler offsets in radians for the head and the neck; the caller post-multiplies them onto the
// bones after the mixer (the clips never key them), and zeroes everything for one-shots.
//
// Axes (the caller maps them to bones): pitch positive = chin down, yaw positive = to the
// character's left, roll positive = ear to the left shoulder.

import { HEAD } from './actingConfig.js';
import { SecondOrder, SineMix, between, clamp, damp, minJerk } from './dynamics.js';

const NOD_SETTLE = 0.15; // s to come back from the overshoot

/** Nod curve: down, back with a small overshoot past rest, settle. Positive = down. */
export function nodCurve(t, amp, down, back) {
  if (t <= 0) return 0;
  if (t < down) return amp * minJerk(t / down);
  const t2 = t - down;
  if (t2 < back) return amp * (1 - minJerk(t2 / back)) - amp * HEAD.nodOvershoot * Math.sin((t2 / back) * Math.PI) * 0.5;
  const t3 = t2 - back;
  if (t3 < NOD_SETTLE) return -amp * HEAD.nodOvershoot * 0.25 * (1 - minJerk(t3 / NOD_SETTLE));
  return 0;
}

export class SpeechHead {
  /**
   * @param {object} [opts]
   * @param {() => number} [opts.rng] [0,1); seed it in tests
   */
  constructor({ rng = Math.random, config } = {}) {
    this.cfg = { ...HEAD, ...config };
    const c = this.cfg;
    this.rng = rng;
    this.pitchMix = new SineMix(c.pitchHz, c.mix, rng);
    this.yawMix = new SineMix(c.yawHz, c.mix, rng);
    this.rollMix = new SineMix(c.rollHz, c.mix, rng);
    this.driftYawMix = new SineMix(c.driftHz, c.driftMix, rng);
    this.driftPitchMix = new SineMix(c.driftHz.map((h) => h * 1.37), c.driftMix, rng);
    this.time = 0;
    this.energy = 0; // E: the smoothed voice envelope
    this.blend = 0; // speech layer fade 0..1
    this.nodT = 99; // time since the current nod began
    this.nodAmp = 0;
    this.nodDown = 0.12;
    this.nodBack = 0.26;
    this.nextNod = 0; // earliest time for the next nod
    this.jawHeld = 0; // seconds the jaw has been above jawDampAt
    this.damp = 1;
    // Ear flicks: a spring on each ear, target kicked out then released.
    this.earL = new SecondOrder(c.earSpring.f, c.earSpring.z, c.earSpring.r);
    this.earR = new SecondOrder(c.earSpring.f, c.earSpring.z, c.earSpring.r);
    this.earTimer = between(c.earEvery, rng);
    this.earTarget = [0, 0];
    this.earOutLeft = [0, 0];
    this.nods = 0; // count, for tests
    this.flicks = 0;
    // Outputs (reused objects).
    this.head = { pitch: 0, yaw: 0, roll: 0 };
    this.neck = { pitch: 0, yaw: 0, roll: 0 };
    this.ears = { l: 0, r: 0 };
  }

  reset() {
    this.energy = 0;
    this.blend = 0;
    this.nodT = 99;
    this.damp = 1;
  }

  /** Kick a nod now (the accent already passed the gap check or `force` is set). */
  nod(strength = 1, force = false) {
    if (!force && this.time < this.nextNod) return false;
    const c = this.cfg;
    this.nodT = 0;
    this.nodAmp = c.nodMin + (c.nodMax - c.nodMin) * clamp(strength, 0, 1);
    this.nodDown = between(c.nodDown, this.rng);
    this.nodBack = between(c.nodBack, this.rng);
    this.nextNod = this.time + this.nodDown + this.nodBack + between(c.nodGap, this.rng);
    this.nods++;
    return true;
  }

  /**
   * @param {number} dt
   * @param {object} ctx
   * @param {boolean} ctx.speaking a clip is playing
   * @param {number} [ctx.level] loudness 0..1
   * @param {number} [ctx.jaw] current jaw angle in rad (the speech noise yields to a wide jaw)
   * @param {boolean} [ctx.accent] a stress accent this frame
   * @param {number} [ctx.accentStrength]
   * @param {string} [ctx.state] idle | listening | speaking | thinking | oneshot | walk
   * @param {boolean} [ctx.reduced] prefers-reduced-motion
   * @returns {{head: object, neck: object, ears: object}}
   */
  update(dt, { speaking, level = 0, jaw = 0, accent = false, accentStrength = 0.5, state = 'idle', reduced = false }) {
    const c = this.cfg;
    this.time += dt;
    const scale = reduced ? c.reducedScale : 1;

    // Voice envelope E.
    const target = speaking ? clamp(level, 0, 1) : 0;
    const tau = target > this.energy ? c.energyAttack : c.energyRelease;
    this.energy += (target - this.energy) * (1 - Math.exp(-dt / tau));
    this.blend = damp(this.blend, speaking ? 1 : 0, c.speakBlend, dt);

    // The speech noise yields a little while the jaw is wide, so a big aa does not wobble.
    if (jaw > c.jawDampAt) this.jawHeld = c.jawDampFor;
    else this.jawHeld = Math.max(0, this.jawHeld - dt);
    this.damp = damp(this.damp, this.jawHeld > 0 ? 1 - c.jawDampBy : 1, 20, dt);

    // Continuous speech head.
    const amp = (c.floor + (1 - c.floor) * this.energy) * this.blend * this.damp * scale;
    let pitch = this.pitchMix.at(this.time) * c.pitch * amp;
    let yaw = this.yawMix.at(this.time) * c.yaw * amp;
    let roll = this.rollMix.at(this.time) * c.roll * amp;

    // Micro-drift (the procedural layer): wanders, scaled by motion state.
    const dm = (c.driftMult[state] ?? 0) * scale;
    yaw += this.driftYawMix.at(this.time) * c.driftYaw * dm;
    pitch += this.driftPitchMix.at(this.time) * c.driftPitch * dm;

    // Accent nod (speaking only). The neck leads by one frame.
    if (accent && speaking && this.blend > 0.5) this.nod(accentStrength);
    this.nodT += dt;
    const nodHead = nodCurve(this.nodT, this.nodAmp, this.nodDown, this.nodBack) * scale;
    const nodNeck = nodCurve(this.nodT + c.nodNeckLead, this.nodAmp, this.nodDown, this.nodBack) * scale;

    const ns = c.neckShare;
    this.neck.pitch = pitch * ns + nodNeck * ns;
    this.neck.yaw = yaw * ns;
    this.neck.roll = roll * ns;
    this.head.pitch = pitch * (1 - ns) + nodHead * (1 - ns);
    this.head.yaw = yaw * (1 - ns);
    this.head.roll = roll * (1 - ns);

    // Ear flicks while idle-ish, one ear at a time.
    this.earTimer -= dt;
    if (this.earTimer <= 0 && !reduced && state !== 'oneshot' && state !== 'walk') {
      const side = this.rng() < 0.5 ? 0 : 1;
      this.earTarget[side] = between(c.earAmp, this.rng);
      this.earOutLeft[side] = c.earOut;
      this.earTimer = between(c.earEvery, this.rng);
      this.flicks++;
    }
    for (let s = 0; s < 2; s++) {
      if (this.earOutLeft[s] > 0) {
        this.earOutLeft[s] -= dt;
        if (this.earOutLeft[s] <= 0) this.earTarget[s] = 0;
      }
    }
    this.ears.l = this.earL.update(dt, this.earTarget[0]);
    this.ears.r = this.earR.update(dt, this.earTarget[1]);
    return this;
  }
}
