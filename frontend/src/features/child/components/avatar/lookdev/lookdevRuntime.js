// Small runtime helpers shared by AvatarLookdev.jsx and Avatar.jsx (kept out of the component file so fast refresh works).
import { solveFraming } from './stageFraming.js';

/** Where Sadiq stands (world x). Today's value outside the painted meadow, the framing's inside it. */
export function lookdevAvatarX(framing, size) {
  if (framing === 'meadow') return solveFraming(size.width, size.height).avatarX;
  return size.width / size.height < 0.8 ? -0.02 : -0.13;
}

// Timing for the gates (L11): the cost of the rig's frame work, readable as window.__lookdev. Nothing is allocated per frame.
export const lookdevStats = { frames: 0, totalMs: 0, maxMs: 0, scans: 0, dpr: 0 };
if (typeof window !== 'undefined') window.__lookdev = lookdevStats;
