// A flat 2D mouth for the dev page, so the 14 viseme weights can be judged by eye without the 3D
// avatar. Each viseme is a handful of numbers; the shown mouth is their weighted blend.

import { VISEMES } from '../visemes.js';

// open: gap between the lips 0..1, wide: mouth width 0..1, round: lips pushed out 0..1,
// teeth: upper teeth visible 0..1, tongue: tongue raised 0..1, press: lips pressed together 0..1
const SHAPES = {
  sil: { open: 0.0, wide: 0.5, round: 0, teeth: 0, tongue: 0, press: 0 },
  PP: { open: 0.0, wide: 0.45, round: 0, teeth: 0, tongue: 0, press: 1 },
  FF: { open: 0.12, wide: 0.55, round: 0, teeth: 1, tongue: 0, press: 0 },
  DD: { open: 0.3, wide: 0.55, round: 0, teeth: 0.8, tongue: 0.8, press: 0 },
  kk: { open: 0.4, wide: 0.5, round: 0, teeth: 0.2, tongue: 0.5, press: 0 },
  CH: { open: 0.25, wide: 0.35, round: 0.55, teeth: 0.7, tongue: 0.3, press: 0 },
  SS: { open: 0.12, wide: 0.8, round: 0, teeth: 1, tongue: 0.2, press: 0 },
  nn: { open: 0.2, wide: 0.5, round: 0, teeth: 0.4, tongue: 0.8, press: 0 },
  RR: { open: 0.25, wide: 0.4, round: 0.4, teeth: 0.3, tongue: 0.4, press: 0 },
  aa: { open: 1.0, wide: 0.6, round: 0, teeth: 0.4, tongue: 0.1, press: 0 },
  E: { open: 0.5, wide: 0.85, round: 0, teeth: 0.6, tongue: 0.2, press: 0 },
  I: { open: 0.25, wide: 1.0, round: 0, teeth: 0.85, tongue: 0.3, press: 0 },
  O: { open: 0.65, wide: 0.3, round: 0.85, teeth: 0, tongue: 0, press: 0 },
  U: { open: 0.3, wide: 0.1, round: 1.0, teeth: 0, tongue: 0, press: 0 },
};

const KEYS = ['open', 'wide', 'round', 'teeth', 'tongue', 'press'];

/** Weighted blend of the shapes (the weights are expected to sum to about 1). */
export function blendShape(weights) {
  const out = { open: 0, wide: 0, round: 0, teeth: 0, tongue: 0, press: 0 };
  let sum = 0;
  for (let i = 0; i < VISEMES.length; i++) {
    const w = weights[i];
    if (!(w > 0)) continue;
    sum += w;
    const s = SHAPES[VISEMES[i]];
    for (const k of KEYS) out[k] += s[k] * w;
  }
  if (sum > 1e-4) for (const k of KEYS) out[k] /= sum;
  return out;
}

/** SVG geometry for a blended shape, in a 200 x 120 box centred on (100, 62). */
export function mouthGeometry(shape) {
  const half = 20 + 34 * shape.wide - 14 * shape.round; // half width
  const up = 3 + 11 * shape.open + 5 * shape.round; // upper lip lift
  const down = 3 + 30 * shape.open + 6 * shape.round; // lower lip drop
  const pinch = 0.55 + 0.25 * shape.round; // how far the control points sit from the corner
  const cx = 100;
  const cy = 62;
  const left = cx - half;
  const right = cx + half;
  const inner =
    `M ${left} ${cy} ` +
    `C ${cx - half * pinch} ${cy - up}, ${cx + half * pinch} ${cy - up}, ${right} ${cy} ` +
    `C ${cx + half * pinch} ${cy + down}, ${cx - half * pinch} ${cy + down}, ${left} ${cy} Z`;
  return { inner, left, right, cy, half, up, down, cx };
}
