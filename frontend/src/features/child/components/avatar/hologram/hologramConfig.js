// The search hologram: every number and colour in one place (SPEC-EXPERIENCE section 7).
// Plain data, no three.js. Lengths are avatar-local metres (before MODEL_SCALE), angles radians.
//
// Nothing here may contain scripture or any other Islamic text; the hologram shows abstract shapes only.

const deg = (d) => (d * Math.PI) / 180;

export const HOLO = {
  // Colour tokens (sRGB hex).
  color: {
    core: '#7DF5E6',
    highlight: '#E9FFFB',
    plate: '#0B2E35',
    found: '#FFD36E',
    foundHighlight: '#FFF4CF',
    folders: ['#8EF0D2', '#FFE08A', '#FFB4A2'],
    folderToCore: 0.6, // the folder tints are mixed this far toward the core colour (section 7.3)
  },
  plateAlpha: 0.5,

  // The panel.
  size: [0.26, 0.195], // 4:3
  radius: 0.022,
  rim: 0.004,

  // Attach point.
  anchorHalfLife: 0.06, // the spring that follows the hand
  panelOffset: [0.035, 0.125, 0.04], // from the anchor: up, a little toward the camera and out past the sleeve (tuned on prop_L, Phase B)
  towardHead: 0.3, // facing = lerp(dirToCamera, dirToHead, this)
  tiltBack: deg(8),
  facingRate: 10, // slerp rate per second
  swayYaw: deg(4), // +-, the hand float (also the parallax)
  swayHz: 0.45,
  // No SearchHold clip (today's GLB): a virtual palm point, no pyramid.
  virtualAnchor: [0.33, 0.5, 0.16],
  // A hand bone without the prop_L socket: hand plus this offset (tuned in the dev preview).
  fallbackOffset: [0.0, 0.06, 0.04],
  socketBone: 'prop_L',
  handBone: 'handl',
  headBone: 'head',

  // Layers (avatar-local z, relative to the panel plane).
  z: { plate: -0.006, content: 0, lens: 0.012, sparkle: 0.02 },
  pyramid: { width: 0.8, depth: 0.02, alphaPalm: 0.3, alphaPanel: 0.05, flicker: 0.04 },
  halo: { scale: 1.8, base: 0.35, pulse: 0.1, flash: 1.6 },
  sparkles: { orbit: 18, burst: 14, burstLife: 0.6, gravity: 0.35, burstSpeed: 0.14 },

  // Frame safety (section 7.4).
  safety: { headRadius: 0.12, maxShift: 0.06, ndcLimit: 0.96, minScale: 0.8 },

  // Reduced motion icon (avatar-local, beside the left shoulder).
  icon: { pos: [0.24, 0.86, 0.1], size: 0.085, canvas: 128 },

  // Open animation (0.35 s, "the classic materialise").
  open: {
    pyramid: 0.12,
    widthStart: 0.2,
    widthEnd: 0.2, // the width reaches 1 (after the 1.04 overshoot) by this time
    heightDelay: 0.05,
    heightEnd: 0.3,
    wipe: 0.25, // the scan line wipes the content in over this time
    dipAt: 0.2,
    dipFor: 2 / 30,
    dip: 0.15,
    overshoot: 0.62, // easeOutBack constant: about +4 percent
  },
  // Found: gold, collapse into the palm, sparkle burst.
  found: { goldIn: 0.25, flashLuma: 0.3, twist: deg(25) },
  none: { dim: 0.5, desaturate: 0.5 },

  // Content (skins).
  scroll: 0.9, // cards per second
  shimmerEvery: 1.2,
  scanline: 0.02,
  progressFill: 6, // seconds for the progress bar to fill (it only hints at the wait)

  // Phones: two draw calls (pyramid and panel), no halo or sparkles.
  lowTier: { hardwareConcurrency: 4, deviceMemory: 4, shortSide: 500 },

  // Optional status line (UI copy, not content).
  status: {
    library: { ar: 'الصديق يبحث في مكتبته…', en: 'Al-Sadiq is looking in his library…' },
    folders: { ar: 'يتفقد ملف مهماتك…', en: 'Checking your quest folder…' },
    web: { ar: 'الصديق يبحث…', en: 'Al-Sadiq is searching…' },
    found: { ar: 'وجدها!', en: 'Found it!' },
  },
};

export const SKIN_INDEX = { library: 0, folders: 1, web: 2 };

/** True when this device should get the 2-draw-call hologram. */
export function isLowTier(env = globalThis) {
  const L = HOLO.lowTier;
  try {
    const nav = env.navigator;
    const cores = nav?.hardwareConcurrency;
    const mem = nav?.deviceMemory;
    const scr = env.screen;
    const short = scr ? Math.min(scr.width, scr.height) : 9999;
    return (
      (typeof cores === 'number' && cores <= L.hardwareConcurrency) ||
      (typeof mem === 'number' && mem <= L.deviceMemory) ||
      short < L.shortSide
    );
  } catch {
    return false;
  }
}
