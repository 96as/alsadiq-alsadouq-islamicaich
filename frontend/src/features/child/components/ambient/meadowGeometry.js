// Where the painting is on screen, and the wind at a screen position. Pure (no React, no WebGL), shared by
// MeadowLife (the painting layer, on the GPU) and the foreground strip (on the CPU) so both read the same gust
// at the same x and y.

import { computeFraming, MEADOW_IMAGE } from '../meadowFraming';
import { HORIZON_V } from './meadowMasks';
import { screenGustWith } from '../forest/wind/windField';

/**
 * The rectangle of the painting under object-fit: cover with the anchored framing, in css px, plus the screen y
 * of its horizon row. sc is the scale against the 1100 px reference width of the Motion Bible numbers.
 */
export function meadowRect(w, h, out = {}) {
  const fr = computeFraming(w, h);
  const s = Math.max(w / MEADOW_IMAGE.aspect, h);
  const imgW = s * MEADOW_IMAGE.aspect;
  const imgH = s;
  out.left = -fr.objectX * (imgW - w);
  out.top = -fr.objectY * (imgH - h);
  out.width = imgW;
  out.height = imgH;
  out.horizonY = out.top + HORIZON_V * imgH;
  out.sc = imgW / 1100;
  out.pathX = fr.pathX;
  out.feetY = fr.feetY;
  out.avatarPx = fr.avatarPx;
  return out;
}

/** Depth 0 (horizon) to 1 (bottom edge) of a screen y, the same clamp the shaders use. */
export function paintedDepth(y, horizonY, h) {
  const d = (y - horizonY) / Math.max(1, h - horizonY);
  return d < 0 ? 0 : d > 1 ? 1 : d;
}

/** The gust strength at a screen position (css px), from a prepared windState. Same value as the GPU. */
export function paintedGust(st, x, y, w, h, horizonY, lag = 0) {
  return screenGustWith(st, x / w, paintedDepth(y, horizonY, h), lag);
}
