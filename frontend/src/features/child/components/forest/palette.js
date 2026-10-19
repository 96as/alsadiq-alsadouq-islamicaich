import * as THREE from 'three';
import { PALETTES } from './timeOfDay';

/** Turn a palette (hex strings, numbers, arrays, objects) into mutable runtime values. */
function toRuntime(value) {
  if (typeof value === 'string') return new THREE.Color(value);
  if (Array.isArray(value)) return value.slice();
  if (value && typeof value === 'object') {
    const out = {};
    Object.keys(value).forEach((k) => {
      out[k] = toRuntime(value[k]);
    });
    return out;
  }
  return value;
}

function blend(cur, target, k) {
  if (cur && cur.isColor) {
    cur.lerp(target, k);
    return cur;
  }
  if (Array.isArray(cur)) {
    for (let i = 0; i < cur.length; i += 1) cur[i] += (target[i] - cur[i]) * k;
    return cur;
  }
  if (cur && typeof cur === 'object') {
    Object.keys(cur).forEach((key) => {
      cur[key] = blend(cur[key], target[key], k);
    });
    return cur;
  }
  return cur + (target - cur) * k;
}

export function makePalette(name) {
  return toRuntime(PALETTES[name] || PALETTES.noon);
}

export function makeTargets() {
  const out = {};
  Object.keys(PALETTES).forEach((name) => {
    out[name] = toRuntime(PALETTES[name]);
  });
  return out;
}

/** Move `current` toward `target` by factor k (0..1). Mutates `current`. */
export function stepPalette(current, target, k) {
  blend(current, target, k);
}

export function avatarFilterCss(f) {
  const identity =
    Math.abs(f.b - 1) < 0.015 && Math.abs(f.s - 1) < 0.015 && f.sep < 0.015;
  if (identity) return 'none';
  return `brightness(${f.b.toFixed(3)}) saturate(${f.s.toFixed(3)}) sepia(${f.sep.toFixed(3)}) hue-rotate(${f.hue.toFixed(1)}deg)`;
}

function assign(out, src) {
  if (out && out.isColor) {
    out.copy(src);
    return out;
  }
  if (Array.isArray(out)) {
    for (let i = 0; i < out.length; i += 1) out[i] = src[i];
    return out;
  }
  if (out && typeof out === 'object') {
    Object.keys(out).forEach((key) => {
      out[key] = assign(out[key], src[key]);
    });
    return out;
  }
  return src;
}

/** out = a, then moved toward b by weight w (0..1). Mutates `out`, which must have a's shape. */
export function mixPalette(out, a, b, w) {
  assign(out, a);
  blend(out, b, w);
}
