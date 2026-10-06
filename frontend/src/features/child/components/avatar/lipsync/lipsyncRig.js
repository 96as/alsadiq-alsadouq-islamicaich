// Everything the avatar needs from lip-sync in one object per loaded scene: the bound morph
// targets, the blink scheduler, and the per-frame write. useAvatarMotion creates one and calls
// update() each frame; the dev page does the same, so both exercise the same code.
//
// If the scene has no viseme morphs (today's avatar-web.glb) `hasVisemes` is false, update()
// writes nothing to the mouth and the caller keeps driving the jaw bone as before.

import { StudioBlinkScheduler } from '../acting/blinkTiming.js'; // WP4: gamma-interval blinks
import { JAW_WITH_VISEMES } from './lipsyncConfig.js';
import { applyBlink, applyVisemes, bindMorphTargets, resetMorphs } from './morphTargets.js';
import { VISEME_COUNT, VISEME_GAIN, VI } from './visemes.js';

const UNIT_GAINS = Object.freeze({}); // WP4: no further gain on the shaper's output
const damp = (a, b, rate, dt) => b + (a - b) * Math.exp(-rate * dt);

/**
 * Rate at which the mouth follows live weights and the fallback. The live weights are already
 * smoothed, so this stage only softens the hand-over from the fallback. Keep it fast: every
 * stage adds lag (see SMOOTHING.preRate).
 */
export const LIVE_RATE = 120;
export const FALLBACK_RATE = 16;

export class LipsyncRig {
  /**
   * @param {object} scene the cloned avatar scene (anything with traverse())
   * @param {{morphNames?: object, blinkNames?: string[], rng?: () => number, meshGain?: object}} [opts]
   *   meshGain: per-viseme gain already baked into the mesh; the web gain is divided by it.
   */
  constructor(scene, { morphNames, blinkNames, rng, meshGain } = {}) {
    this.binding = bindMorphTargets(scene, { morphNames, blinkNames });
    // The gain table written to the morphs when there is no shaper: VISEME_GAIN, with what the mesh
    // already applies divided out. (With the WP4 shaper, its own per-version table is used instead.)
    this.gains = { ...VISEME_GAIN };
    if (meshGain) for (const k in meshGain) this.gains[k] = (VISEME_GAIN[k] ?? 1) / meshGain[k];
    this.blinker = new StudioBlinkScheduler({ rng }); // WP4
    this.shaper = null; // WP4: set by ActingRig, writes the morphs with gain, cap and open budget
    this.shown = new Float32Array(VISEME_COUNT);
    this.shown[VI.sil] = 1;
    this.target = new Float32Array(VISEME_COUNT);
    this.lastPhraseEnds = 0;
    this.bias = new Float32Array(VISEME_COUNT); // 06-avatar-context: added to the target before smoothing
    this.active = false;
    this.live = false; // true while the last frame used real analysis
    this.blinkCtx = { stress: 0, reduced: false }; // reused every frame
  }

  /** True when the scene has viseme morph targets, so the mouth is driven here, not by the jaw. */
  get hasVisemes() {
    return this.binding.hasVisemes;
  }

  get hasBlink() {
    return this.binding.hasBlink;
  }

  /** 0..1 factor for the jaw bone: 1 without viseme morphs, JAW_WITH_VISEMES with them. */
  get jawScale() {
    return this.binding.hasVisemes ? JAW_WITH_VISEMES : 1;
  }

  /**
   * @param {number} dt seconds
   * @param {object} ctx
   * @param {object|null} ctx.lipsync result of getLipsync(), or null when there is no analysis
   * @param {number} ctx.open 0..1 jaw opening from the level or synthetic path (the fallback)
   * @param {boolean} ctx.speaking the agent is speaking
   * @param {boolean} ctx.reduced prefers-reduced-motion
   * @returns {number} the blink weight written (0 when there is no blink morph)
   */
  update(dt, { lipsync, open, speaking, reduced }) {
    const { shown, target } = this;
    const live = Boolean(lipsync);
    this.live = live;

    if (this.binding.hasVisemes) {
      if (live) {
        target.set(lipsync.weights);
      } else {
        // No analysis (no source, or the audio context is still suspended): open and close with
        // the level or the synthetic wave, on the "aa" shape with a little rounding.
        target.fill(0);
        const o = speaking ? open : 0;
        target[VI.aa] = 0.75 * o;
        target[VI.O] = 0.12 * o;
        target[VI.sil] = 1 - target[VI.aa] - target[VI.O];
      }
      // 06-avatar-context: the expression layer's 14 viseme offsets (smile, soft mouth, "ooh"); all 0 by default.
      const bias = this.bias;
      for (let i = 0; i < VISEME_COUNT; i++) target[i] = Math.min(1, target[i] + bias[i]);
      const rate = live ? LIVE_RATE : FALLBACK_RATE;
      for (let i = 0; i < VISEME_COUNT; i++) shown[i] = damp(shown[i], target[i], rate, dt);
      if (this.shaper) {
        // WP4: the shaper owns the gains, caps and the open budget, and the jaw angle.
        const level = live ? lipsync.level : open;
        const active = live ? Boolean(lipsync.active) : speaking && open > 0.1;
        this.active = active; // WP4: read by the dev metrics
        // [MB 6.3] The vowel, stress and PP holds are for the audio-only path. While a text timeline
        // drives the mouth (more than half mixed in) the timeline's own closures and holds are used.
        this.shaper.audioPath = !(live && lipsync.timed > 0.5);
        const morph = this.shaper.update(dt, shown, { level, stress: live ? lipsync.stress : 0, speaking, active });
        applyVisemes(this.binding, morph, UNIT_GAINS);
      } else {
        applyVisemes(this.binding, shown, this.gains);
      }
    }

    // Blink.
    if (lipsync && lipsync.phraseEnds !== this.lastPhraseEnds) {
      this.lastPhraseEnds = lipsync.phraseEnds;
      this.blinker.notifyPhraseEnd();
    }
    const stress = lipsync ? lipsync.stress : speaking && open > 0.7 ? 1 : 0;
    this.blinkCtx.stress = stress;
    this.blinkCtx.reduced = reduced;
    const blink = this.blinker.update(dt, this.blinkCtx);
    if (this.binding.hasBlink) applyBlink(this.binding, blink);
    return blink;
  }

  /** Put every bound morph back to 0 (the scene is being torn down or the source changed). */
  reset() {
    resetMorphs(this.binding);
    this.shown.fill(0);
    this.shown[VI.sil] = 1;
  }
}
