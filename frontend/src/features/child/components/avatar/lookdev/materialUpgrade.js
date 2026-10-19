// Runtime material upgrades for the avatar (LOOKDEV-SPEC S7). The GLB is never rebuilt: the lookdev component
// walks the loaded scene and swaps each mesh's material for an upgraded CLONE, so the cached glTF stays
// pristine (the forest and the "?look=before" A/B keep today's look).
//
//   - normal scale 0.9, a warmer and tighter fur sheen, anisotropic filtering on every map;
//   - an eye mask from the ORM roughness (0.078 only in the eyes, 0.34 or more everywhere else), so the eyes get a
//     wet cornea (low roughness, full specular) without a new texture;
//   - a Fresnel^3 light wrap: the painting's grass colour on his lower silhouette, its sky on the upper one;
//   - the shared grade uniforms (every tone-mapped material of the canvas must carry them).
import { Color } from 'three';
import { LOOKDEV } from './lookdevConfig.js';
import { attachGradeUniforms } from './gradeToneMapping.js';

const BACKDROP = 'BackdropMat';
const TEXTURE_SLOTS = ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'aoMap', 'emissiveMap'];
const f = (n) => (Number.isInteger(n) ? `${n}.0` : String(n));

// One shared pair of colours: every upgraded material reads the same objects.
const WRAP_UNIFORMS = {
  uWrapLow: { value: new Color(LOOKDEV.material.wrap.low) },
  uWrapHigh: { value: new Color(LOOKDEV.material.wrap.high) },
  uWrap: { value: LOOKDEV.material.wrap.strength },
};

/** The shader edits, as plain string replacements on three's own chunk names (checked against r184). */
function patchShader(shader, hasEyeMask) {
  const m = LOOKDEV.material;
  const w = m.wrap;
  const e = m.eye;
  Object.assign(shader.uniforms, WRAP_UNIFORMS);
  attachGradeUniforms(shader);

  shader.vertexShader = shader.vertexShader
    .replace('#include <common>', '#include <common>\nvarying float vLookWorldY;')
    .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvLookWorldY = ( modelMatrix * vec4( transformed, 1.0 ) ).y;');

  const eyeRoughness = hasEyeMask
    ? `float eyeMask = 1.0 - smoothstep( ${f(e.maskFrom)}, ${f(e.maskTo)}, roughnessFactor );\nroughnessFactor = mix( roughnessFactor, ${f(e.roughness)}, eyeMask );`
    : 'float eyeMask = 0.0;';
  const eyeSpecular = hasEyeMask
    ? `material.specularColorBlended = mix( material.specularColorBlended, vec3( ${f(e.specularColor)} ), eyeMask );\nmaterial.specularF90 = mix( material.specularF90, ${f(e.specularF90)}, eyeMask );\n#ifdef USE_SHEEN\nmaterial.sheenColor *= ( 1.0 - eyeMask );\n#endif`
    : '';

  shader.fragmentShader = shader.fragmentShader
    .replace(
      '#include <common>',
      '#include <common>\nvarying float vLookWorldY;\nuniform vec3 uWrapLow;\nuniform vec3 uWrapHigh;\nuniform float uWrap;',
    )
    .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>\n${eyeRoughness}`)
    .replace('#include <lights_physical_fragment>', `#include <lights_physical_fragment>\n${eyeSpecular}`)
    .replace(
      '#include <emissivemap_fragment>',
      `#include <emissivemap_fragment>
float lookFr = pow( 1.0 - clamp( dot( normal, normalize( vViewPosition ) ), 0.0, 1.0 ), ${f(w.power)} );
vec3 lookWrap = mix( uWrapLow, uWrapHigh, smoothstep( ${f(w.worldYRange[0])}, ${f(w.worldYRange[1])}, vLookWorldY ) );
totalEmissiveRadiance += lookWrap * lookFr * uWrap * ( 1.0 - eyeMask );`,
    );
}

/**
 * Upgrade one material in place (pass a clone). Returns it. Skips the legacy backdrop and non-PBR materials.
 * @param {import('three').Material} material
 * @param {number} maxAnisotropy renderer.capabilities.getMaxAnisotropy()
 */
export function upgradeAvatarMaterial(material, maxAnisotropy = 1) {
  const cfg = LOOKDEV.material;
  if (!material || material.name === BACKDROP || material.userData.lookdev) return material;
  material.userData.lookdev = true;
  if (!material.isMeshStandardMaterial) {
    // Not a PBR material: no upgrade, but if it is tone-mapped it still needs the grade uniforms.
    const prior = material.onBeforeCompile;
    material.onBeforeCompile = (shader, renderer) => {
      if (prior) prior.call(material, shader, renderer);
      attachGradeUniforms(shader);
    };
    material.customProgramCacheKey = () => 'lookdev-plain';
    material.needsUpdate = true;
    return material;
  }

  if (material.normalMap) material.normalScale.setScalar(cfg.normalScale);
  material.envMapIntensity = cfg.envMapIntensity;
  if (material.isMeshPhysicalMaterial) {
    material.sheen = 1;
    material.sheenColor = new Color(cfg.sheenColor);
    material.sheenRoughness = cfg.sheenRoughness;
  }
  const aniso = Math.min(cfg.maxAnisotropy, maxAnisotropy);
  for (const slot of TEXTURE_SLOTS) {
    const tex = material[slot];
    if (tex && tex.anisotropy !== aniso) {
      tex.anisotropy = aniso;
      tex.needsUpdate = true; // re-upload with the new filter (a no-op cost before the first render)
    }
  }

  const hasEyeMask = Boolean(material.roughnessMap); // the mask reads the ORM; a scalar roughness cannot isolate the eyes
  const prior = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    if (prior) prior.call(material, shader, renderer);
    patchShader(shader, hasEyeMask);
  };
  // Variants must not collide in three's program cache.
  material.customProgramCacheKey = () => `lookdev1${hasEyeMask ? 'e' : ''}${material.isMeshPhysicalMaterial ? 'p' : 's'}`;
  material.needsUpdate = true;
  return material;
}

/** A material the grade has to reach: tone-mapped, and not the legacy backdrop. */
const needsGrade = (m) => Boolean(m) && m.name !== BACKDROP && m.toneMapped !== false;

/**
 * Upgrade the meshes below `root` (once per mesh). Returns how many meshes changed.
 * - The avatar's PBR materials get an upgraded CLONE (the cached glTF is shared with other canvases).
 * - Other tone-mapped materials are patched IN PLACE: they only need the grade uniforms, and a clone would cut
 *   their owner's live references (a ShaderMaterial clone deep-copies its uniforms, so per-frame updates stop).
 * - Un-tone-mapped materials (the context hologram, sprites, the rig's own blobs) never call the grade: left alone.
 * - Only PBR meshes (the avatar) cast the shadow on the catcher.
 */
export function upgradeSceneMaterials(root, maxAnisotropy, castShadow = false) {
  let changed = 0;
  root.traverse((obj) => {
    if (!obj.isMesh || !obj.material || obj.userData.lookdevMaterial) return;
    const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
    if (mats.some((x) => x?.name === BACKDROP)) return;
    if (!mats.some(needsGrade)) return;
    obj.userData.lookdevMaterial = true;
    if (castShadow && mats.some((x) => x?.isMeshStandardMaterial)) obj.castShadow = true;
    obj.userData.originalMaterial = obj.material;
    const up = (x) => {
      if (!needsGrade(x)) return x;
      return upgradeAvatarMaterial(x.isMeshStandardMaterial ? x.clone() : x, maxAnisotropy);
    };
    obj.material = Array.isArray(obj.material) ? obj.material.map(up) : up(obj.material);
    changed += 1;
  });
  return changed;
}

/** Mark every upgraded material for recompilation (used when the grade falls back to Neutral). */
export function refreshSceneMaterials(root) {
  root.traverse((obj) => {
    if (!obj.isMesh || !obj.material) return;
    for (const mat of Array.isArray(obj.material) ? obj.material : [obj.material]) mat.needsUpdate = true;
  });
}
