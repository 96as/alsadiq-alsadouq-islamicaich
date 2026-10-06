// w3: where Sadiq looks while the page is in his hand (BEHAVIOUR-SPEC 6.5). Pure and allocation-free.
//
// The rig has no eye bones, so the HEAD reads: the look-at target travels along a line of text in the reading
// direction (left to right in English, right to left in Arabic) over 0.6 s, comes back in 0.15 s and steps down
// 22 px for the next sweep. The line sits on the page, so it scrolls with the page; after a flick it jumps to
// the top of the new view in 0.12 s and blinks once. Every 4 to 6 s he glances at the child for 0.6 s.
//
// The output is a point in window logical px (x from the left edge, y from the top of the window, 360 x 480) and
// a `glance` amount (0 on the page, 1 on the child) the rig uses to lerp the target toward the camera.

import { WIN } from './pageLayout.js';

export const GAZE = {
  sweep: 0.6, // s along a line
  back: 0.15, // s to return
  stepDown: 22, // px per sweep
  lineLen: 230, // px, how far along a line the head travels
  margin: 40, // px from the side where a line starts
  jump: 0.12, // s, the jump to the top after a flick
  glanceEvery: [4, 6],
  glanceFor: 0.6,
  topY: WIN.chrome + 34, // window y of the first line of a view
  maxY: WIN.h - 60, // lines never go below this (window y)
};

const smooth = (x) => {
  const c = x < 0 ? 0 : x > 1 ? 1 : x;
  return c * c * (3 - 2 * c);
};

export function createReadingGaze(rng = Math.random, cfg = GAZE) {
  const g = {
    x: WIN.w / 2,
    y: cfg.topY,
    glance: 0,
    blink: false,
    rtl: false,
    // internal
    sweepT: 0,
    lineWin: cfg.topY, // the line's window y (moves with the page)
    jumpFrom: 0,
    jumpT: 1,
    nextGlance: 4,
    glanceT: -1,
    clock: 0,
    lastScroll: 0,
  };

  const between = (r) => r[0] + rng() * (r[1] - r[0]);

  g.reset = (rtl) => {
    g.rtl = !!rtl;
    g.sweepT = 0;
    g.lineWin = cfg.topY;
    g.jumpT = 1;
    g.glance = 0;
    g.glanceT = -1;
    g.clock = 0;
    g.nextGlance = between(cfg.glanceEvery);
    g.blink = false;
    g.lastScroll = 0;
  };

  /** A flick began: after it, the head jumps to the top of the new view. */
  g.onFlick = () => {
    g.jumpFrom = g.lineWin;
    g.lineWin = cfg.topY;
    g.jumpT = 0;
    g.blink = true;
  };

  /**
   * @param {number} dt
   * @param {number} scroll the page's current scroll (px)
   * @param {boolean} reading false when the head should rest (found, reduced motion)
   */
  g.step = (dt, scroll, reading) => {
    g.blink = false; // a blink is a one-frame request: onFlick sets it after this step, the next step clears it
    g.clock += dt;
    // the line rides the page: when the page moves up by d px, the line moves up by d px too
    const d = scroll - g.lastScroll;
    g.lastScroll = scroll;
    if (g.jumpT >= 1) g.lineWin -= d;
    if (!reading) {
      g.glance += (0 - g.glance) * Math.min(1, dt * 6);
      return g;
    }
    // the sweep
    g.sweepT += dt;
    const cycle = cfg.sweep + cfg.back;
    if (g.sweepT >= cycle) {
      g.sweepT -= cycle;
      if (g.jumpT >= 1) g.lineWin += cfg.stepDown;
      if (g.lineWin > cfg.maxY) g.lineWin = cfg.topY; // wrapped: start the next pass at the top
      if (g.lineWin < cfg.topY - 10) g.lineWin = cfg.topY;
    }
    const along = g.sweepT < cfg.sweep ? smooth(g.sweepT / cfg.sweep) : 1 - smooth((g.sweepT - cfg.sweep) / cfg.back);
    const startX = g.rtl ? WIN.w - cfg.margin : cfg.margin;
    const dir = g.rtl ? -1 : 1;
    g.x = startX + dir * along * cfg.lineLen;
    let y = g.lineWin;
    if (g.jumpT < 1) {
      g.jumpT += dt / cfg.jump;
      const k = smooth(g.jumpT);
      y = g.jumpFrom + (g.lineWin - g.jumpFrom) * k;
    }
    g.y = y;
    // the glance at the child
    if (g.glanceT < 0 && g.clock >= g.nextGlance) {
      g.glanceT = 0;
    }
    if (g.glanceT >= 0) {
      g.glanceT += dt;
      const u = g.glanceT / cfg.glanceFor;
      g.glance = u < 0.25 ? smooth(u / 0.25) : u < 0.75 ? 1 : 1 - smooth((u - 0.75) / 0.25);
      if (g.glanceT >= cfg.glanceFor) {
        g.glanceT = -1;
        g.glance = 0;
        g.nextGlance = g.clock + between(cfg.glanceEvery);
      }
    }
    return g;
  };

  g.reset(false);
  return g;
}
