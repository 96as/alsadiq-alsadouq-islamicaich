// Look-dev numbers for Sadiq on the painted meadow: lights, grade, materials, grounding, camera.
// Plain data, no three.js, no React. Section numbers (S3.2, S5, ...) point at studio-research/LOOKDEV-SPEC.md.
// Colours are sRGB hex strings; three's Color('#hex') converts them to linear.
//
// Nothing here may contain scripture or any other Islamic text.

export const LOOKDEV = {
  // ---- S3.2 image-based light from the meadow panorama --------------------------------------------
  env: {
    url: '/backgrounds/meadow-env-1024.webp', // the pano rolled 0.75, so no rotation is needed (verified, S3.1)
    intensity: 0.95, // review retune: the sky fill keeps the key:fill ratio (L5) in band with the lighter grade below
  },

  // ---- S3.2 lights (directions point from the avatar toward the light) -------------------------------
  key: { color: '#ffecd0', intensity: 3.2, dir: [-0.7788, 0.5, 0.3788] }, // the painting's sun, no shadow
  rim: { color: '#ffc4d2', intensity: 3.2, pos: [1.1, 1.5, -1.9], targetY: 0.5 }, // pink cloud glow behind-right
  hemi: { sky: '#b8c3ee', ground: '#9a8456', intensity: 0.18 }, // cool shadow fill, warm path bounce (review: 0.28 greyed the fur)
  lightDistance: 4, // positions are the directions times this, offset by the avatar x
  keyTargetY: 0.4,
  // S3.2: the shadow-only sun. Same azimuth as the key, 58 deg up, so the cast shadow stays 0.6 x his height.
  shadowSun: {
    color: '#ffffff',
    intensity: 0, // casts shadows, adds no light
    dir: [-0.477, 0.848, 0.232],
    mapSize: 1024,
    bounds: 1.5,
    near: 0.5,
    far: 9,
    bias: -0.0004,
    normalBias: 0.02,
  },

  // ---- S3.4 grounding ---------------------------------------------------------------------------------
  catcher: {
    size: 6,
    color: '#2a3550',
    opacity: 0.55,
    fade: [0.25, 0.9], // smoothstep radius (u) from the feet: no hard band across the painted grass
  },
  ao: {
    size: [0.56, 0.32], // u, across and deep
    y: 0.002,
    color: '#1e2638',
    opacity: 0.92,
    texSize: 128,
    stops: [
      [0, 1.0],
      [0.35, 0.85],
      [0.6, 0.3],
      [1.0, 0],
    ],
    hopFade: 0.12, // opacity * (1 - smoothstep(0, hopFade, hopY))
    hopGrow: 0.6, // scale * (1 + hopGrow * hopY)
  },
  foot: {
    size: [0.16, 0.1],
    opacity: 0.5,
    fadeHeight: 0.06, // opacity * (1 - smoothstep(0, fadeHeight, footY))
  },

  // ---- S4 / S5 tone mapping and grade (inside CustomToneMapping, no extra pass) ------------------------
  exposure: 1.0,
  // Review retune (back toward the spec's S5 values): split 0.5 and lift 0.5 turned the red-brown fur grey-mauve
  // (face fur saturation 0.50 against 0.78 in the original app, darkest pixels hue 316 at saturation 0.11). A
  // multiplicative blue tint cannot make a red-brown slate; it makes it mauve. These values give saturation about 0.65
  // with warm, deep shadows, like the original app, and keep L5 at 1.59.
  grade: {
    saturation: 1.15,
    shadowTint: '#6f86c0',
    highlightTint: '#fff1dc',
    split: 0.2,
    lift: '#2b3346',
    liftAmount: 0.1,
    haze: 0.02,
    hazeColor: '#d3c6dc',
  },

  // ---- S7 material upgrade (runtime only) --------------------------------------------------------------
  material: {
    normalScale: 0.9,
    sheenColor: '#8a6446',
    sheenRoughness: 0.42,
    maxAnisotropy: 8,
    envMapIntensity: 1.0,
    eye: {
      maskFrom: 0.12, // eyeMask = 1 - smoothstep(maskFrom, maskTo, roughnessFactor); the ORM is 0.078 only in the eyes
      maskTo: 0.22,
      roughness: 0.03,
      specularColor: 0.06,
      specularF90: 1.0,
    },
    wrap: {
      low: '#8fa45a', // the painting's grass on his lower silhouette
      high: '#e2cbe0', // the painting's sky on the upper one
      strength: 0.28,
      worldYRange: [0.05, 0.8],
      power: 3,
    },
  },

  // ---- S8 anti-aliasing and DPR -------------------------------------------------------------------------
  dpr: {
    high: { range: [1, 2], adaptiveMin: 1.5 },
    low: { range: [1, 1.5], adaptiveMin: 1.25 },
    slowFrameMs: 20, // mean frame time over this for slowSeconds drops the cap one step
    slowSeconds: 2,
  },

  // ---- S6 camera and framing ----------------------------------------------------------------------------
  framing: {
    fov: 30,
    charHeight: 0.85, // 0.977 x 0.87 u, ears to claws
    aspectRange: [0.6, 2.4], // t is smoothstep over log(aspect) between these
    heightFraction: [0.5, 0.68], // Hf at t = 0 and t = 1
    eyeFraction: [0.8, 0.62], // k at t = 0 and t = 1: where the horizon cuts him
    pathScreenX: [0.4, 0.6], // his screen x never leaves this band of the width
    // S6.4 safe areas in CSS px, measured on VoiceMode (header pt-8 + h-11; mic row h-16 + pb-4).
    safe: { top: 76, bottom: 80 },
    earsBelowHeader: 12,
    feetAboveControls: 16,
  },
};

/** S3.3: the time-of-day hook. Ship 'meadow' only; the painting is a single golden-hour moment. */
export const TIME_OF_DAY = 'meadow';
