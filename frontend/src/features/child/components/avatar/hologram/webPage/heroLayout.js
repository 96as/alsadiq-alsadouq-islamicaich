// w3: where the page goes for the hero hold (BEHAVIOUR-SPEC 6.6): after Found, the window leaves his hand and is
// held out to the child, big enough to read. Pure and unit tested: the rect never meets his head and never covers
// his mouth. All numbers are css px on the stage (y grows downward); the window is 360 x 480, so w / h = 0.75.

import { WIN } from './pageLayout.js';

export const HERO = {
  portraitW: 0.6, // of the canvas width (55 to 70 percent)
  landscapeW: 0.6, // of the canvas width ...
  landscapeMax: 520, // ... but at most this many css px
  landscapeH: 0.7, // and at most this share of the canvas height
  mouthGap: 0.04, // portrait: the top edge is at least this share of the stage height below the mouth
  margin: 0.02, // clear space kept at the canvas edge
  sideGap: 0.04, // landscape: clear space (share of the canvas width) between the head circle and the window
  headGrow: 1.12, // landscape: the head circle is widened by this before the gap
};

const ASPECT = WIN.w / WIN.h;
const clamp = (x, lo, hi) => (x < lo ? lo : x > hi ? hi : x);

/** True when the rect (x, y, w, h) and the circle (cx, cy, r) overlap. */
export function rectHitsCircle(x, y, w, h, cx, cy, r) {
  const nx = clamp(cx, x, x + w);
  const ny = clamp(cy, y, y + h);
  return Math.hypot(nx - cx, ny - cy) < r;
}

/**
 * The hero rect on a stage.
 * @param {number} W stage width (css px)
 * @param {number} H stage height (css px)
 * @param {{x: number, y: number, r: number, mouthY: number}} head head circle centre, radius and the mouth's y (stage px)
 * @param {number} side +1 when the hand is on the viewer's right, -1 on the left
 * @param {{x: number, y: number, w: number, h: number, side: number}} [out]
 */
export function heroRect(W, H, head, side = 1, out = { x: 0, y: 0, w: 0, h: 0, side: 1 }) {
  const m = HERO.margin;
  if (H >= W) {
    // portrait: below his face, centred on the body
    let top = Math.max(head.mouthY + HERO.mouthGap * H, head.y + head.r + 0.01 * H);
    let w = HERO.portraitW * W;
    const room = H * (1 - m) - top;
    if (w / ASPECT > room) w = Math.max(0.4 * W, room * ASPECT);
    const h = w / ASPECT;
    if (top + h > H * (1 - m)) top = Math.max(head.mouthY + HERO.mouthGap * H, H * (1 - m) - h); // never up into the face
    out.w = w;
    out.h = h;
    out.x = clamp(head.x - w / 2, W * m, W * (1 - m) - w);
    out.y = top;
    out.side = side;
    return out;
  }
  // landscape: beside him on the hand side, top at eye level
  let w = Math.min(HERO.landscapeW * W, HERO.landscapeMax, HERO.landscapeH * H * ASPECT);
  const gap = HERO.sideGap * W;
  let s = side >= 0 ? 1 : -1;
  const hr = head.r * HERO.headGrow; // the face (ears, a turned head) is wider than the tracked circle
  const room = (dir) => (dir > 0 ? W * (1 - m) - (head.x + hr + gap) : head.x - hr - gap - W * m);
  if (room(s) < w && room(-s) > room(s)) s = -s;
  if (room(s) < w) w = Math.max(0.2 * W, room(s));
  const h = w / ASPECT;
  const x = s > 0 ? head.x + hr + gap : head.x - hr - gap - w;
  const eye = head.y - 0.25 * head.r;
  const y = clamp(eye, H * m, Math.max(H * m, H * (1 - m) - h));
  out.x = x;
  out.y = y;
  out.w = w;
  out.h = h;
  out.side = s;
  return out;
}

/** Min-jerk easing: 0 to 1 with zero velocity and acceleration at both ends. */
export function minJerk(x) {
  const t = clamp(x, 0, 1);
  return t * t * t * (t * (t * 6 - 15) + 10);
}
