// The colour grade, inside THREE.CustomToneMapping (LOOKDEV-SPEC S4 and S5): PBR Neutral first, then
// saturation, a split tone toward the painting's slate shadows and warm highlights, a black lift and a touch of
// horizon haze. No post pass, so MSAA and alpha survive and there is no new dependency.
//
// Importing this file patches ShaderChunk.tonemapping_pars_fragment once (idempotent). Only programs that
// select CustomToneMapping call the grade; other canvases (forest, MeadowLife) never use it. Every tone-mapped
// material of the avatar canvas must carry the uniforms below (attachGradeUniforms); a missing one reads 0.
import { Color, CustomToneMapping, NeutralToneMapping, ShaderChunk } from 'three';
import { LOOKDEV } from './lookdevConfig.js';

const MARKER = '/* lookdev-grade */';
const STOCK = 'vec3 CustomToneMapping( vec3 color ) { return color; }';

const GRADE_GLSL = `${MARKER}
uniform vec3 uGradeShadow;
uniform vec3 uGradeHigh;
uniform vec3 uGradeLift;
uniform float uGradeSat;
uniform float uGradeSplit;
uniform float uGradeHaze;
uniform vec3 uGradeHazeColor;
vec3 CustomToneMapping( vec3 color ) {
  vec3 c = NeutralToneMapping( color );
  float l = dot( c, vec3( 0.2126, 0.7152, 0.0722 ) );
  c = mix( vec3( l ), c, uGradeSat );
  float sh = 1.0 - smoothstep( 0.0, 0.45, l );
  float hi = smoothstep( 0.45, 1.0, l );
  c = mix( c, c * uGradeShadow * 2.0, sh * uGradeSplit );
  c = mix( c, c * uGradeHigh * 1.15, hi * uGradeSplit * 0.6 );
  c = uGradeLift + c * ( 1.0 - uGradeLift );
  c = mix( c, uGradeHazeColor, uGradeHaze );
  return clamp( c, 0.0, 1.0 );
}`;

let patched = false;
/** Patch the chunk once, before the first program that uses it compiles. Safe to call any number of times. */
export function patchToneMappingChunk() {
  if (patched) return;
  patched = true;
  const chunk = ShaderChunk.tonemapping_pars_fragment;
  if (chunk.includes(MARKER) || !chunk.includes(STOCK)) return; // already patched, or three changed the stub
  ShaderChunk.tonemapping_pars_fragment = chunk.replace(STOCK, GRADE_GLSL);
}

const g = LOOKDEV.grade;
/** Scale a tint so its luminance is 0.5 (the shader doubles it): the split tone then changes hue, not brightness. */
function neutralTint(c) {
  const l = 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
  return l > 0 ? c.multiplyScalar(0.5 / l) : c;
}
/** The shared uniform objects (linear colours). Change .value and every material follows. */
export const GRADE_UNIFORMS = {
  uGradeShadow: { value: neutralTint(new Color(g.shadowTint)) },
  uGradeHigh: { value: new Color(g.highlightTint) },
  uGradeLift: { value: new Color(g.lift).multiplyScalar(g.liftAmount) },
  uGradeSat: { value: g.saturation },
  uGradeSplit: { value: g.split },
  uGradeHaze: { value: g.haze },
  uGradeHazeColor: { value: new Color(g.hazeColor) },
};

/** Put the shared grade uniforms on a compiling shader (call from onBeforeCompile). */
export function attachGradeUniforms(shader) {
  Object.assign(shader.uniforms, GRADE_UNIFORMS);
}

/**
 * Select the grade on a renderer. If a program fails to compile with it, fall back to plain Neutral and log once.
 * Returns an undo function.
 */
export function selectGradeToneMapping(gl, onFallback) {
  patchToneMappingChunk();
  const prevMapping = gl.toneMapping;
  const prevExposure = gl.toneMappingExposure;
  const prevHandler = gl.debug.onShaderError;
  gl.toneMapping = CustomToneMapping;
  gl.toneMappingExposure = LOOKDEV.exposure;
  let fellBack = false;
  gl.debug.onShaderError = (...args) => {
    if (prevHandler) prevHandler(...args);
    if (fellBack || gl.toneMapping !== CustomToneMapping) return;
    fellBack = true;
    console.warn('[lookdev] the colour grade failed to compile; using Neutral tone mapping instead.');
    gl.toneMapping = NeutralToneMapping;
    if (onFallback) onFallback();
  };
  return () => {
    gl.debug.onShaderError = prevHandler;
    gl.toneMapping = prevMapping;
    gl.toneMappingExposure = prevExposure;
  };
}
