// The lead's painted meadow and where Sadiq stands in it. Plain data and one pure function (no React,
// no three.js), so the image layer (MeadowImage.jsx) and the avatar camera (avatar/Avatar.jsx) use the
// same numbers and always agree on where the path and the avatar's feet are, on any window shape.
//
// To swap the meadow picture (for example for the living meadow), change MEADOW_IMAGE below.
// Nothing here may contain scripture or any other Islamic text.

const BASE = (import.meta.env && import.meta.env.BASE_URL) || '/';

/**
 * The painted meadow, as widths of the same 16:9 picture. The files are the lead's 2560x1440 painting
 * cleaned and upscaled (Real-ESRGAN anime model, BSD-3) with a mild unsharp mask, so a wide or
 * high-density screen still gets enough pixels. The browser picks one from `sizes` and the pixel ratio.
 */
export const MEADOW_IMAGE = {
  dir: `${BASE}backgrounds/hq/`,
  file: (w) => `meadow-${w}.webp`,
  widths: [900, 1600, 2560, 3840, 5120],
  aspect: 16 / 9,
  fallbackWidth: 2560,
  // The image is drawn with object-fit: cover, so its displayed width is max(100vw, 100vh * 16/9).
  sizes: 'max(100vw, 177.78vh)',
};

export const MEADOW_SRC = MEADOW_IMAGE.dir + MEADOW_IMAGE.file(MEADOW_IMAGE.fallbackWidth);
export const MEADOW_SRCSET = MEADOW_IMAGE.widths
  .map((w) => `${MEADOW_IMAGE.dir}${MEADOW_IMAGE.file(w)} ${w}w`)
  .join(', ');

/**
 * cards-spec (05) The narrow tier (perf): a portrait viewport (3:4 or narrower) sees only a thin vertical slice of the painting, so it
 * gets meadow-narrow-<w>.webp, the same picture at the same sizes with everything outside `band` (painting u) washed
 * out, about 45% fewer bytes (scripts/make-narrow-meadow.mjs). The layout and the GL maths do not change.
 * `band` must cover the visible slice of a 3:4 viewport under both fits (tests/meadowNarrow.test.mjs checks it).
 */
export const MEADOW_NARROW = {
  media: '(max-aspect-ratio: 3/4)',
  band: [0.19, 0.75],
  file: (w) => `meadow-narrow-${w}.webp`,
};
export const MEADOW_NARROW_SRCSET = meadowNarrowSrcset();

/**
 * cards-spec (05) perf review: the narrow srcset up to `cap` px wide. MeadowLife's GL layer covers the <img> and never
 * loads a file wider than its quality cap (meadowCap), so the narrow <img> stops at the same cap: a phone then takes one
 * meadow file instead of two (the GL layer's Image() reuses the <img>'s download).
 */
export function meadowNarrowSrcset(cap = Infinity) {
  return MEADOW_IMAGE.widths
    .filter((w) => w <= cap)
    .map((w) => `${MEADOW_IMAGE.dir}${MEADOW_NARROW.file(w)} ${w}w`)
    .join(', ');
}

/** cards-spec (05) perf review: the widest meadow file MeadowLife's GL layer loads at a quality tier ('low' on every phone). */
export function meadowCap(quality) {
  return quality === 'low' ? 2560 : 3840;
}

/** True when this viewport takes the narrow tier (the same test the <picture> source makes). */
export function isNarrowMeadow() {
  try {
    return typeof window !== 'undefined' && typeof window.matchMedia === 'function' && window.matchMedia(MEADOW_NARROW.media).matches;
  } catch {
    return false;
  }
}

/** The file name of the meadow at `width` for the narrow or the full tier. */
export function meadowFile(width, narrow) {
  return narrow ? MEADOW_NARROW.file(width) : MEADOW_IMAGE.file(width);
}

// Where things are in the painting, as fractions of its width and height.
/** The path's centre column on the rows near the bottom (where Sadiq stands). */
export const PATH_X = 0.455;
/** The painting row where Sadiq's feet should land. */
export const FEET_ROW = 0.82;

// Framing targets.
export const FOV_DEG = 32;
/** Sadiq's height on screen, as a share of the stage height (the stage never gets smaller than this). */
export const AVATAR_SHARE = 0.57;
/** Height of the avatar in world units as the camera sees it (ears to claws, with the idle pose). */
export const AVATAR_HEIGHT = 0.865;
/** Room kept free at the bottom for the mic row, and at the top for the header, in CSS pixels. */
export const BOTTOM_RESERVE = [88, 124];
export const TOP_RESERVE = [64, 104];

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

/**
 * Everything that depends on the stage size w x h (CSS pixels).
 * - avatarPx: Sadiq's height on screen; feetY: where his feet are, from the top of the stage.
 * - distance, targetY: camera distance and the height the camera looks at (no tilt).
 * - pathX: the screen column of the path centre; avatarX: the world x that puts Sadiq there.
 * - objectX / objectY: object-position (0..1) for the cover image so the path and the feet row line up.
 */
export function computeFraming(w, h) {
  const bottom = clamp(h * 0.14, BOTTOM_RESERVE[0], BOTTOM_RESERVE[1]);
  const top = clamp(h * 0.12, TOP_RESERVE[0], TOP_RESERVE[1]);
  const feetY = h - bottom;
  const avatarPx = Math.max(60, Math.min(h * AVATAR_SHARE, feetY - top));

  const worldH = AVATAR_HEIGHT * (h / avatarPx); // world units that fit the stage height
  const distance = worldH / (2 * Math.tan((FOV_DEG * Math.PI) / 360));
  const targetY = ((feetY - h / 2) / h) * worldH;

  const s = Math.max(w / MEADOW_IMAGE.aspect, h); // image height in px under object-fit: cover
  const imgW = s * MEADOW_IMAGE.aspect;
  const imgH = s;
  const objectX = imgW > w ? clamp((PATH_X * imgW - w / 2) / (imgW - w), 0, 1) : 0.5;
  const objectY = imgH > h ? clamp((FEET_ROW * imgH - feetY) / (imgH - h), 0, 1) : 0.5;
  const pathX = PATH_X * imgW - objectX * (imgW - w);
  const avatarX = ((pathX - w / 2) / h) * worldH;

  return { feetY, avatarPx, worldH, distance, targetY, objectX, objectY, pathX, avatarX, top, bottom }; // hotfix-2: top, bottom for the conversation shot
}
