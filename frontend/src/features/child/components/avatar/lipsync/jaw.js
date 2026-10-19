// The jaw target as a pure function of the viseme weights the mouth is showing, so the avatar
// (ClipAvatar.jsx) and the offline evaluation (scripts/lipsync-eval) use the same formula.
// No three.js, no DOM.

import { VI, VISEMES, VISEME_COUNT } from './visemes.js';

/**
 * Per-viseme jaw opening table (VISEMES order) from a name -> 0..1 map such as JAW.open.
 * @param {Record<string, number>} openByName
 */
export function jawOpenTable(openByName) {
  const table = new Float32Array(VISEME_COUNT);
  VISEMES.forEach((name, i) => {
    table[i] = openByName[name] ?? 0;
  });
  return table;
}

/**
 * Where the jaw wants to be, 0..1 of JAW.max (before the attack and release damping).
 *
 * Two parts, as in JALI (jaw from loudness, lips from the phoneme): the viseme table says how far
 * the shape opens the jaw, and the loudness scales it, 1 - couple + couple * level, so a whisper
 * does not drop the chin as far as a shout. A lip closure keeps the chin up: while the closure
 * weight is at or above `ppAt` the target is at most `ppMax`.
 *
 * @param {Float32Array|number[]} shown the 14 weights on screen (index 0, sil, is ignored)
 * @param {Float32Array} table from jawOpenTable()
 * @param {{level?: number, couple?: number, ppMax?: number, ppAt?: number}} [opts] level is the
 *   loudness 0..1; couple 0 (the default) ignores it; ppMax defaults to no clamp
 */
export function jawTarget(shown, table, { level = 1, couple = 0, ppMax = 1, ppAt = 0.5 } = {}) {
  let want = 0;
  for (let i = 1; i < VISEME_COUNT; i++) want += shown[i] * table[i];
  want *= 1 - couple + couple * (level < 0 ? 0 : level > 1 ? 1 : level);
  if (shown[VI.PP] >= ppAt && want > ppMax) want = ppMax;
  return want < 0 ? 0 : want > 1 ? 1 : want;
}
