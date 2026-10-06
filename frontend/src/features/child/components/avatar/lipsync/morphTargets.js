// Finds the viseme and blink morph targets in a loaded avatar scene and writes weights to them.
// Duck-typed on three.js meshes (`morphTargetDictionary`, `morphTargetInfluences`), so it works
// on any scene and is testable without a renderer.
//
// A face is often several meshes (head, teeth, tongue) that share morph names; every mesh that
// has a name is bound, so one weight moves them all together.

import { BLINK_MORPH_NAMES, MORPH_NAME_PREFIXES, VISEMES, VISEME_COUNT, VISEME_GAIN } from './visemes.js';

/** A viseme is "driven by morphs" once the scene has at least this many of the 14. */
export const MIN_VISEMES_FOUND = 5;

/**
 * Candidate names for each viseme, lowercase, most specific first. `morphNames` overrides:
 *   { aa: 'Mouth_Ah', O: ['Mouth_Oh', 'oh'] }  (a string or an array of strings per viseme)
 */
function candidatesFor(viseme, morphNames) {
  const given = morphNames?.[viseme];
  const list = [];
  if (given) list.push(...[].concat(given).map((n) => n.toLowerCase()));
  for (const prefix of MORPH_NAME_PREFIXES) list.push(`${prefix}${viseme}`.toLowerCase());
  return list;
}

/**
 * @param {object} root the scene (anything with traverse())
 * @param {{morphNames?: object, blinkNames?: string[]}} [opts]
 * @returns {{
 *   visemes: Array<Array<{mesh: object, index: number}>>,
 *   blink: Array<{mesh: object, index: number}>,
 *   foundVisemes: string[], missingVisemes: string[], hasVisemes: boolean, hasBlink: boolean,
 * }}
 */
export function bindMorphTargets(root, { morphNames, blinkNames = BLINK_MORPH_NAMES } = {}) {
  const visemes = Array.from({ length: VISEME_COUNT }, () => []);
  const blink = [];
  const wanted = VISEMES.map((v) => candidatesFor(v, morphNames));
  const blinkWanted = new Set(blinkNames.map((n) => n.toLowerCase()));

  root.traverse((obj) => {
    const dict = obj.morphTargetDictionary;
    if (!dict || !obj.morphTargetInfluences) return;
    // Lowercase lookup of this mesh's morph names.
    const lower = new Map();
    for (const [name, index] of Object.entries(dict)) lower.set(name.toLowerCase(), index);
    wanted.forEach((names, v) => {
      for (const name of names) {
        if (lower.has(name)) {
          visemes[v].push({ mesh: obj, index: lower.get(name) });
          return; // the first name that matches wins for this mesh
        }
      }
    });
    for (const [name, index] of lower) {
      if (blinkWanted.has(name)) blink.push({ mesh: obj, index });
    }
  });

  const foundVisemes = VISEMES.filter((_, v) => visemes[v].length > 0);
  return {
    visemes,
    blink,
    foundVisemes,
    missingVisemes: VISEMES.filter((_, v) => visemes[v].length === 0),
    hasVisemes: foundVisemes.length >= MIN_VISEMES_FOUND,
    hasBlink: blink.length > 0,
  };
}

function write(bindings, weight) {
  for (let i = 0; i < bindings.length; i++) {
    const { mesh, index } = bindings[i];
    mesh.morphTargetInfluences[index] = weight;
  }
}

/** Write 14 viseme weights (index = VI.*) to the bound morph targets, scaled by VISEME_GAIN. */
export function applyVisemes(binding, weights, gains = VISEME_GAIN) {
  for (let v = 0; v < VISEME_COUNT; v++) {
    const list = binding.visemes[v];
    if (list.length === 0) continue;
    const gain = gains[VISEMES[v]] ?? 1;
    write(list, weights[v] * gain);
  }
}

/** Write the blink weight (0 open, 1 closed) to every bound blink morph. */
export function applyBlink(binding, weight) {
  if (binding.blink.length > 0) write(binding.blink, weight);
}

/** Put every bound morph back to 0. */
export function resetMorphs(binding) {
  for (const list of binding.visemes) write(list, 0);
  write(binding.blink, 0);
}
