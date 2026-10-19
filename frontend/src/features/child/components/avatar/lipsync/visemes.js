// The 14 Oculus / OVR visemes, in the order of the shape keys in Abdulrahman's Blender file.
// Plain data only: no audio, no three.js. Everything else in lipsync/ builds on this.

export const VISEMES = ['sil', 'PP', 'FF', 'DD', 'kk', 'CH', 'SS', 'nn', 'RR', 'aa', 'E', 'I', 'O', 'U'];
export const VISEME_COUNT = VISEMES.length;

/** Index of each viseme in a weights array, e.g. VI.aa === 9. */
export const VI = Object.freeze(Object.fromEntries(VISEMES.map((name, i) => [name, i])));

export const VOWELS = ['aa', 'E', 'I', 'O', 'U'];
export const VOWEL_INDEX = VOWELS.map((name) => VI[name]);

/**
 * Names a viseme morph target may have in the GLB, in the order they are tried. Matching ignores
 * case. To plug in the exact names of a new GLB, pass `morphNames` (see morphTargets.js), or
 * edit MORPH_NAME_PREFIXES below if the whole set shares one prefix.
 */
export const MORPH_NAME_PREFIXES = ['viseme_', 'v_', 'viseme', 'mouth_', 'vis_', ''];

/** Names of the eyelid morph target(s) that blink. All that are found are driven together. */
export const BLINK_MORPH_NAMES = [
  'blink',
  'eyeblink',
  'eyes_blink',
  'eyesclosed',
  'eyes_closed',
  'eyeblinkleft',
  'eyeblinkright',
  'blink_l',
  'blink_r',
  'blinkl',
  'blinkr',
];

/**
 * How strongly each viseme may be driven on this avatar, 0..1 (a multiplier on the weight).
 * Lower a value if that shape key looks too strong in the GLB. Keys not listed use 1.
 */
export const VISEME_GAIN = Object.freeze({
  aa: 0.95,
  O: 0.9,
  U: 0.9,
  E: 0.9,
  I: 0.85,
});
