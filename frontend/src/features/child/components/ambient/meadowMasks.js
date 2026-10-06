// Masks for the painted meadow, computed once at load from a small downsample of the painting itself (no
// hand-painted mask yet; if the lead supplies one, return it from here instead). Pure: no DOM, no WebGL.
//
// The image is 256 x 144 RGBA in, and a 256 x 144 RGBA mask out:
//   R grass   below the horizon and not the path: the layer that waves, brightens in gusts and takes cloud shadow
//   G trees   green above the horizon (crowns): a small warp
//   B path    the beige track: it stays still, but takes the cloud shadow
//   A sky     above the horizon, not trees, not the grey-blue mountains: only the cloud wisps go here
//
// Coordinates are fractions of the image. The horizon is at v = 0.455 (measured on the 1600 px painting).

export const HORIZON_V = 0.455;
export const MASK_W = 256;
export const MASK_H = 144;

const smooth = (a, b, x) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

function hsv(r, g, b, out) {
  const mx = Math.max(r, g, b);
  const mn = Math.min(r, g, b);
  const d = mx - mn;
  let h = 0;
  if (d > 1e-6) {
    if (mx === r) h = ((g - b) / d) % 6;
    else if (mx === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h *= 60;
    if (h < 0) h += 360;
  }
  out[0] = h;
  out[1] = mx > 1e-6 ? d / mx : 0;
  out[2] = mx;
  return out;
}

/** Box blur of one channel of an interleaved RGBA float buffer, radius r, in place via a temp. */
function blurChannel(buf, w, h, ch, r) {
  const tmp = new Float32Array(w * h);
  const n = 2 * r + 1;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      let s = 0;
      for (let k = -r; k <= r; k++) s += buf[(y * w + Math.min(w - 1, Math.max(0, x + k))) * 4 + ch];
      tmp[y * w + x] = s / n;
    }
  }
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      let s = 0;
      for (let k = -r; k <= r; k++) s += tmp[Math.min(h - 1, Math.max(0, y + k)) * w + x];
      buf[(y * w + x) * 4 + ch] = s / n;
    }
  }
}

/** rgba: Uint8ClampedArray or Uint8Array of w * h * 4. Returns Uint8Array w * h * 4. */
export function computeMeadowMasks(rgba, w = MASK_W, h = MASK_H) {
  const m = new Float32Array(w * h * 4);
  const c = [0, 0, 0];
  for (let y = 0; y < h; y++) {
    const v = (y + 0.5) / h;
    const below = smooth(HORIZON_V - 0.012, HORIZON_V + 0.012, v);
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4;
      const r = rgba[i] / 255;
      const g = rgba[i + 1] / 255;
      const b = rgba[i + 2] / 255;
      hsv(r, g, b, c);
      const hue = c[0];
      const sat = c[1];
      const val = c[2];
      const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;

      // Path: beige, low-mid saturation, warm hue, in the lower part of the picture.
      const warm = smooth(2, 12, hue) * (1 - smooth(40, 52, hue));
      const pathness = warm * smooth(0.1, 0.18, sat) * (1 - smooth(0.46, 0.58, sat)) * smooth(0.36, 0.5, val) * smooth(0.5, 0.56, v);

      // Green: grass and tree colour (yellow-green to green-teal).
      const dark = (1 - smooth(0.42, 0.56, val)) * smooth(0.05, 0.12, sat); // dark conifers
      const green = smooth(52, 72, hue) * (1 - smooth(165, 185, hue)) * Math.max(smooth(0.16, 0.3, sat), dark);

      // Mountains and the rock face: grey-blue and not bright.
      const blueGrey = smooth(185, 205, hue) * (1 - smooth(255, 275, hue)) * (1 - smooth(0.46, 0.6, sat)) * (1 - smooth(0.5, 0.64, lum));

      const grass = below * (1 - pathness);
      const trees = (1 - below) * green;
      const sky = (1 - below) * (1 - green) * (1 - blueGrey) * smooth(0.5, 0.62, lum);
      m[i] = grass;
      m[i + 1] = trees;
      m[i + 2] = below * pathness;
      m[i + 3] = sky;
    }
  }
  // Soften edges so a mask never gives a visible seam in the warp (bilinear upsample does the rest).
  for (let ch = 0; ch < 4; ch++) blurChannel(m, w, h, ch, 1);
  // The grass mask keeps its crisp horizon: restore it analytically.
  for (let y = 0; y < h; y++) {
    const v = (y + 0.5) / h;
    const below = smooth(HORIZON_V - 0.012, HORIZON_V + 0.012, v);
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4;
      m[i] = Math.min(m[i], below);
      m[i + 3] = Math.min(m[i + 3], 1 - below);
    }
  }
  const out = new Uint8Array(w * h * 4);
  for (let i = 0; i < out.length; i++) out[i] = Math.max(0, Math.min(255, Math.round(m[i] * 255)));
  return out;
}
