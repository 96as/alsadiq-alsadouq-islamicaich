// Where the painted meadow sits on the stage, and the camera that puts Sadiq in it (LOOKDEV-SPEC S6).
// Pure functions, no React, no three.js, so node --test can check them (tests/stageFraming.test.mjs).
//
// The painting is MeadowImage's <img>: object-fit: cover, object-position 47.5% center (the fit it draws
// before it has measured, and the one it keeps in look-dev mode). The test parses MeadowImage.jsx and
// meadowFraming.js so a change there that is not mirrored here fails.
//
// The camera is level (pitch 0, verticals stay vertical like the painting). A vertical lens shift puts the
// 3D horizon on the painted one, and the camera height is a fraction k of his height, so the horizon cuts
// him at that fraction like in the original app (eye level on phones, chest on wide screens).
import { LOOKDEV } from './lookdevConfig.js';

/** The painting's fit. Keep in step with MeadowImage.jsx and meadowFraming.js (the test checks both). */
export const PAINTING = {
  aspect: 16 / 9, // 2560 x 1440, and every file in backgrounds/hq/
  horizonV: 0.455, // the horizon's row, from the top of the painting (MOTION-BIBLE 7.8)
  posX: 0.475, // object-position 47.5% center
  posY: 0.5,
};

/** Path centre of the painting, image v to image u (S6.2, lookdev-tools/path_centre.py). */
const PATH_RAW = [
  [0.55, 0.528],
  [0.6, 0.553],
  [0.65, 0.517],
  [0.7, 0.517],
  [0.75, 0.503],
  [0.8, 0.463],
  [0.85, 0.415],
  [0.9, 0.419],
  [0.95, 0.391],
];
/** Path width (image u), same rows: used by the tests and the gates (L3). */
const PATH_WIDTH = [0.062, 0.097, 0.147, 0.122, 0.103, 0.072, 0.13, 0.197, 0.192];

// A 3-tap mean (ends keep their value) so one noisy row never kicks him sideways.
const PATH_U = PATH_RAW.map(([, u], i, a) => (i === 0 || i === a.length - 1 ? u : (a[i - 1][1] + u + a[i + 1][1]) / 3));

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const smoothstep = (a, b, x) => {
  const t = clamp((x - a) / (b - a), 0, 1);
  return t * t * (3 - 2 * t);
};
const lerp = (a, b, t) => a + (b - a) * t;
const interp = (table, key) => {
  if (key <= table[0][0]) return table[0][1];
  for (let i = 1; i < table.length; i++) {
    if (key <= table[i][0]) {
      const [k0, v0] = table[i - 1];
      const [k1, v1] = table[i];
      return lerp(v0, v1, (key - k0) / (k1 - k0));
    }
  }
  return table[table.length - 1][1];
};

/** The painting's placement on a W x H stage: displayed size and the top-left corner, in px. */
export function paintingFit(W, H) {
  const dh = Math.max(W / PAINTING.aspect, H);
  const dw = dh * PAINTING.aspect;
  return { dw, dh, ox: (W - dw) * PAINTING.posX, oy: (H - dh) * PAINTING.posY };
}

/** Image (u, v) in 0..1 to stage px. */
export function paintingToScreen(u, v, W, H) {
  const f = paintingFit(W, H);
  return [f.ox + u * f.dw, f.oy + v * f.dh];
}

/** Stage y (px) to image v. */
export function screenToPaintingV(y, W, H) {
  const f = paintingFit(W, H);
  return (y - f.oy) / f.dh;
}

/** The painted horizon, as a fraction of the stage height from the top. */
export function horizonY(W, H) {
  return paintingToScreen(0.5, PAINTING.horizonV, W, H)[1] / H;
}

/** Path centre (image u) at image row v. Clamped above and below the measured rows. */
export function pathCentreU(v) {
  return interp(
    PATH_RAW.map(([vv], i) => [vv, PATH_U[i]]),
    v,
  );
}

/** Path width (image u) at image row v. */
export function pathWidthU(v) {
  return interp(
    PATH_RAW.map(([vv], i) => [vv, PATH_WIDTH[i]]),
    v,
  );
}

/**
 * Everything the stage camera needs for a W x H stage (CSS px). `safe` is { top, bottom } px kept free for
 * the header and the controls row.
 * Returns { fov, dist, eye, viewOffsetY, avatarX, Hf, k, yH, yFeet, feetX } where yH, yFeet, Hf are fractions of
 * the stage height, viewOffsetY is px for camera.setViewOffset(W, H, 0, viewOffsetY, W, H), and feetX is the
 * feet's screen x as a fraction of the width.
 */
export function solveFraming(W, H, safe = LOOKDEV.framing.safe) {
  const F = LOOKDEV.framing;
  const a = W / H;
  const t = smoothstep(0, 1, (Math.log(a) - Math.log(F.aspectRange[0])) / (Math.log(F.aspectRange[1]) - Math.log(F.aspectRange[0])));
  const k = lerp(F.eyeFraction[0], F.eyeFraction[1], t);
  const yH = horizonY(W, H);

  // His height as a share of the stage, then the safe areas: feet 16 px above the controls row and ears 12 px
  // below the header. Both limits are linear in Hf at a fixed k, so each gives a ceiling for Hf.
  let Hf = lerp(F.heightFraction[0], F.heightFraction[1], t);
  const feetMax = 1 - (safe.bottom + F.feetAboveControls) / H;
  const earsMin = (safe.top + F.earsBelowHeader) / H;
  Hf = Math.min(Hf, (feetMax - yH) / k, (yH - earsMin) / (1 - k));
  Hf = Math.max(Hf, 0.2); // a tiny stage must still show him

  const yFeet = yH + k * Hf;
  const halfTan = Math.tan((F.fov * Math.PI) / 360);
  const dist = F.charHeight / (Hf * 2 * halfTan);
  const eye = k * F.charHeight;

  // Feet x: the path centre at the feet's painting row, clamped to the middle band of the width.
  const v = screenToPaintingV(yFeet * H, W, H);
  const [px] = paintingToScreen(pathCentreU(v), v, W, H);
  const feetX = clamp(px / W, F.pathScreenX[0], F.pathScreenX[1]);
  const halfWidthWorld = dist * halfTan * a; // half the stage width at his depth
  const avatarX = (feetX - 0.5) * 2 * halfWidthWorld;

  return { fov: F.fov, dist, eye, viewOffsetY: -(yH - 0.5) * H, avatarX, Hf, k, yH, yFeet, feetX };
}
