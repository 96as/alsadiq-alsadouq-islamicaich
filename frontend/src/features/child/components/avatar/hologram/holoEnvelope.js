// How the hologram looks in each phase of the timeline (context/holoTimeline.js): size, opacity,
// colour and the beam, as plain numbers. Pure and allocation-free, so it is unit tested and the
// component only has to copy the numbers into uniforms.

import { DIRECTOR } from '../avatarConfig.js';
import { HP } from '../context/holoTimeline.js';
import { HOLO } from './hologramConfig.js';

const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const smooth = (x) => {
  const c = clamp01(x);
  return c * c * (3 - 2 * c);
};
const easeOutCubic = (x) => 1 - (1 - clamp01(x)) ** 3;
const easeInCubic = (x) => clamp01(x) ** 3;
const easeOutBack = (x, c1) => {
  const u = clamp01(x) - 1;
  return 1 + (c1 + 1) * u * u * u + c1 * u * u;
};

export function makeEnvelope() {
  return {
    visible: false, // anything of the panel, beam or halo to draw
    panel: false,
    sx: 1, // panel scale
    sy: 1,
    alpha: 0, // overall opacity
    pyr: 0, // beam 0..1 (grown from the palm)
    wipe: 1, // the content scan line, 0..1 (1: all visible)
    gold: 0, // 0..1 toward the found colours
    dim: 0, // 0..1 not found (dimmed, desaturated)
    luma: 0, // extra brightness for the one flash (at most HOLO.found.flashLuma)
    twist: 0, // radians about the panel normal
    toPalm: 0, // 0..1 how far the panel has travelled into the palm
    halo: 0, // halo brightness multiplier
    haloGold: 0,
    burstT: -1, // seconds into the sparkle burst, -1 none
    orbit: 0, // 0..1 the orbiting sparkles
    stamp: -1, // seconds since the found stamp began, -1 none
  };
}

const O = HOLO.open;

/** The classic materialise at time `ot` (0 to 0.35 s); `dip` adds the 2-frame 15 percent dip. */
function openShape(ot, dip, e) {
  e.pyr = smooth(ot / O.pyramid);
  e.sx = O.widthStart + (1 - O.widthStart) * easeOutBack(ot / O.widthEnd, O.overshoot);
  e.sy = 0.02 + 0.98 * easeOutCubic((ot - O.heightDelay) / (O.heightEnd - O.heightDelay));
  e.wipe = clamp01(ot / O.wipe);
  e.alpha = clamp01(ot / 0.1);
  if (dip && ot >= O.dipAt && ot < O.dipAt + O.dipFor) e.alpha *= 1 - O.dip;
  e.orbit = smooth((ot - 0.15) / 0.2);
}

/**
 * w3: reduced motion with a web page. A 0.15 s fade in, still while it shows (gold and in place once Found), a 0.15 s
 * fade out. No scale, no scan line, no beam, no sparkles, no halo pulse.
 */
function reducedEnvelope(h, e, D) {
  const p = h.phase;
  e.pyr = 0;
  e.orbit = 0;
  e.halo = 0;
  if (p === HP.OPENING) {
    e.alpha = clamp01(h.t / D.reducedOpen);
  } else if (p === HP.INT_CLOSE) {
    e.alpha = 1 - smooth(h.t / D.interruptClose);
  } else if (p === HP.NONE_DIM) {
    e.dim = smooth(h.t / D.noneDim);
  } else if (p === HP.NONE_CLOSE) {
    e.dim = 1;
    e.alpha = 1 - smooth(h.t / (D.noneSquash + D.noneGone));
  } else if (p >= HP.GLOW && p <= HP.BURST) {
    const ft = h.foundT < 0 ? 0 : h.foundT;
    e.gold = 1;
    e.haloGold = 1;
    e.stamp = ft >= D.glowAt ? ft - D.glowAt : -1;
    e.alpha = 1 - smooth((ft - D.reducedHold) / D.reducedFade);
  }
  return e;
}

/**
 * @param {object} h the timeline output (makeHoloOutput)
 * @param {object} e the envelope to fill (makeEnvelope), reused
 * @returns {object} e
 */
export function holoEnvelope(h, e) {
  const D = DIRECTOR.holo;
  const p = h.phase;
  e.visible = false;
  e.panel = false;
  e.sx = 1;
  e.sy = 1;
  e.alpha = 1;
  e.pyr = 1;
  e.wipe = 1;
  e.gold = 0;
  e.dim = 0;
  e.luma = 0;
  e.twist = 0;
  e.toPalm = 0;
  e.haloGold = 0;
  e.burstT = -1;
  e.orbit = 1;
  e.stamp = -1;
  e.halo = 0;

  if (p === HP.CLOSED || p === HP.START || p === HP.ICON || p === HP.ICON_CHECK) return e;

  e.visible = true;
  e.panel = true;
  if (h.reduced) return reducedEnvelope(h, e, D); // w3: a page in reduced motion has no motion but the fade
  if (p === HP.OPENING) {
    openShape(h.t, true, e);
  } else if (p === HP.INT_CLOSE) {
    const k = clamp01(h.t / D.interruptClose);
    openShape((1 - k) * (D.open), false, e);
    e.alpha *= 1 - smooth(k);
    e.pyr *= 1 - k;
    e.orbit *= 1 - k;
  } else if (p === HP.NONE_DIM) {
    e.dim = smooth(h.t / D.noneDim);
  } else if (p === HP.NONE_CLOSE) {
    const squash = clamp01(h.t / D.noneSquash);
    const gone = clamp01((h.t - D.noneSquash) / D.noneGone);
    e.dim = 1;
    e.sy = 1 - 0.98 * smooth(squash);
    e.sx = 1 - easeInCubic(gone);
    e.alpha = 1 - smooth(gone);
    e.pyr = 1 - squash;
    e.orbit = 1 - squash;
  } else if (p >= HP.GLOW && p <= HP.BURST) {
    const ft = h.foundT < 0 ? 0 : h.foundT;
    const g = (ft - D.glowAt) / D.glow;
    e.gold = smooth(g);
    // One bright flash, a smooth bump of 0.25 s: at most one per Found, 0.3 in luminance.
    if (g > 0 && g < 1) {
      const s = Math.sin(Math.PI * g);
      e.luma = HOLO.found.flashLuma * s * s;
    }
    e.stamp = ft >= D.glowAt ? ft - D.glowAt : -1;
    const c = clamp01((ft - D.collapseAt - (h.shift || 0)) / (D.sparkleAt - D.collapseAt)); // w3: the hero hold shifts it
    if (p === HP.BURST) {
      e.panel = false;
      e.pyr = 0;
      e.orbit = 0;
      e.gold = 1;
      e.burstT = h.t;
      e.alpha = 0;
    } else if (c > 0) {
      const shrink = 1 - easeInCubic(c);
      e.sx = shrink;
      e.sy = shrink;
      e.twist = HOLO.found.twist * smooth(c);
      e.pyr = 1 - c;
      e.orbit = 1 - c;
      e.toPalm = easeInCubic(c);
      e.alpha = 1 - 0.25 * c;
    }
  }

  // The halo: pulses while holding, goes gold and flashes at Found.
  const flash = e.luma > 0 ? 1 + (HOLO.halo.flash - 1) * (e.luma / HOLO.found.flashLuma) : 1;
  e.haloGold = e.gold;
  e.halo = (HOLO.halo.base + HOLO.halo.pulse * Math.sin(h.total * 2.1)) * e.alpha * flash * (1 - 0.5 * e.dim);
  // The panel is gone during the burst, so its halo goes with it (a ring with nothing inside looks broken).
  if (p === HP.BURST) e.halo = 0;
  return e;
}
